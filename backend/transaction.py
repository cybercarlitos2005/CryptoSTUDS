import hashlib
import json
import time

from backend.wallet import Wallet

class Transaction:

    def __init__(self, sender: str, recipient: str, amount: float):
        self.sender    = sender
        self.recipient = recipient
        self.amount    = amount
        self.ts        = time.time()
        self.sig       = None
        self.pub_pem   = None

    def _signable(self) -> dict:
        return {
            "sender":    self.sender,
            "recipient": self.recipient,
            "amount":    self.amount,
            "ts":        self.ts,
        }

    def sign(self, wallet: "Wallet") -> None:
        self.pub_pem = wallet.pub_pem
        self.sig     = wallet.sign_tx(self._signable())

    def is_valid(self) -> bool:
        if self.sender == "SISTEMA":
            return True
        if not self.sig or not self.pub_pem:
            return False
        return Wallet.verify_signature(self.pub_pem, self._signable(), self.sig)

    def tx_id(self) -> str:
        return hashlib.sha256(
            json.dumps(self._signable(), sort_keys=True).encode()
        ).hexdigest()

    def to_dict(self) -> dict:
        return {
            "sender":    self.sender,
            "recipient": self.recipient,
            "amount":    self.amount,
            "ts":        self.ts,
            "signature": self.sig,
            "pub_pem":   self.pub_pem,
        }
