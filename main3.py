import time
from threading import Thread

from node import Node
from server import Server


def run_nodes():
    server = Server(port=8002)
    Thread(target=server.start, daemon=True).start()
    time.sleep(1)
    n = Node()
    n.name = "C"
    n.neighbours = [8001, 8004, 8003]
    n.start()


if __name__ == '__main__':
    run_nodes()
