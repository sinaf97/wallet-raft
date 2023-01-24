import hashlib
import json


class Block:
    def __init__(self, prev_hash, index=1, root=None):
        self.index = index
        self.transactions = []
        self.prev_hash = prev_hash
        self.next = None
        self.hash = None
        self.root = root or self
        self.index = index

    def make_hash(self):
        if self.is_full:
            self.hash = hashlib.sha256(json.dumps({
                'index': self.index,
                'transactions': self.transactions,
                'prev_hash': self.prev_hash,
            }).encode()).hexdigest()

    @property
    def is_full(self):
        return len(self.transactions) >= 2

    def add_transaction(self, tr):
        self.transactions.append(tr)
        if self.is_full:
            self.make_hash()
            next_block = Block(self.hash, self.index+1, self.root)
            self.next = next_block
            return next_block
        return self

    def to_string(self):
        return json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash
        })

    @staticmethod
    def from_string(root, block):
        block_dict = json.loads(json.loads(block))

        new_block = Block(block_dict["prev_hash"], block_dict["index"], root)
        new_block.transactions = block_dict["transactions"]

        return new_block

    def root_to_dict(self) -> dict:
        if self.root == self:
            return self.deep_to_dict()
        else:
            return self.root.root_to_dict()

    def deep_to_dict(self) -> dict:
        return {
            "index": self.index,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
            "next": self.next.deep_to_dict()
        }
