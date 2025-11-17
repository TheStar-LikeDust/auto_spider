"""
Simple daemon client for one-time commands.

Simplified client that sends commands and returns responses.
"""

import json
import socket
from .config import DEFAULT_HOST, DEFAULT_PORT, ADD_PLAN, RELOAD, SHUTDOWN


def encode_command(cmd: str, data: dict = None) -> bytes:
    """
    Encode command and data to bytes.

    Args:
        cmd: Command type
        data: Command data

    Returns:
        JSON encoded bytes
    """
    message = {'cmd': cmd, 'data': data or {}}
    return json.dumps(message).encode('utf-8')


def decode_command(data: bytes) -> tuple:
    """
    Decode bytes to command and data.

    Args:
        data: JSON encoded bytes

    Returns:
        Tuple of (cmd, data)
    """
    message = json.loads(data.decode('utf-8'))
    return message['cmd'], message.get('data', {})


def encode_response(success: bool, message: str = '', data=None) -> bytes:
    """
    Encode response to bytes.

    Args:
        success: Whether command succeeded
        message: Response message
        data: Response data

    Returns:
        JSON encoded bytes
    """
    response = {'success': success, 'message': message, 'data': data}
    return json.dumps(response).encode('utf-8')


def decode_response(data: bytes) -> dict:
    """
    Decode bytes to response dict.

    Args:
        data: JSON encoded bytes

    Returns:
        Response dict with success, message, data
    """
    return json.loads(data.decode('utf-8'))


def send_command(cmd: str, data: dict = None, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """
    Send one-time command to daemon manager.

    Args:
        cmd: Command type
        data: Command data (optional)
        host: Manager host
        port: Manager port

    Returns:
        Response dictionary with 'success' and 'message' keys
    """
    try:
        # create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        sock.connect((host, port))

        # send command
        command_data = encode_command(cmd, data or {})
        sock.sendall(command_data)

        # receive response
        response_data = sock.recv(4096)
        response = decode_response(response_data)

        sock.close()
        return response

    except Exception as e:
        return {'success': False, 'message': str(e)}


def add_plan(plan_file: str, stage: str = 'action', steps: list = None, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """
    Add plan to daemon.

    Args:
        plan_file: Path to plan file
        stage: Stage type
        steps: Step names
        host: Manager host
        port: Manager port

    Returns:
        Response dictionary
    """
    data = {
        'plan_file': plan_file,
        'stage': stage,
        'steps': steps or []
    }
    return send_command(ADD_PLAN, data, host, port)


def reload(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """
    Reload daemon modules.

    Args:
        host: Manager host
        port: Manager port

    Returns:
        Response dictionary
    """
    return send_command(RELOAD, host=host, port=port)


def shutdown(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """
    Shutdown daemon manager.

    Args:
        host: Manager host
        port: Manager port

    Returns:
        Response dictionary
    """
    return send_command(SHUTDOWN, host=host, port=port)


