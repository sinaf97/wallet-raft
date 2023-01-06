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
        self.election_timeout = random.randint(1000, 5000)

    def handle_request(self, rh):
        if rh["action"] == Actions.Vote:
            r = self.vote_for(rh)
            if r:
                return {"vote": self.my_vote}
        elif rh["action"] == Actions.Leader_ACK:
            self.leader_ack = True
        elif rh["action"] == Actions.Leader:
            self.leader_ack = True
            self.leader = rh["from"]
            self.term = rh["term"]

    def add_neighbour(self):
        self.neighbours.append(int(input("Node port: ")))

    def start(self):
        self.election_timeout_runner()

    def become_candidate(self):
        self.state = STATES.CANDIDATE
        self.term += 1
        print(f"{self.name}: I am candidate in term {self.term}")
        results = self.broadcast({
            "action": Actions.Vote,
            "from": self.name,
            "term": self.term
        })
        results = [r for r in results if r.status_code == 200]
        results = [r.status_code == 200 and json.loads(r.content).get("vote", False) == self.name for r in results]

        if len(results) and results.count(True)/len(results) > 0.5:
            self.become_leader()

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
        if self.state != STATES.CANDIDATE and self.term < candidate["term"]:
            self.my_vote = candidate["from"]
            self.term = candidate["term"]
            print(f"{self.name}: I voted for {self.my_vote} in term {self.term}")
            return True

    def become_follower(self, leader):
        self.state = STATES.FOLLOWER
        self.leader_ack = True
        self.leader = leader["from"]
        self.term = leader["term"]
        print(f"{self.name}: I became follower")

    def election_timeout_runner(self):
        start = datetime.datetime.now()
        while True:
            if self.state != STATES.LEADER:
                if self.leader_ack:
                    start = datetime.datetime.now()
                    self.election_timeout = random.randint(1000, 5000)
                    self.leader_ack = False
                elif (datetime.datetime.now() - start).total_seconds() > self.election_timeout / 1000:
                    self.become_candidate()
                    start = datetime.datetime.now()
                    self.election_timeout = random.randint(1000, 5000)
                    self.leader_ack = False

    def heartbeat(self):
        while True:
            time.sleep(0.8)
            self.broadcast({
                "action": Actions.Leader_ACK
            })
