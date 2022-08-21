
import logging
import os
import time
from typing import Dict, Union
from sts_api.models import Train, Stop, Track


class TrainCollection:
    TIME_FORMAT = "%H:%M"
    DATA_FOLDER = "data"
    NUMBER_STOP_POSITIONS = 4
    TITLE_LINE = "id;name;from;to;track;arrival;departure;flags\n"
    
    def __init__(self, name: str) -> None:
        self.log = logging.getLogger(__class__.__name__)
        self.name = name
        self.filename: str = f"{self.DATA_FOLDER}/{name}.csv"
        self.already_saved_trains = [] # train ids
        self.save_train_dict: Dict[int, Train] = {}
        self.load()
        
    def load(self) -> None:
        if os.path.isfile(self.filename):
            self.log.info(f"Loading csv file: {self.filename}")
            
            with open(self.filename, "r") as file:
                line_list = file.readlines()
                for line in line_list:
                    if line == self.TITLE_LINE:
                        continue
                    
                    train = self._parse_csv_line(line)
                    if train is None:
                        self.log.error("Error parsing train - Skipping")
                    else:
                        self.already_saved_trains.append(train.id)
            
            self.log.info(f"Successfully loaded {self.filename}")
                    
    def _parse_csv_line(self, line: str) -> Union[Train, None]:
        line_split = line.split(";")
        
        if len(line_split) > 4:
            train_id = line_split[0]
            train_name = line_split[1]
            from_ = line_split[2]
            to = line_split[3]
            train = Train(train_id, train_name, from_=from_, to=to)
            line_pos = 4
            
            # \n
            while len(line_split) >= line_pos + self.NUMBER_STOP_POSITIONS + 1:
                stop_name = line_split[line_pos]
                try:
                    if line_split[line_pos + 1] != "":
                        stop_arrival = time.strptime(line_split[line_pos + 1], self.TIME_FORMAT)
                    else:
                        stop_arrival = None
                    if line_split[line_pos + 2] != "":
                        stop_departure = time.strptime(line_split[line_pos + 2], self.TIME_FORMAT)  
                    else:
                        stop_departure = None
                except ValueError as err:
                    self.log.error(f"Could not parse departure or arrival time: {err}")
                    return None
                
                track = Track(stop_name)
                stop = Stop(track, track, stop_arrival, stop_departure, [])
                train.add_stop(stop)
                line_pos += self.NUMBER_STOP_POSITIONS
            
            # \n
            if len(line_split) != line_pos + 1:
                self.log.warn(f"Unexpected line length for train {train.name}. Some stops my not be parsed!")
            
            return train
        
        else:
            self.log.error(f"Could not parse line: {line}: Not enough entries")
            return None
        
    def save(self) -> None:
        saved_trains = []
        
        self.log.info("Saving new trains")
        if not os.path.isdir(self.DATA_FOLDER):
            os.makedirs(self.DATA_FOLDER, exist_ok=True)
        
        add_title_line = False    
        if not os.path.isfile(self.filename):
            add_title_line = True
            
        with open(self.filename, "a") as file:
            if add_title_line:
                file.write(self.TITLE_LINE)
            
            for train in self.save_train_dict.values():
                line = self._train_to_csv_line(train)
                file.write(f"{line}\n")
                saved_trains.append(train.id)
        self.log.info("Saved trains")
        
        for train_id in saved_trains:
            self.save_train_dict.pop(train_id)
        self.already_saved_trains.extend(saved_trains)       
     
    def _train_to_csv_line(self, train: Train) -> str:
        line = f"{train.id};{train.name};{train.from_};{train.to}"
        
        for stop in train.stops:
            if stop.arrival is not None:
                arrival_formatted = stop.arrival.strftime(self.TIME_FORMAT)
            else:
                arrival_formatted = ""
            if stop.departure is not None:
                departure_formatted = stop.departure.strftime(self.TIME_FORMAT)
            else:
                departure_formatted = ""
            line += f";{stop.plan.name};{arrival_formatted};{departure_formatted}"
            
            flags_str = ";"
            for flag in stop.flags:
                value_str = ""
                for value in flag.values:
                    value_str += f"{value},"
                
                flags_str += f"[{flag.name}{flag.number}({value_str})]"
                
            line += flags_str
        
        return line + ";"
        
    def add_train(self, train: Train) -> None:
        if str(train.id) not in self.already_saved_trains:
            self.save_train_dict[train.id] = train