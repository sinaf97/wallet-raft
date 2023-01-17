import datetime
import json
import random
import time, os
from multiprocessing.pool import ThreadPool
from log import Log, TYPES as LOGTYPES
import json

import requests


class STATES:
    """
    Node states in static mode to prevent using raw strings or numbers
    """
    CANDIDATE = "Candidate"
    LEADER = "Leader"
    FOLLOWER = "Follower"


class Actions:
    """
    Node actions in static mode to prevent using raw strings or numbers
    """
    Vote = 0
    Leader = 1
    Leader_ACK = 2


class Node(object):
    """
    Node class
    It is singleton to let the flask server find it easily in the process.
    This class is responsible for leader election and consensus algorithm `raft`
    """
    instance = None

    def __new__(cls, port, name, neighbours, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self, port=None, name="", neighbours=[]):
        self.name = name
        self.term = 1
        self.neighbours = neighbours
        self.state = STATES.FOLLOWER
        self.leader = None
        self.leader_ack = False
        self.my_vote = None
        self.heartbeat_timer = 500      # ms
        self.random_timeout = lambda: random.randint(2000, 5000)    # ms
        self.election_timeout = self.random_timeout()
        self.port = port
        self.log_votes = {}
        self.log = Log()

    def handle_request(self, rh):
        """
        Handles incoming requests from other nodes
        We have three actions:
            - vote: casts vote for a node if requirements are met
            - leader ack: resets election_timeout to prevent re-election
            - leader: sets a new leader for this node and ends the leader election process
        """
        if rh["action"] == Actions.Vote:
            self.vote_for(rh)
            return {"vote": self.my_vote}

        elif rh["action"] == Actions.Leader_ACK:
            self.leader_ack = True
            self.leader = rh["from"]
            self.term = rh["term"]
        elif rh["action"] == Actions.Leader:
            self.become_follower(rh)

    def start(self):
        self.election_timeout_runner()

    def become_candidate(self):
        """
        sets the node state to CANDIDATE and broadcasts a message to collect votes
        if it has more than 50% of the votes, it elects itself as the leader and broadcasts it.
        """
        self.state = STATES.CANDIDATE
        print(f"{self.name}: I am candidate in term {self.term}")
        results = self.broadcast({
            "action": Actions.Vote,
            "from": self.name,
            "term": self.term
        })
        results = [r and r.status_code == 200 and json.loads(r.content).get("vote", False) == self.name for r in results]

        if len(results) and (results.count(True) + 1)/(len(results) + 1) > 0.5:
            self.become_leader()
        else:
            self.state = STATES.FOLLOWER

    def broadcast(self, data, path="/"):
        """
        broadcasts a message(data) to all other nodes in a parallel manner using Threads
        """
        def post(n):
            try:
                return requests.post(f"http://127.0.0.1:{n}{path}", json=data)
            except Exception as e:
                return None

        if len(self.neighbours):
            pool = ThreadPool(processes=len(self.neighbours))
            results = pool.map(post, self.neighbours)
        else:
            results = [True]
        return results

    def become_leader(self):
        """
        this method is called after a candidate elects itself as the leader.
        it updates the node's state and broadcasts its leadership to others.
        it also starts the heartbeat process, assuring people of their leader being alive and healthy.
        """
        self.log.node_type = STATES.LEADER
        self.state = STATES.LEADER
        self.leader = self
        self.term += 1
        self.broadcast({
            "action": Actions.Leader,
            "from": self.name,
            "term": self.term
        })

        # store leader address, simply port here
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + '/leader', 'w') as f:
            f.write(str(self.port))

        print(f"{self.name}: I am the leader in term {self.term}")
        self.heartbeat()

    def vote_for(self, candidate):
        """
        It decides whether to vote for a candidate or not

        Only the followers can vote and once they vote in a term, they can't change their vote unless
        they themselves become a candidate to clear their vote history
        """
        if self.state == STATES.FOLLOWER and not self.my_vote:
            self.my_vote = candidate["from"]
            self.term = candidate["term"]
            print(f"{self.name}: I voted for {self.my_vote} in term {self.term}")

    def become_follower(self, leader):
        """
        It sets a node to be a follower, cancelling its candidate status if exists.
        """
        self.log.node_type = STATES.FOLLOWER
        self.state = STATES.FOLLOWER
        self.leader_ack = True
        self.leader = leader["from"]
        self.term = leader["term"]
        print(f"{self.name}: I became a follower of {self.leader}")

    def election_timeout_runner(self):
        """
        It controls the flow of consensus.
        This method waits for the leader ack to reset the election timeout, else it steps in
        to be a candidate.
        If it fails to become the leader, the timeout starts and the flow is carried on again.
        """
        start = datetime.datetime.now()
        while True:
            if self.state != STATES.LEADER:
                if self.leader_ack:
                    start = datetime.datetime.now()
                    self.election_timeout = self.random_timeout()
                    self.leader_ack = False
                elif ((datetime.datetime.now() - start).total_seconds() * 1000) > self.election_timeout:
                    self.my_vote = None
                    self.become_candidate()
                    start = datetime.datetime.now()
                    self.election_timeout = self.random_timeout()
                    self.leader_ack = False

    def heartbeat(self):
        """
        It broadcasts the heartbeat message as long as the node is alive
        """
        while self.state == STATES.LEADER:
            self.broadcast({
                "action": Actions.Leader_ACK,
                "from": self.name,
                "term": self.term
            })
            time.sleep(self.heartbeat_timer/1000)

    def append_entry(self, data, path, type):
        if type == LOGTYPES.LOG:
            if (self.state == STATES.LEADER):
                # add mandatory data to payload
                data = json.loads(data)
                data["term"] = self.term
                data = json.dumps(data)
                (prxid, rxid) = self.log.append(data, type)

                data = json.loads(data)
                # we will count votes later
                self.log_votes[rxid] = set()
                data["rxid"] = rxid
                data = json.dumps(data)

                # initialize handshake
                self.handshake(data, path, type)
            elif self.state == STATES.FOLLOWER:
                self.vote_for_commit(rxid)
        elif type == LOGTYPES.COMMIT:
            if (self.state == STATES.LEADER):
                self.handshake(data, path, type)
            elif self.state == STATES.FOLLOWER:
                (prxid, rxid) = self.log.append(data, type)

    def leader_port(self) -> str:
        with open("leader", "r") as f:
            port = f.read()

        return port or ""

    def vote_for_commit(self, rxid):
        port = self.leader_port()
        if not port.isnumeric():
            return False

        requests.post(f"http://127.0.0.1:{port}/log", {
                "port": port,
                "rxid": rxid,
                "term": self.term
            })

        return True

    def wait_till_commit(self, data):
        if self.state != STATES.LEADER:
            return (False, "")

        data = json.loads(data)
        if data["term"] < self.term:
            return (False, "")

        self.log_votes.add(data["port"])

        # we know the number of nodes but there is a problem here
        if len(self.log_votes) / 3 > 0.5:
            return (True, data["rxid"])

        return (False, "")

    def handshake(self, data, path, type):
        if self.state == STATES.LEADER:
            return False

        if type == LOGTYPES.LOG:
            self.broadcast(data, path, type)
        elif type == LOGTYPES.COMMIT:
            if (self.commit(data)):
                self.broadcast(data, path, type)

        return True

    def commit(self, data):
        # `data`` should be the result after the execution
        # self.log.append(data, type=commit)
        pass
