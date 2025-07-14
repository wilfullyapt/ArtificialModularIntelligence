import socket

from ami.core.config import Config

def get_network_url(remote_host="www.x.com" ):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        remote_ip = socket.gethostbyname(remote_host)
        s.connect((remote_ip, 80))
        ip_address = s.getsockname()[0]
        s.close()
        port = Config().server_port
        return f"{ip_address}:{port}"
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
