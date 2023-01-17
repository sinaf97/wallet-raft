import json
import node

class TYPES:
    LOG = "log"
    COMMIT = "commit"

class Log:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self.log = {}
        self.state_machine = {}
        self.rxid = 0 # raft transaction id
        self.prxid = 0 # previous rxid
        self.node_type = node.STATES.FOLLOWER # default log type

    def append(self, data, type):
        data = json.loads(data)
        if type == TYPES.LOG:
            if self.node_type == node.STATES.LEADER:
                self.log[self.rxid + 1] = (data["term"], data)
                self.prxid = self.rxid
                self.rxid = self.rxid + 1
            elif self.node_type == node.STATES.FOLLOWER:
                    self.log[int(data["rxid"])] = (data["term"], data)
                    self.prxid = self.rxid
                    self.rxid = int(data["rxid"])
        elif type == TYPES.COMMIT:
                self.state_machine[int(data['rxid'])] = (data["term"], data)

        return (self.prxid, self.rxid)
