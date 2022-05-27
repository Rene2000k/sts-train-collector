import logging
import socket
from datetime import time
from typing import List
import xmltodict

from sts_api.models import *

class STSApi:
    HOST = "localhost"
    PORT = 3691

    def __init__(self) -> None:
        self.log = logging.getLogger(__class__.__name__)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.1)
        
    def connect(self) -> Status:
        try:
            self.socket.connect((self.HOST, self.PORT))
        except (ConnectionRefusedError, TimeoutError):
            self.log.error("Could not connect to STS plugin interface") 
            raise
        else:
            self.log.info("Connected to STS plugin interface")
            # receive register message
            resp = self._recv()
            resp_dict = self._parse_xml(resp)
            return Status(int(resp_dict["status"]["@code"]), resp_dict["status"]["#text"])
            
    def register(self, name: str, author: str, version: str, desc: str, protocol_version: int = 1) -> Status:
        req = f"<register name='{name}' autor='{author}' version='{version}' protokoll='{protocol_version}' text='{desc}' />"
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        return Status(int(resp_dict["status"]["@code"]), resp_dict["status"]["#text"])
        
    def get_simtime(self) -> int:
        current_unix_time = time.time()
        req = f"<simzeit sender='{current_unix_time}' />"
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        return int(resp_dict["simzeit"]["@zeit"])
    
    def get_signal_box_info(self) -> SignalBoxInfo:
        req = "<anlageninfo />"
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        return SignalBoxInfo(
            int(resp_dict["anlageninfo"]["@simbuild"]), 
            resp_dict["anlageninfo"]["@name"], 
            int(resp_dict["anlageninfo"]["@aid"]),
            resp_dict["anlageninfo"]["@region"],
            resp_dict["anlageninfo"]["@online"]
        )
    
    def get_track_list(self) -> List[Track]:
        req = "<bahnsteigliste />"
        track_list = []
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        for track in resp_dict["bahnsteigliste"]["bahnsteig"]:
            track_list.append(Track(track["@name"], self._str_to_bool(track["@haltepunkt"])))
        return track_list
    
    def get_train_list(self) -> List[Train]:
        req = "<zugliste />"
        train_list = []
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        for train in resp_dict["zugliste"]["zug"]:
            train_list.append(Train(int(train["@zid"]), train["@name"]))
        return train_list
    
    def get_train_details(self, train_id: int) -> Train:
        req = f"<zugdetails zid='{train_id}' />"
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        track_list = self.get_track_list()
        return Train(
            int(resp_dict["zugdetails"]["@zid"]),
            resp_dict["zugdetails"]["@name"],
            int(resp_dict["zugdetails"]["@verspaetung"]),
            next((track for track in track_list if track.name == resp_dict["zugdetails"]["@gleis"]), None),
            next((track for track in track_list if track.name == resp_dict["zugdetails"]["@plangleis"]), None),
            resp_dict["zugdetails"]["@von"],
            resp_dict["zugdetails"]["@nach"],
            self._str_to_bool(resp_dict["zugdetails"]["@sichtbar"]),
            self._str_to_bool(resp_dict["zugdetails"]["@amgleis"]),
            resp_dict["zugdetails"]["@usertext"],
            resp_dict["zugdetails"]["@usertextsender"],
            resp_dict["zugdetails"]["@hinweistext"] if "@hinweistext" in resp_dict["zugdetails"] else None
        )
        
    def get_train_timetable(self, train_id: int) -> Train:
        req = f"<zugfahrplan zid='{train_id}' />"
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        
        train = self.get_train_details(train_id)
        track_list = self.get_track_list()
        
        if isinstance(resp_dict["zugfahrplan"]["gleis"], list):
            for stop in resp_dict["zugfahrplan"]["gleis"]:
                self._add_stop(train, track_list, stop)
        else:
            self._add_stop(train, track_list, resp_dict["zugfahrplan"]["gleis"])
        return train
    
    def _add_stop(self, train: Train, track_list: List[Track], stop_dict: dict) -> None:
        arrival_time_splitted = None
        departure_time_splitted = None
        
        if "@an" in stop_dict and stop_dict["@an"] != "":
            arrival_time_splitted = stop_dict["@an"].split(":")
        if "@ab" in stop_dict and stop_dict["@ab"] != "":
            departure_time_splitted = stop_dict["@ab"].split(":")
        
        train.add_stop(Stop(
            next((track for track in track_list if track.name == stop_dict["@plan"]), None),
            next((track for track in track_list if track.name == stop_dict["@name"]), None),
            time(hour=int(arrival_time_splitted[0]), minute=int(arrival_time_splitted[1])) if arrival_time_splitted else None,
            time(hour=int(departure_time_splitted[0]), minute=int(departure_time_splitted[1])) if departure_time_splitted else None,
            # TODO: flags parsen
            stop_dict["@flags"]
        ))
            
    def _send_and_recv(self, msg: str) -> str:
        self._send(msg)
        return self._recv()
    
    def _send(self, msg: str) -> None:
        try:
            self.socket.send(bytes(msg + "\n", "UTF-8"))
        except Exception:
            self.log.error("Failed to send data to socket")
            raise
    
    def _recv(self) -> str:
        msg = ""
        received_at_least_one = False
        while True:
            try:
                recv_data = self.socket.recv(4096)
                msg += str(recv_data, "UTF-8")
                received_at_least_one = True
            except Exception:
                if not received_at_least_one:
                    self.log.error("Failed to receive data from socket")
                    raise
                else:
                    return msg
               
    def _parse_xml(self, xml_str: str) -> dict:
        return xmltodict.parse(xml_str)
    
    def _str_to_bool(self, input: str) -> bool:
        if input in ["True", "true"]:
            return True
        return False
