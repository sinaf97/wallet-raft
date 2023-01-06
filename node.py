import datetime
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.pool import ThreadPool
from threading import Thread

import requests


class STATES:
    CANDIDATE = "Candidate"
    LEADER = "Leader"
    FOLLOWER = "Follower"


class Actions:
    Vote = 0
    Leader = 1
    Leader_ACK = 2


class Node(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self.name = None
        self.term = 1
        self.neighbours = []
        self.state = STATES.FOLLOWER
        self.leader = None
        self.leader_ack = False
        self.my_vote = None
        self.election_timeout = random.randint(2, 5)

    def handle_request(self, rh):
        if rh["action"] == Actions.Vote:
            r = self.vote_for(rh)
            if r:
                return {"vote": self.my_vote}
        elif rh["action"] == Actions.Leader_ACK:
            self.leader_ack = True
            self.leader = rh["from"]
            self.term = rh["term"]
        elif rh["action"] == Actions.Leader:
            self.become_follower(rh)

    def add_neighbour(self):
        self.neighbours.append(int(input("Node port: ")))

    def start(self):
        self.election_timeout_runner()

    def become_candidate(self):
        self.state = STATES.CANDIDATE
        # self.term += 1
        print(f"{self.name}: I am candidate in term {self.term}")
        results = self.broadcast({
            "action": Actions.Vote,
            "from": self.name,
            "term": self.term
        })
        results = [r.status_code == 200 and json.loads(r.content).get("vote", False) == self.name for r in results]

        if len(results) and (results.count(True) + 1)/(len(results) + 1) > 0.5:
            self.become_leader()
        else:
            self.state = STATES.FOLLOWER

    def broadcast(self, data):
        def post(n):
            try:
                return requests.post(f"http://127.0.0.1:{n}", json=data)
            except Exception as e:
                return None

        if len(self.neighbours):
            pool = ThreadPool(processes=len(self.neighbours))
            results = pool.map(post, self.neighbours)
        else:
            results = [True]
        return results

    def become_leader(self):
        self.state = STATES.LEADER
        self.leader = self
        self.term += 1
        self.broadcast({
            "action": Actions.Leader,
            "from": self.name,
            "term": self.term
        })
        print(f"{self.name}: I am the leader in term {self.term}")
        self.heartbeat()

    def vote_for(self, candidate):
        if self.state == STATES.FOLLOWER and not self.my_vote:
            self.my_vote = candidate["from"]
            self.term = candidate["term"]
            print(f"{self.name}: I voted for {self.my_vote} in term {self.term}")
            return True

    def become_follower(self, leader):
        self.state = STATES.FOLLOWER
        self.leader_ack = True
        self.leader = leader["from"]
        self.term = leader["term"]
        print(f"{self.name}: I became a follower of {self.leader}")

    def election_timeout_runner(self):
        start = datetime.datetime.now()
        while True:
            if self.state != STATES.LEADER:
                if self.leader_ack:
                    start = datetime.datetime.now()
                    self.election_timeout = random.randint(2, 5)
                    self.leader_ack = False
                elif (datetime.datetime.now() - start).total_seconds() > self.election_timeout:
                    print("************ shit **********")
                    self.my_vote = None
                    self.become_candidate()
                    start = datetime.datetime.now()
                    self.election_timeout = random.randint(2, 5)
                    self.leader_ack = False

    def heartbeat(self):
        while self.state == STATES.LEADER:
            self.broadcast({
                "action": Actions.Leader_ACK,
                "from": self.name,
                "term": self.term
            })
            time.sleep(0.5)
