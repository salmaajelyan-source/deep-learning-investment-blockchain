import hashlib
import json
from datetime import datetime

class Block:
    def __init__(self, index, data, previous_hash):
        self.index = index
        self.timestamp = str(datetime.now())
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        contenu = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        texte = json.dumps(contenu, sort_keys=True)
        return hashlib.sha256(texte.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d):
        bloc = cls(d["index"], d["data"], d["previous_hash"])
        bloc.timestamp = d["timestamp"]
        bloc.hash = d["hash"]
        return bloc


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, {"message": "Bloc de genèse"}, "0")

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        nouveau = Block(
            index=len(self.chain),
            data=data,
            previous_hash=self.get_last_block().hash,
        )
        self.chain.append(nouveau)
        return nouveau

    def is_valid(self):
        for i in range(len(self.chain)):
            courant = self.chain[i]
            if courant.hash != courant.compute_hash():
                return False
            if i > 0 and courant.previous_hash != self.chain[i - 1].hash:
                return False
        return True

    def save_to_file(self, path="blockchain.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.chain], f,
                      indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, path="blockchain.json"):
        bc = cls.__new__(cls)
        with open(path, "r", encoding="utf-8") as f:
            bc.chain = [Block.from_dict(d) for d in json.load(f)]
        return bc
