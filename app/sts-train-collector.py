import time
from sts_api.models import EventType
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
# for train in train_list:
#     train_timetable = api.get_train_timetable(train.id)
#     print(train_timetable)
train_timetable = api.get_train_timetable(train_list[0].id)
print(train_timetable)
connectors = api.get_all_connection_elements()
for connector in connectors:
    print(connector)