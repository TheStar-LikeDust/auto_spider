"""
Worker support: collector thread and shutdown signal.

Historical note: This module previously contained _feeder_thread for rate-limited
task dispatch (assigned _index and slept between tasks). Replaced by worker-level
rate limiting via shared multiprocessing.Lock.
"""

from typing import List
from threading import Thread
from ..tools.logger import build_logger

_LOGGER = build_logger('worker_support')

SHUTDOWN_SIGNAL = '__SHUTDOWN__'


# ── collector ──

def _collector_thread(task_result_process_queue, process_result_callback, collected: list):
    """Thread target: drain result queue, save results. Exits on SHUTDOWN_SIGNAL."""
    while True:
        result = task_result_process_queue.get()
        if result == SHUTDOWN_SIGNAL:
            break
        process_result_callback(result)
        collected.append(result)


def launch_collector(task_result_process_queue, process_result_callback, collected: list):
    """Start collector thread."""
    thread = Thread(target=_collector_thread,
                    args=(task_result_process_queue, process_result_callback, collected))
    thread.start()
    return thread
