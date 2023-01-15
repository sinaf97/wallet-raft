import time
from threading import Thread

from node import Node
from server import Server


def run_nodes():
    server = Server(port=8001, name="B", neighbours=[8004, 8002, 8003])
    Thread(target=server.start, daemon=True).start()
    while True: continue


if __name__ == '__main__':
    run_nodes()
