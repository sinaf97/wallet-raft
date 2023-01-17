from threading import Thread
from server import Server


def run_nodes():
    server = Server(port=8003, name="D", neighbours=[8001, 8002, 8004])
    Thread(target=server.start, daemon=True).start()
    while True: continue


if __name__ == '__main__':
    run_nodes()
