import hashlib
import json
import requests

from backend.blockchain import CryptoPy
from backend.block import Block, compute_merkle_root
from backend.transaction import Transaction

class CryptoPyNode:

    def __init__(self, port: int, difficulty: int = 4):
        self.port   = port
        self.peers: set[str] = set()
        self.chain  = CryptoPy(difficulty=difficulty)

    def register_peer(self, peer_url: str) -> None:
        url = peer_url.rstrip("/")
        self.peers.add(url)
        print(f"[Node:{self.port}] Peer registrado: {url}")

    def remove_peer(self, peer_url: str) -> None:
        self.peers.discard(peer_url.rstrip("/"))

    def broadcast_new_block(self, block: Block) -> None:
        for peer in self.peers:
            try:
                resp = requests.post(
                    f"{peer}/block/receive",
                    json={"block": block.to_dict()},
                    timeout=3,
                )
                print(f"[Node:{self.port}] Bloque #{block.idx} -> {peer} ({resp.status_code})")
            except requests.exceptions.ConnectionError:
                print(f"[Node:{self.port}] Sin conexión con {peer}")

    def mine_and_broadcast(self, miner_addr: str) -> Block:
        block = self.chain.mine_pending(miner_addr)
        self.broadcast_new_block(block)
        return block

    def receive_block(self, block_data: dict) -> bool:
        last = self.chain.chain[-1]

        if (block_data["prev_hash"] == last.hash
                and block_data["idx"] == last.idx + 1):

            txs = [
                Transaction(t["sender"], t["recipient"], t["amount"])
                for t in block_data.get("txs", [])
            ]
            b             = Block(block_data["idx"], txs, block_data["prev_hash"])
            b.nonce       = block_data["nonce"]
            b.ts          = block_data["ts"]
            b.merkle_root = block_data.get("merkle_root", "0" * 64)
            b.hash        = block_data["hash"]

            if not b.hash.startswith("0" * self.chain.difficulty):
                print(f"[Node:{self.port}] Bloque rechazado: PoW inválido.")
                return False

            self.chain.chain.append(b)
            print(f"[Node:{self.port}] Bloque #{b.idx} aceptado.")
            return True

        print(f"[Node:{self.port}] Bloque #{block_data['idx']} no encaja; resolviendo fork...")
        return self.resolve_conflicts()

    def resolve_conflicts(self) -> bool:
        max_length = len(self.chain.chain)
        new_chain  = None

        for peer_url in self.peers:
            try:
                r = requests.get(f"{peer_url}/chain", timeout=5)
                if r.status_code != 200:
                    continue
                peer_length = r.json()["length"]
                peer_chain  = r.json()["chain"]

                if peer_length > max_length and self._validate_chain(peer_chain):
                    max_length = peer_length
                    new_chain  = peer_chain

            except Exception as e:
                print(f"[Node:{self.port}] Error contactando {peer_url}: {e}")

        if new_chain:
            self.chain.chain = self._rebuild_chain(new_chain)
            print(f"[Node:{self.port}] Cadena reemplazada. Longitud: {max_length}")
            return True

        print(f"[Node:{self.port}] Cadena local es autoritativa. Longitud: {max_length}")
        return False

    def _validate_chain(self, raw_chain: list) -> bool:
        target = "0" * self.chain.difficulty

        for i in range(1, len(raw_chain)):
            curr = raw_chain[i]
            prev = raw_chain[i - 1]

            if curr["prev_hash"] != prev["hash"]:
                print(f"[Node:{self.port}] Cadena inválida: hash roto en bloque {i}")
                return False

            if not curr["hash"].startswith(target):
                print(f"[Node:{self.port}] Cadena inválida: PoW inválido en bloque {i}")
                return False

            content = json.dumps({
                "i":  curr["idx"],
                "ts": curr["ts"],
                "p":  curr["prev_hash"],
                "n":  curr["nonce"],
                "mr": curr.get("merkle_root", "0" * 64),
            }, sort_keys=True)
            recalc = hashlib.sha256(content.encode()).hexdigest()
            if recalc != curr["hash"]:
                print(f"[Node:{self.port}] Cadena inválida: hash manipulado en bloque {i}")
                return False

            tx_ids = [
                hashlib.sha256(
                    json.dumps(
                        {k: t[k] for k in ("sender", "recipient", "amount", "ts")},
                        sort_keys=True
                    ).encode()
                ).hexdigest()
                for t in curr.get("txs", [])
            ]
            expected_mr = compute_merkle_root(tx_ids)
            if expected_mr != curr.get("merkle_root", expected_mr):
                print(f"[Node:{self.port}] Cadena inválida: Merkle Root incorrecta en bloque {i}")
                return False

        return True

    def _rebuild_chain(self, raw_chain: list) -> list:
        blocks = []
        for data in raw_chain:
            txs = [
                Transaction(t["sender"], t["recipient"], t["amount"])
                for t in data.get("txs", [])
            ]
            b             = Block(data["idx"], txs, data["prev_hash"])
            b.nonce       = data["nonce"]
            b.ts          = data["ts"]
            b.merkle_root = data.get("merkle_root", "0" * 64)
            b.hash        = data["hash"]
            blocks.append(b)
        return blocks
