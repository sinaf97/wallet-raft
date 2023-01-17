import json
import random
from flask import Flask, request
from threading import Thread

from node import Node
from log import TYPES as LOGTYPES

app = Flask(__name__)
n = None

@app.before_request
def middleware():
    # wait till node is initialized
    while n is None: continue

@app.route("/", methods=["POST"])
def handle():
    response = n.handle_request(json.loads(request.data))
    if response:
        return response
    return {
        "status": "Ok"
    }

@app.route("/add", methods=["POST"])
def add_to_wallet():
    n.append_entry(request.data, request.path, LOGTYPES.LOG)
    return {
        "status": "Ok"
    }

@app.route("/log", methods=["POST"])
def trigger_commit():
    (result, rxid) = n.wait_till_commit(request.data)
    if result:
        n.append_entry(request.data, request.path, LOGTYPES.COMMIT)
        return {
            "status": "Ok"
        }

    return {
        "status": "Error"
    }

class Server:
    def __init__(self, address="localhost", name="", neighbours=[], port=None):
        global n
        self.address = address
        self.port = port or random.randint(8000, 9000)
        node = Node(port, name, neighbours)
        Thread(target=node.start, daemon=True).start()
        n = node

    def start(self):
        app.run(host=self.address, port=self.port)
