import sys
import os
import argparse

from flask import Flask, jsonify, request
from flask_cors import CORS

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_raiz   = os.path.abspath(os.path.join(ruta_actual, ".."))
if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)

from backend.node        import CryptoPyNode
from backend.wallet      import Wallet
from backend.transaction import Transaction

app = Flask(__name__)
CORS(app)

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)))
args, _ = parser.parse_known_args()

node    = CryptoPyNode(port=args.port, difficulty=4)
wallets: dict[str, Wallet] = {}

@app.route("/chain", methods=["GET"])
def chain_info():
    return jsonify({
        "length": len(node.chain.chain),
        "chain":  node.chain.chain_to_list(),
        "port":   node.port,
    })

@app.route("/chain/valid", methods=["GET"])
def chain_valid():
    valid = node.chain.chain_is_valid()
    return jsonify({"valid": valid, "length": len(node.chain.chain)})

@app.route("/mine", methods=["GET"])
def mine():
    miner = request.args.get("miner", "MINER_DEFAULT")
    block = node.mine_and_broadcast(miner)
    return jsonify({
        "message":        "Bloque minado y propagado",
        "index":          block.idx,
        "hash":           block.hash,
        "nonce":          block.nonce,
        "merkle_root":    block.merkle_root,
        "chain_length":   len(node.chain.chain),
        "peers_notified": list(node.peers),
    })

@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    data  = request.get_json()
    peers = data.get("nodes", [])
    if not peers:
        return jsonify({"error": "Se requiere lista 'nodes'"}), 400
    for peer in peers:
        node.register_peer(peer)
    return jsonify({"message": "Peers registrados", "total_peers": list(node.peers)})

@app.route("/nodes/list", methods=["GET"])
def list_nodes():
    return jsonify({"peers": list(node.peers)})

@app.route("/nodes/resolve", methods=["GET"])
def resolve():
    replaced = node.resolve_conflicts()
    if replaced:
        return jsonify({
            "message": "Cadena reemplazada por una más larga de un peer",
            "length":  len(node.chain.chain),
        })
    return jsonify({
        "message": "La cadena local ya es la más larga",
        "length":  len(node.chain.chain),
    })

@app.route("/block/receive", methods=["POST"])
def receive_block():
    data = request.get_json()
    if not data or "block" not in data:
        return jsonify({"error": "Falta campo 'block'"}), 400
    accepted = node.receive_block(data["block"])
    if accepted:
        return jsonify({"message": "Bloque aceptado", "length": len(node.chain.chain)})
    return jsonify({"message": "Bloque rechazado o fork resuelto"}), 409

@app.route("/wallet/new", methods=["GET"])
def new_wallet():
    w = Wallet()
    wallets[w.address] = w
    return jsonify({"address": w.address})

@app.route("/transaction/new", methods=["POST"])
def new_tx():
    d  = request.get_json()
    tx = Transaction(d["from"], d["to"], d["amount"])

    w = wallets.get(d["from"])
    if w:
        tx.sign(w)

    accepted = node.chain.add_tx(tx)
    if not accepted:
        return jsonify({"error": "TX rechazada: firma inválida o saldo insuficiente"}), 400

    return jsonify({
        "message": "TX en cola",
        "pending": len(node.chain.pending_txs),
    })

@app.route("/balance/<address>", methods=["GET"])
def get_balance(address):
    return jsonify({
        "address": address,
        "balance": node.chain.get_balance(address),
    })

if __name__ == "__main__":
    print(f"[CryptoStuds] Nodo iniciando en puerto {args.port} — dificultad PoW: 4")
    app.run(host="0.0.0.0", port=args.port, debug=False)
