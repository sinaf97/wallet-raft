import datetime
import json
import random
import time
import os
from multiprocessing.pool import ThreadPool
import json
import requests

from log import Log, TYPES as LOGTYPES
from walletManager import WalletManager, ACTIONS as WALLET_ACTIONS
from block import Block


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

    def __new__(cls, port, name, neighbors, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self, port=None, name="", neighbors=[]):
        self.name = name
        self.term = 1
        self.neighbors = neighbors
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
        self.db = WalletManager()
        self.current_block = Block('')

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
            if self.term != rh["term"]:
                self.term = rh["term"]
                # request for all blocks from leader
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
        results = [r and r.status_code == 200 and json.loads(
            r.content).get("vote", False) == self.name for r in results]

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

        if len(self.neighbors):
            pool = ThreadPool(processes=len(self.neighbors))
            results = pool.map(post, self.neighbors)
        else:
            results = [True]
        return results

    def broadcast_block(self, block: Block, path="/add-block"):
        # TODO: convert block into raw data
        def post(n):
            try:
                return requests.post(f"http://127.0.0.1:{n}{path}", json=block.to_string())
            except Exception as e:
                return None

        if len(self.neighbors):
            pool = ThreadPool(processes=len(self.neighbors))
            pool.map(post, self.neighbors)

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
            return self.handshake(data, path)
        elif self.state == STATES.FOLLOWER:
            self.log.append(data, type)

    def leader_port(self) -> str:
        with open("leader", "r") as f:
            port = f.read()

        return port or ""

    def handshake(self, data, path):
        results = self.broadcast(json.loads(data), path)
        results = [r and r.status_code == 200 for r in results]

        if len(results) and (results.count(True) + 1)/(len(results) + 1) > 0.5:
            return self.leader_commit(data)
        # retry till get commit
        return {'response': 'rejected'}

    def leader_commit(self, data):
        data = json.loads(data)
        # input data must have "action" key

        # send from log to state machine
        rxid = int(data['rxid'])
        self.log.append(json.dumps({'rxid': rxid}), LOGTYPES.COMMIT)

        term, data = self.log.log[rxid]
        if ('action' not in data.keys()):
            result = {'response': 'rejected'}
        else:
            res = self.db.perform_action(data['action'], data)
            print(res)
            if (res == None):
                result = {'response': 'rejected'}
            else:
                result = {'response': 'accepted', 'content': res}

        # add transaction to current block
        self.current_block.add_transaction({
            'rxid': int(data['rxid']),
            'action': WALLET_ACTIONS.REPLAY,
            'result': result,
            'data': data
        })

        # if current block completed
        if self.current_block.is_full:
            # broadcast completed Block
            self.broadcast_block(self.current_block, path='/add-block')
            self.current_block = self.current_block.next

        return result

    def follower_commit(self, rxid: int, data):
        # reply action

        # send from log to state machine
        rxid = int(data['rxid'])
        self.log.append(json.dumps({'rxid': rxid}), LOGTYPES.COMMIT)

        if ('action' not in data.keys() or data['action'] != WALLET_ACTIONS.REPLAY):
            result = {'response': 'rejected'}
        else:
            res = self.db.perform_action(data['action'], data)
            print(res)
            if (res == None):
                result = {'response': 'rejected'}
            else:
                result = {'response': 'accepted', 'content': res}
