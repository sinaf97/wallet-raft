import json
import random
from flask import Flask, request

from node import Node

app = Flask(__name__)
n = Node()


@app.route("/", methods=["POST"])
def handle():
    response = n.handle_request(json.loads(request.data))
    if response:
        return response
    return {
        "status": "Ok"
    }


class Server:
    def __init__(self, address="localhost", port=None):
        self.address = address
        self.port = port or random.randint(8000, 9000)

    def start(self):
        app.run(host=self.address, port=self.port)
