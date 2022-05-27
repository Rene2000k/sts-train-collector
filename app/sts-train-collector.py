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
api.register("STS train collector", "Rene Klemm", "0.0.1", "desc")
train_list = api.get_train_list()
for train in train_list:
    train_timetable = api.get_train_timetable(train.id)
    print(train_timetable)