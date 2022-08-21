import time
from sts_api.STSApi import STSApi
from TrainCollection import TrainCollection

SLEEP_INTERVAL = 600


def run():
    api = STSApi()
    connected = False
    while not connected:
        try:
            api.connect()
            connected = True
        except (ConnectionRefusedError, TimeoutError):
            time.sleep(2)
    api.register("STS train collector", "Rene Klemm", "0.0.1", "desc")
    
    signal_box_name = api.get_signal_box_info().name
    train_collection = TrainCollection(signal_box_name)
    
    try:
        while True:
            print("Running train collection")
            train_list = api.get_train_list()
            for train in train_list:
                train_timetable = api.get_train_timetable(train.id)
                train_collection.add_train(train_timetable)
            train_collection.save()
            print("Finished train collection")
            time.sleep(SLEEP_INTERVAL)
    
    except KeyboardInterrupt:
        print("Running train collection")
        train_list = api.get_train_list()
        for train in train_list:
            train_timetable = api.get_train_timetable(train.id)
            train_collection.add_train(train_timetable)
        train_collection.save()
        print("Finished train collection")

if __name__ == "__main__":
    print("Starting STS Train Collector")
    run()