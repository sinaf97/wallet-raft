import hashlib
import json


class Block:
    def __init__(self, prev_hash):
        self.transactions = []
        self.prev_hash = prev_hash
        self.next = None
        self.hash = None

    def make_hash(self):
        if self.is_full:
            self.hash = hashlib.sha256(json.dumps({
                'transactions': self.transactions,
                'prev_hash': self.prev_hash,
            }))

    @property
    def is_full(self):
        return len(self.transactions) >= 2

    def add_transaction(self, tr):
        if self.is_full:
            self.make_hash()
            next_block = Block(self.hash)
            self.next = next_block
            next_block.add_transaction(tr)
        else:
            self.transactions.append(tr)
