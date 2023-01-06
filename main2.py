import time
from threading import Thread

from node import Node
from server import Server


def run_nodes():
    server = Server(port=8001)
    Thread(target=server.start, daemon=True).start()
    time.sleep(1)
    n = Node()
    n.name = "B"
    n.neighbours = [8004, 8002, 8003]
    n.start()


if __name__ == '__main__':
    run_nodes()
