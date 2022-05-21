import logging
import socket

class STSApi:
    HOST = "localhost"
    PORT = 3691

    def __init__(self) -> None:
        self.log = logging.getLogger(__class__.__name__)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect(self):
        try:
            self.socket.connect((self.HOST, self.PORT))
            msg = self.socket.recv(4096)
            print(msg)
        except (ConnectionRefusedError, TimeoutError):
            self.log.error("Could not connect to STS plugin interface") 
            raise
        else:
            self.log.info("Connected to STS plugin interface")

