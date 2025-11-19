"""
Daemon manager for continuous task execution.

Socket-based manager similar to multiprocessing.Manager.
"""

import socket
import threading
import importlib.util
import sys
from pathlib import Path
from multiprocessing import JoinableQueue, Process
from threading import Thread, Event
from queue import Queue as ThreadQueue
from typing import Callable, Dict, List, Optional

from ..logger import build_logger
from ..core.worker import run_worker, SHUTDOWN_SIGNAL, RELOAD_SIGNAL
from ..core.registry import get_step, clear_all_steps, reload_tracked_modules
from ..core.stage import get_tasks_for_stage, setup_context_for_stage, save_stage_result
from ..step import Context, execute_steps
from ..storage import initial_storage
from .config import ADD_PLAN, RELOAD, SHUTDOWN, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_MAX_WORKERS
from .client import encode_command, decode_command, encode_response, decode_response

_LOGGER = build_logger('daemon.manager')


class DaemonManager:
    """
    Daemon manager for background task execution.
    
    Manages worker pool and accepts plan submissions via socket.
    """
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, max_workers: int = DEFAULT_MAX_WORKERS):
        """
        Initialize daemon manager.
        
        Args:
            host: Socket host
            port: Socket port
            max_workers: Number of workers
        """
        self.host = host
        self.port = port
        self.max_workers = max_workers
        
        self.server_socket = None
        self.running = False
        self.reload_event = Event()
        
        # worker pool (process or thread based on stage)
        self.workers = []
        self.task_queue = None
        self.worker_type = None
        
        # current plan info
        self.plan_module = None
        self.plan_name = None
        self.current_stage = None
        self.current_steps = []
        self.initial_spider = None
        self.initial_plan = None
        self.initial_task = None
        self.output_folder = None
        
        _LOGGER.info(f"DaemonManager initialized: {host}:{port}, {max_workers} workers")
    
    def start(self):
        """
        Start daemon manager.
        
        Creates socket server and starts listening for commands.
        """
        if self.running:
            _LOGGER.warning("Manager already running")
            return
        
        self.running = True
        
        # create socket server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        _LOGGER.info(f"Daemon manager started on {self.host}:{self.port}")
        
        # start accepting connections
        self._accept_loop()
    
    def _accept_loop(self):
        """Accept incoming connections and handle commands"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                _LOGGER.debug(f"Client connected: {addr}")
                
                # handle client in new thread
                handler = threading.Thread(target=self._handle_client, args=(client_socket,))
                handler.daemon = True
                handler.start()
                
            except Exception as e:
                if self.running:
                    _LOGGER.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket):
        """
        Handle client connection and commands.
        
        Args:
            client_socket: Client socket
        """
        try:
            # receive command
            data = client_socket.recv(4096)
            if not data:
                return
            
            cmd, cmd_data = decode_command(data)
            _LOGGER.info(f"Received command: {cmd}")
            
            # dispatch command
            if cmd == ADD_PLAN:
                response = self._handle_add_plan(cmd_data)
            elif cmd == RELOAD:
                response = self._handle_reload()
            elif cmd == SHUTDOWN:
                response = self._handle_shutdown()
            else:
                response = encode_response(False, f'Unknown command: {cmd}')
            
            # send response
            client_socket.sendall(response)
            
        except Exception as e:
            _LOGGER.error(f"Error handling client: {e}")
            response = encode_response(False, str(e))
            try:
                client_socket.sendall(response)
            except:
                pass
        finally:
            client_socket.close()
    
    def _handle_add_plan(self, data: Dict) -> bytes:
        """
        Handle add_plan command.
        
        Args:
            data: Command data with plan_file, stage, steps
            
        Returns:
            Response bytes
        """
        try:
            plan_file = data.get('plan_file')
            stage = data.get('stage', 'action')
            steps = data.get('steps', [])
            
            if not plan_file:
                return encode_response(False, 'plan_file is required')
            
            if not steps:
                return encode_response(False, 'steps is required')
            
            _LOGGER.info(f"Adding plan: {plan_file}, stage={stage}, steps={steps}")
            
            # load plan module
            plan_path = Path(plan_file)
            self.plan_name = plan_path.stem
            self._load_plan_module(plan_file)
            
            # start workers if not started
            if not self.workers:
                self.current_stage = stage
                self.current_steps = steps
                self._start_workers(stage, steps)
            
            # get tasks for stage
            tasks = self._get_tasks_for_stage(stage)
            
            # add tasks to queue
            for i, task in enumerate(tasks):
                self.task_queue.put((i, task))
            
            _LOGGER.info(f"Added {len(tasks)} tasks to queue")
            
            return encode_response(True, f'Added {len(tasks)} tasks')
            
        except Exception as e:
            _LOGGER.error(f"Failed to add plan: {e}")
            return encode_response(False, str(e))
    
    def _handle_reload(self) -> bytes:
        """
        Handle reload command.
        
        Returns:
            Response bytes
        """
        try:
            _LOGGER.info("Triggering module reload")
            
            # send reload signal via queue
            for _ in range(self.max_workers):
                self.task_queue.put(RELOAD_SIGNAL)
            
            return encode_response(True, 'Reload signal sent')
            
        except Exception as e:
            _LOGGER.error(f"Failed to reload: {e}")
            return encode_response(False, str(e))
    
    def _handle_shutdown(self) -> bytes:
        """
        Handle shutdown command.
        
        Returns:
            Response bytes
        """
        try:
            _LOGGER.info("Shutting down daemon manager")
            
            # send shutdown signal to workers
            if self.workers:
                for _ in range(self.max_workers):
                    self.task_queue.put(SHUTDOWN_SIGNAL)
                
                # wait for workers to exit
                for worker in self.workers:
                    worker.join(timeout=5)
            
            self.running = False
            
            # close server socket
            if self.server_socket:
                self.server_socket.close()
            
            return encode_response(True, 'Manager shutdown')
            
        except Exception as e:
            _LOGGER.error(f"Failed to shutdown: {e}")
            return encode_response(False, str(e))
    
    def _load_plan_module(self, plan_file: str):
        """
        Load plan module and extract initial functions.
        
        Args:
            plan_file: Path to plan file
        """
        plan_path = Path(plan_file).resolve()
        
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")
        
        # load module
        spec = importlib.util.spec_from_file_location("plan_module", plan_path)
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load plan file: {plan_file}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules["plan_module"] = module
        spec.loader.exec_module(module)
        
        # extract initial functions
        self.plan_module = module
        self.initial_spider = getattr(module, 'initial_spider', None)
        self.initial_task = getattr(module, 'initial_task', None)
        self.initial_plan = getattr(module, 'initial_plan', None)
        
        if not self.initial_task or not self.initial_plan:
            raise ValueError("Plan file must define: initial_task, initial_plan")
        
        _LOGGER.info(f"Plan module loaded: {plan_file}")
    
    def _start_workers(self, stage: str, steps: List[str]):
        """
        Start worker pool.
        
        Args:
            stage: Stage type ('action', 'parse', 'extract')
            steps: Step names to execute
        """
        if stage == 'action' and not self.initial_spider:
            raise ValueError("initial_spider is required for action stage")
        
        self.worker_type = 'process' if stage == 'action' else 'thread'
        
        # create task queue
        if self.worker_type == 'process':
            from multiprocessing import JoinableQueue
            self.task_queue = JoinableQueue()
        else:
            from queue import Queue
            self.task_queue = Queue()
        
        # create output folder
        if stage in ['action', 'parse']:
            self.output_folder = initial_storage(stage)
        
        # start workers without barriers (daemon mode doesn't need sync)
        worker_class = Process if self.worker_type == 'process' else Thread
        
        for worker_id in range(self.max_workers):
            worker = worker_class(
                target=self._worker_loop,
                args=(worker_id, stage, steps)
            )
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        _LOGGER.info(f"Started {self.max_workers} {self.worker_type} workers")
    
    def _worker_loop(self, worker_id: int, stage: str, steps: List[str]):
        """
        Worker loop for daemon mode.
        
        Args:
            worker_id: Worker ID
            stage: Stage type
            steps: Step names to execute
        """
        # initialize spider and resources
        spider = None
        if self.initial_spider:
            spider = self.initial_spider()
            spider.attach()
        
        initial = self.initial_plan()
        if not isinstance(initial, dict):
            initial = {'resources': initial}
        
        # get step functions
        step_funcs = [get_step(stage, name) for name in steps]
        
        _LOGGER.info(f"[Worker-{worker_id}] Started and ready")
        
        # process tasks continuously
        while True:
            try:
                item = self.task_queue.get()
                
                # check for shutdown signal
                if item == SHUTDOWN_SIGNAL:
                    self.task_queue.task_done()
                    _LOGGER.info(f"[Worker-{worker_id}] Received shutdown signal")
                    break
                
                # check for reload signal
                if item == RELOAD_SIGNAL:
                    self.task_queue.task_done()
                    _LOGGER.info(f"[Worker-{worker_id}] Reloading modules...")
                    try:
                        clear_all_steps()
                        reload_tracked_modules()
                        # re-get step functions after reload
                        step_funcs = [get_step(stage, name) for name in steps]
                        _LOGGER.info(f"[Worker-{worker_id}] Modules reloaded")
                    except Exception as e:
                        _LOGGER.error(f"[Worker-{worker_id}] Reload failed: {e}")
                    continue
                
                # process task
                task_index, task = item
                task_name = f'task{task_index + 1}'
                
                _LOGGER.info(f"[Worker-{worker_id}] Processing {task_name}")
                
                try:
                    # create context with original task
                    original_task = task.get('task', task) if isinstance(task, dict) else task
                    context = Context(spider=spider, task=original_task, initial=initial)
                    
                    # setup context for stage
                    setup_context_for_stage(stage, context, task)
                    
                    # execute steps
                    execute_steps(step_funcs, context)
                    
                    # save result (only for action and parse stages)
                    if self.output_folder:
                        save_stage_result(stage, context, self.output_folder, task_name)
                    
                    _LOGGER.info(f"[Worker-{worker_id}] Task {task_name} completed")
                    
                except Exception as e:
                    _LOGGER.error(f"[Worker-{worker_id}] Task {task_name} failed: {e}")
                
                self.task_queue.task_done()
                
            except Exception as e:
                _LOGGER.error(f"[Worker-{worker_id}] Error: {e}")
                try:
                    self.task_queue.task_done()
                except:
                    pass
        
        # cleanup
        if spider:
            spider.detach()
        
        _LOGGER.info(f"[Worker-{worker_id}] Exited")
    
    def _get_tasks_for_stage(self, stage: str) -> List:
        """
        Get tasks for stage.
        
        Args:
            stage: Stage type
            
        Returns:
            List of tasks
        """
        if stage == 'action':
            return self.initial_task()
        else:
            # TODO: Load from previous stage output
            return []
