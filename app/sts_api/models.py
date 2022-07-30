from datetime import time
from enum import Enum
from typing import List, Union


class FlagName(Enum):
    EARLY_DEPARTURE = "A"
    SCRIPT_FLAG = "B"
    DRIVE_THROUGH = "D"
    FOLLOW_UP_TRAIN = "E"
    GETS_SEPERATED = "F"
    GETS_COUPLED = "K"
    LOCO_CONVERTS = "L"
    START_LOAD_POINT = "P"
    CHANGE_DIRECTION = "R"
    LOCO_CHANGES = "W"
    
    
class EventType(Enum):
    ENTRY = "einfahrt"
    EXIT = "ausfahrt"
    ARRIVAL = "ankunft"
    DEPARTURE = "abfahrt"
    RED_LIGHT_STOP = "rothalt"
    SIGNAL_GOT_GREEN = "wurdegruen"
    COUPLE = "kuppeln"
    SEPERATE = "fluegeln"
    

class NodeType(Enum):
    SIGNAL = 2
    TRACK_LIMITING_SWITCH = 3
    SWITCH = 4
    TRACK = 5
    ENTRY = 6
    EXIT = 7
    STOPPING_POINT = 12
   
    
class Flag:
    def __init__(self, name: FlagName, number: int = 0, values: list = None) -> None:
         self.name = name
         self.number = number
         self.values = values or []
         
    def __repr__(self) -> str:
        return f"<flag name='{self.name}' number='{self.number}' values='{self.values}'/>"


class Status:
    def __init__(self, code: int, description: str) -> None:
        self.code = code
        self.desciption = description
        
    def __repr__(self) -> str:
        return f"<status code='{self.code}' >{self.desciption}</status>"
  
      
class SignalBoxInfo:
    def __init__(self, simbuild: int, name: str, id: int, region: str, online: str) -> None:
            self.simbuild = simbuild
            self.name = name
            self.id = id
            self.region = region
            self.online = online
            
    def __repr__(self) -> str:
        return f"<anlageninfo simbuild='{self.simbuild}' name='{self.name}' aid='{self.id}' region='{self.region}' online='{self.online}'/>"

           
class Track:
    def __init__(self, name: str, stopping_point: bool=False) -> None:
            self.name = name
            self.stopping_point = stopping_point
            
    def __repr__(self) -> str:
        return f"<bahnsteig name='{self.name}' haltepunkt='{self.stopping_point}'/>"
    
    
class Stop:
    def __init__(self, plan: Track, name: Track, arrival: time, departure: time, flags: List[Flag]) -> None:
        self.plan = plan
        self.name = name
        self.arrival = arrival
        self.departure = departure
        self.flags = flags
        
    def __repr__(self) -> str:
        return f"<gleis plan='{self.plan}' name='{self.name}' an='{self.arrival}' ab='{self.departure}' flags='{self.flags}'/>"
            

class Train:
    def __init__(self, id: int, name: str, delay: int=None, next_track: Track=None, planned_track: Track=None,
                 from_: str=None, to: str=None, visible: bool=None, currently_stopping: bool=None, user_text: str=None,
                 user_text_sender: str=None, note_text: str=None) -> None:
            self.id = id
            self.name = name
            self.delay = delay
            self.next_track = next_track
            self.planned_track = planned_track
            self.from_ = from_
            self.to = to
            self.visible = visible
            self.currently_stopping = currently_stopping
            self.user_text = user_text
            self.user_text_sender = user_text_sender
            self.note_text = note_text
            self.stops = []
            
    def add_stop(self, stop: Stop) -> None:
        self.stops.append(stop)
            
    def __repr__(self) -> str:
        stop_repr = [str(stop) for stop in self.stops]
        stop_repr = "\n".join(stop_repr)
        return "".join([f"<zug zid='{self.id}' name='{self.name}' verspaetung='{self.delay}' gleis='{self.next_track}' ",
                f"plangleis='{self.planned_track}' von='{self.from_}' nach='{self.to}' sichtbar='{self.visible}' ",
                f"amgleis='{self.currently_stopping}' usertext='{self.user_text}' usertextsender='{self.user_text_sender}' ",
                f"hinweistext='{self.note_text}'>\n",
                stop_repr,
                "<zug/>"])

     
class Node:
    def __init__(self, type: NodeType, name: str, enr: Union[int, None]) -> None:
         self.type = type
         self.name = name
         self.enr = enr
         
    def __repr__(self) -> str:
         return f"<shape type='{self.type}' name='{self.name}' enr='{self.enr}' />"
         
         
class Connector:
    def __init__(self, node_1: Node, node_2: Node) -> None:
         self.node_1 = node_1
         self.node_2 = node_2
         
    def __repr__(self) -> str:
         return f"<connector node1='{self.node_1}' node2='{self.node_2}' />"