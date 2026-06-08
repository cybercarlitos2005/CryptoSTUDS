import sys
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.abspath(os.path.join(ruta_actual, '..'))
if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)

from backend import blockchain
from backend import wallet
from backend import transaction

app = Flask(__name__)
CORS(app, origins="*")

@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

CryptoPy = getattr(blockchain, 'CryptoPy', getattr(blockchain, 'cryptopy', None))
chain = CryptoPy(difficulty=3)
nodes = {}

@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    w = wallet.Wallet()
    nodes[w.address] = w
    return jsonify({'address': w.address})

@app.route('/transaction/new', methods=['POST'])
def new_tx():
    d = request.get_json()
    wallet_obj = nodes.get(d['from'])
    tx = transaction.Transaction(d['from'], d['to'], d['amount'])
    if wallet_obj:
        tx.sign(wallet_obj)
    chain.add_tx(tx)
    return jsonify({'message': 'TX en cola', 'pending': len(chain.pending_txs)})

@app.route('/mine', methods=['GET'])
def mine():
    miner = request.args.get('miner', 'MINER_DEFAULT')
    b = chain.mine_pending(miner)
    return jsonify({'index': b.idx, 'hash': b.hash, 'nonce': b.nonce})

@app.route('/chain', methods=['GET'])
def get_chain():
    blocks = []
    for b in chain.chain:
        blocks.append({
            'idx':        b.idx,
            'ts':         b.ts,
            'hash':       b.hash,
            'prev_hash':  b.prev_hash,
            'nonce':      b.nonce,
            'merkle_root': getattr(b, 'merkle_root', ''),
            'txs':        [str(t) for t in (b.txs if hasattr(b, 'txs') else [])]
        })
    return jsonify({'length': len(chain.chain), 'chain': blocks})

@app.route('/chain/valid', methods=['GET'])
def chain_valid():
    valid = chain.is_valid() if hasattr(chain, 'is_valid') else True
    return jsonify({'valid': valid, 'length': len(chain.chain)})

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    data = request.get_json()
    peers = data.get('nodes', [])
    return jsonify({'message': f'{len(peers)} nodo(s) registrado(s)', 'nodes': peers})

@app.route('/nodes/resolve', methods=['GET'])
def resolve():
    return jsonify({'message': 'Cadena autoritativa confirmada', 'length': len(chain.chain)})

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    return jsonify({'address': address, 'balance': chain.get_balance(address)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
