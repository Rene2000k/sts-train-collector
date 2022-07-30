import logging
import socket
import time
from turtle import st
from typing import List, Tuple, Union
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
        
        next_track = None
        if "@gleis" in resp_dict["zugdetails"]:
            next_track = next((track for track in track_list if track.name == resp_dict["zugdetails"]["@gleis"]), None) 
        planned_tack = None
        if "@plangleis" in resp_dict["zugdetails"]:
            planned_tack = next((track for track in track_list if track.name == resp_dict["zugdetails"]["@plangleis"]), None)
        
        return Train(
            int(resp_dict["zugdetails"]["@zid"]),
            resp_dict["zugdetails"]["@name"],
            int(resp_dict["zugdetails"]["@verspaetung"]),
            next_track,
            planned_tack,
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
            self._parse_flags(stop_dict["@flags"])
        ))
    
    def _parse_flags(self, flag_str: str) -> List[Flag]:
        flags = []
        
        for count, char in enumerate(flag_str):
            try:
                flag_name = FlagName(char)
            except ValueError:
                continue
            
            if flag_name in [
                FlagName.EARLY_DEPARTURE, 
                FlagName.DRIVE_THROUGH, 
                FlagName.LOCO_CONVERTS, 
                FlagName.START_LOAD_POINT, 
                FlagName.CHANGE_DIRECTION
            ]:
                flags.append(Flag(flag_name))
            
            if flag_name in [FlagName.FOLLOW_UP_TRAIN, FlagName.GETS_SEPERATED, FlagName.GETS_COUPLED]:
                # Flag structure = <flag>(<train-id>), e.g. E(78596)
                number, values = self._get_flag_train_number(flag_str, count)
                if number is not None and values is not None:
                    flags.append(Flag(flag_name, number, values))
    
            if flag_name == FlagName.SCRIPT_FLAG:
                num_count = count + 1
                # check how big the number of the flag is (e.g. 9, 35, 896, ...)
                while flag_str[num_count].isnumeric():
                    num_count += 1
                flags.append(Flag(flag_name, int(flag_str[count + 1:num_count + 1])))
                
            if flag_name == FlagName.LOCO_CHANGES:
                number, values = self._get_flag_loco_changes_ENRs(flag_str, count)
                if number is not None and values is not None:
                    flags.append(Flag(flag_name, number, values))
                
        return flags      
            
    def _get_flag_train_number(self, flag_str: str, start: int) -> Tuple[Union[int, None], Union[list, None]]:
        # Flag structure = <flag>(<train-id>), e.g. E(78596), F(1234)
        # start should be <flag>
        # returns start and end point of train number
        
        # Check for a number behind the flag (e.g. E1(59648)))
        num_start = start + 1
        while flag_str[num_start].isnumeric():
            num_start += 1
            
        # parse train number
        if flag_str[num_start] != "(":
            self.log.error(f"Error while parsing flags: No train number for flag {flag_str[start]}")
            return None, None
        # start of train number
        end = num_start + 1
        while flag_str[end].isnumeric():
            end += 1
        if flag_str[end] != ")":
            self.log.error(f"Error while parsing flags: Train number was not closed for flag {flag_str[start]}")
            return None, None
        
        if num_start - start > 1:
            return int(flag_str[start + 1:num_start]), [flag_str[num_start + 1:end]]
        return 0, [flag_str[num_start + 1:end]]
    
    def _get_flag_loco_changes_ENRs(self, flag_str: str, start: int) -> Tuple[Union[int, None], Union[list, None]]:
        # Flag structure = <flag>[<ENR1>][<ENR2>], e.g. W[12][532]
        # start should be <flag>
        # returns an optional number (e.g. 1 when W1) and both ENRs
        
        # Check for a number behind the flag (e.g. W1[1][2])
        num_start = start + 1
        while flag_str[num_start].isnumeric():
            num_start += 1
        
        # 1. ENR
        if flag_str[num_start] != "[":
            self.log.error(f"Error while parsing flags: No ENR for loco change")
            return None, None
        # start of ENR 1
        end = num_start + 1
        while flag_str[end].isnumeric():
            end += 1
        if flag_str[end] != "]":
            self.log.error(f"Error while parsing flags: ENR not closed")
            return None, None
        enr_1 = flag_str[num_start + 1:end]
        
        # 2. ENR
        start_2 = end + 1
        if flag_str[start_2] != "[":
            self.log.error(f"Error while parsing flags: No 2. ENR for loco change")
            return None, None
        # start of ENR 2
        end = start_2 + 1
        while flag_str[end].isnumeric():
            end += 1
        if flag_str[end] != "]":
            self.log.error(f"Error while parsing flags: 2. ENR not closed")
            return None, None
        enr_2 = flag_str[start_2 + 1:end]
        
        if num_start - start > 1:
            return int(flag_str[start + 1:num_start]), [enr_1, enr_2]
        return 0, [enr_1, enr_2]
    
    def create_event_listener(self, train_id: int, event: EventType):
        # req = f"<ereignis zid='{train_id}' art='{event.value}'/>"
        # resp = self._send_and_recv(req)
        # TODO
        pass
    
    def get_all_connection_elements(self) -> List[Connector]:
        req = "<wege/>"
        resp = self._send_and_recv(req)
        resp_dict = self._parse_xml(resp)
        
        nodes = self._parse_nodes(resp_dict["wege"]["shape"])          
        connectors = self._parse_connectors(resp_dict["wege"]["connector"], nodes)
        return connectors
                         
    def _parse_nodes(self, node_list: list) -> List[Node]:
        nodes = []
        for node in node_list:
            type = NodeType(int(node["@type"]))
            name = node["@name"]
            enr = None
            if  "@enr" in node:
                enr = node["@enr"]
            nodes.append(Node(type, name, enr))
        return nodes
    
    def _parse_connectors(self, connector_list: list, nodes: List[Node]) -> List[Connector]:
        connectors = []
        for connector in connector_list:
            if "@enr1" in connector and "@enr2" in connector:
                node_1 = self._find_node_by_enr(nodes, connector["@enr1"])
                node_2 = self._find_node_by_enr(nodes, connector["@enr2"])
            elif "@enr1" in connector and "@name2" in connector:
                node_1 = self._find_node_by_enr(nodes, connector["@enr1"])
                node_2 = self._find_node_by_name(nodes, connector["@name2"])
            elif "@name1" in connector and "@enr2" in connector:
                node_1 = self._find_node_by_name(nodes, connector["@name1"])
                node_2 = self._find_node_by_enr(nodes, connector["@enr2"])
            elif "@name1" in connector and "@name2" in connector:
                node_1 = self._find_node_by_name(nodes, connector["@name1"])
                node_2 = self._find_node_by_name(nodes, connector["@name2"])
            else:
                self.log.error(f"Error while parsing connector: No suiting node identifiers found for connector: {connector}")
            
            if node_1 is not None and node_2 is not None:
                connectors.append(Connector(node_1, node_2))
            elif node_1 is None:
                if "@enr1" in connector:
                    self.log.error(f"Error creating connector: Node with ENR {connector['@enr1']} not found")
                else:
                    self.log.error(f"Error creating connector: Node with name {connector['@name1']} not found")
            elif node_2 is None:
                if "@enr2" in connector:
                    self.log.error(f"Error creating connector: Node with ENR {connector['@enr2']} not found")
                else:
                    self.log.error(f"Error creating connector: Node with name {connector['@name2']} not found")
        
        return connectors
                
    def _find_node_by_enr(self, nodes: List[Node], enr: int) -> Union[Node, None]:
        for node in nodes:
            if node.enr == enr:
                return node
        return None
    
    def _find_node_by_name(self, nodes: List[Node], name: str) -> Union[Node, None]:
        for node in nodes:
            if node.name == name:
                return node
        return None
                                    
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
