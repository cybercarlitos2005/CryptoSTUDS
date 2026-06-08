import hashlib
import json

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature, encode_dss_signature
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

class Wallet:

    def __init__(self):

        self._priv = ec.generate_private_key(ec.SECP256K1(), default_backend())
        self._pub  = self._priv.public_key()

        pub_bytes    = self._pub.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.CompressedPoint
        )
        self.address = hashlib.sha256(pub_bytes).hexdigest()[:40]

        self.pub_pem = self._pub.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def sign_tx(self, tx_data: dict) -> str:
        payload = json.dumps(tx_data, sort_keys=True).encode()
        sig_der  = self._priv.sign(payload, ec.ECDSA(hashes.SHA256()))
        return sig_der.hex()

    @staticmethod
    def verify_signature(pub_pem: str, tx_data: dict, sig_hex: str) -> bool:
        try:
            pub_key = serialization.load_pem_public_key(
                pub_pem.encode(), backend=default_backend()
            )
            payload = json.dumps(tx_data, sort_keys=True).encode()
            sig_der = bytes.fromhex(sig_hex)
            pub_key.verify(sig_der, payload, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False
