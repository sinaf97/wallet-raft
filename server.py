import json
import random
from flask import Flask, request
from threading import Thread

from node import Node

app = Flask(__name__)
n = None

@app.route("/", methods=["POST"])
def handle():
    # wait till node is initialized
    while n is None: continue

    response = n.handle_request(json.loads(request.data))
    if response:
        return response
    return {
        "status": "Ok"
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
