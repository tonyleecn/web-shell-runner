import socket
import threading

def check_port(host, port):
    """
    检查指定主机的端口是否开放
    
    Args:
        host: 主机名或IP地址
        port: 端口号
        
    Returns:
        bool: 端口是否开放
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except:
        return False

def check_ports_status(script):
    """
    检查脚本中所有端口的状态
    
    Args:
        script: Script对象
        
    Returns:
        dict: 端口状态字典，格式为 {port: is_open}
    """
    if not script.ports:
        return {}
    
    port_status = {}
    for port_line in script.ports.splitlines():
        port = port_line.strip()
        if port:
            # 默认检查本地主机
            port_status[port] = check_port('127.0.0.1', port)
    
    return port_status 