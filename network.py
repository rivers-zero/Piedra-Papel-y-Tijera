# network.py
import socket
import json

def setup_server_socket(host, port):
    """
    Set up a TCP server socket that listens on the given host and port.
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen(1)
    return server_sock

def accept_connection(server_sock):
    """
    Accept an incoming connection.
    Returns a tuple (client_socket, address).
    """
    client_sock, addr = server_sock.accept()
    return client_sock, addr

def connect_to_server(host, port):
    """
    Connect to a server using its host and port.
    Returns the connected socket.
    """
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect((host, port))
    return client_sock

def send_data(sock, data):
    """
    Send a dictionary as a JSON-formatted message over the socket.
    """
    message = json.dumps(data)
    sock.sendall(message.encode())

def receive_data(sock):
    """
    Receive a JSON-formatted message from the socket.
    Returns the corresponding dictionary, or None if nothing is received.
    """
    try:
        data = sock.recv(4096)
        if not data:
            return None
        return json.loads(data.decode())
    except Exception as e:
        print("Error receiving data:", e)
        return None
