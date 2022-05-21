import time
from sts_api.STSApi import STSApi

api = STSApi()
connected = False
while not connected:
    try:
        api.connect()
        connected = True
    except (ConnectionRefusedError, TimeoutError):
        time.sleep(2)