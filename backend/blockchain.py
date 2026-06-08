from backend.block import Block
from backend.transaction import Transaction

class CryptoPy:

    REWARD     = 50
    DIFFICULTY = 4

    def __init__(self, difficulty: int = DIFFICULTY):
        self.difficulty  = difficulty
        self.pending_txs: list[Transaction] = []
        self.chain       = [self._genesis()]

    def _genesis(self) -> Block:
        b = Block(0, [], "0" * 64)
        b.mine(self.difficulty)
        return b

    def add_tx(self, tx: Transaction) -> bool:
        if not tx.is_valid():
            print(f"[Blockchain] TX rechazada: firma ECDSA inválida — {tx.sender}")
            return False

        if tx.sender != "SISTEMA":
            saldo_actual = self.get_balance(tx.sender)
            pendiente_saliente = sum(
                t.amount for t in self.pending_txs
                if t.sender == tx.sender
            )
            saldo_disponible = saldo_actual - pendiente_saliente
            if saldo_disponible < tx.amount:
                print(
                    f"[Blockchain] TX rechazada: doble gasto detectado — "
                    f"saldo disponible {saldo_disponible}, intento {tx.amount}"
                )
                return False

        self.pending_txs.append(tx)
        return True

    def mine_pending(self, miner_addr: str) -> Block:
        reward_tx = Transaction("SISTEMA", miner_addr, self.REWARD)
        all_txs   = self.pending_txs + [reward_tx]

        b = Block(len(self.chain), all_txs, self.chain[-1].hash)
        b.mine(self.difficulty)

        self.chain.append(b)
        self.pending_txs = []
        return b

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.txs:
                d = tx.to_dict() if hasattr(tx, "to_dict") else tx
                if d["recipient"] == address:
                    balance += d["amount"]
                if d["sender"] == address:
                    balance -= d["amount"]
        return balance

    def chain_is_valid(self) -> bool:
        target = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.prev_hash != prev.hash:
                return False
            if not curr.hash.startswith(target):
                return False
        return True

    def chain_to_list(self) -> list:
        return [b.to_dict() for b in self.chain]
