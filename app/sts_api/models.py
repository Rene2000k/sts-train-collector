
from datetime import time
from enum import Enum
from typing import List

class Flags(Enum):
    EARLY_DEPARTURE = "A"
    # TODO: flags


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
    def __init__(self, plan: Track, name: Track, arrival: time, departure: time, flags: List[Flags]) -> None:
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
        print(stop_repr)
        return "".join([f"<zug zid='{self.id}' name='{self.name}' verspaetung='{self.delay}' gleis='{self.next_track}' ",
                f"plangleis='{self.planned_track}' von='{self.from_}' nach='{self.to}' sichtbar='{self.visible}' ",
                f"amgleis='{self.currently_stopping}' usertext='{self.user_text}' usertextsender='{self.user_text_sender}' ",
                f"hinweistext='{self.note_text}'>\n",
                stop_repr,
                "<zug/>"])
