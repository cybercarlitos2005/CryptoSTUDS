import hashlib
import json
import time

def _merkle_hash(a: str, b: str) -> str:
    return hashlib.sha256((a + b).encode()).hexdigest()

def compute_merkle_root(tx_ids: list[str]) -> str:
    if not tx_ids:
        return "0" * 64

    layer = list(tx_ids)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [
            _merkle_hash(layer[i], layer[i + 1])
            for i in range(0, len(layer), 2)
        ]
    return layer[0]

class Block:

    def __init__(self, idx: int, txs: list, prev_hash: str):
        self.idx         = idx
        self.ts          = time.time()
        self.txs         = txs
        self.prev_hash   = prev_hash
        self.nonce       = 0
        self.merkle_root = self._calc_merkle()
        self.hash        = self.calc_hash()

    def _get_tx_ids(self) -> list[str]:
        ids = []
        for tx in self.txs:
            if hasattr(tx, "tx_id"):
                ids.append(tx.tx_id())
            else:

                ids.append(hashlib.sha256(
                    json.dumps(tx, sort_keys=True).encode()
                ).hexdigest())
        return ids

    def _calc_merkle(self) -> str:
        return compute_merkle_root(self._get_tx_ids())

    def calc_hash(self) -> str:
        content = json.dumps({
            "i":   self.idx,
            "ts":  self.ts,
            "p":   self.prev_hash,
            "n":   self.nonce,
            "mr":  self.merkle_root,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def mine(self, difficulty: int = 4) -> None:
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash   = self.calc_hash()

    def to_dict(self) -> dict:
        return {
            "idx":         self.idx,
            "ts":          self.ts,
            "prev_hash":   self.prev_hash,
            "nonce":       self.nonce,
            "merkle_root": self.merkle_root,
            "hash":        self.hash,
            "txs": [
                t.to_dict() if hasattr(t, "to_dict") else t
                for t in self.txs
            ],
        }
