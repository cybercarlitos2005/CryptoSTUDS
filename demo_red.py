import subprocess
import sys
import threading
import time
import requests

PORT_A, PORT_B, PORT_C = 5000, 5001, 5002
BASE_A = f"http://localhost:{PORT_A}"
BASE_B = f"http://localhost:{PORT_B}"
BASE_C = f"http://localhost:{PORT_C}"

def run_node(port):
    subprocess.run(
        [sys.executable, 'api/node_app.py', '--port', str(port)],
        check=False,
    )

for port in (PORT_A, PORT_B, PORT_C):
    threading.Thread(target=run_node, args=(port,), daemon=True).start()

print("=" * 62)
print("  CryptoPy – Demo Red P2P (Clase 5.3: Reemplazo de Cadena)")
print("=" * 62)
print("\n[demo] Esperando que los 3 nodos arranquen...")
time.sleep(2)

def length(base):
    try:
        return requests.get(f"{base}/chain", timeout=3).json()["length"]
    except Exception as e:
        return f"ERROR({e})"

def mine(base, miner, n=1):
    results = []
    for _ in range(n):
        try:
            r = requests.get(f"{base}/mine?miner={miner}", timeout=30).json()
            results.append(r)
            print(f"  [{miner}] Bloque #{r['index']} minado — hash: {r['hash'][:16]}...")
        except Exception as e:
            print(f"  [{miner}] Error minando: {e}")
    return results

def resolve(base, label):
    try:
        r = requests.get(f"{base}/nodes/resolve", timeout=10).json()
        print(f"  [{label}] {r['message']} -> longitud: {r['length']}")
        return r
    except Exception as e:
        print(f"  [{label}] Error resolviendo: {e}")

def estado(msg="Estado actual"):
    print(f"\n  [{msg}]")
    print(f"    Nodo A (:5000) -> {length(BASE_A)} bloque(s)")
    print(f"    Nodo B (:5001) -> {length(BASE_B)} bloque(s)")
    print(f"    Nodo C (:5002) -> {length(BASE_C)} bloque(s)")

print("\n[demo] Registrando peers (topología full-mesh)...")
requests.post(f"{BASE_A}/nodes/register", json={"nodes": [BASE_B, BASE_C]}, timeout=3)
requests.post(f"{BASE_B}/nodes/register", json={"nodes": [BASE_A, BASE_C]}, timeout=3)
requests.post(f"{BASE_C}/nodes/register", json={"nodes": [BASE_A, BASE_B]}, timeout=3)
print("       Todos los peers registrados.")
estado("Inicial (solo bloque génesis)")

print("\n" + "─" * 62)
print("  MISIÓN 5.3 — 5 bloques en A, 2 en B, resolver en B y C")
print("─" * 62)

print("\n[demo] Minando 5 bloques en Nodo A...")
mine(BASE_A, "MinerA", n=5)

print("\n[demo] Minando 2 bloques en Nodo B...")
mine(BASE_B, "MinerB", n=2)

estado("Antes de resolver")

print("\n[demo] Ejecutando /nodes/resolve en Nodo B...")
resolve(BASE_B, "Nodo B")

print("\n[demo] Ejecutando /nodes/resolve en Nodo C...")
resolve(BASE_C, "Nodo C")

estado("Después de resolver (deben ser iguales)")

print("\n" + "─" * 62)
print("  BONUS — Fork: A y B minan simultáneamente, C resuelve")
print("─" * 62)

results = {}

def mine_node(base, label):
    try:
        r = requests.get(f"{base}/mine?miner={label}", timeout=30).json()
        results[label] = r
    except Exception as e:
        results[label] = {"error": str(e)}

t1 = threading.Thread(target=mine_node, args=(BASE_A, "MinerA"))
t2 = threading.Thread(target=mine_node, args=(BASE_B, "MinerB"))
t1.start(); t2.start()
t1.join();  t2.join()

ra, rb = results.get("MinerA", {}), results.get("MinerB", {})
print(f"\n  Nodo A minó bloque #{ra.get('index','?')} -> {str(ra.get('hash',''))[:16]}...")
print(f"  Nodo B minó bloque #{rb.get('index','?')} -> {str(rb.get('hash',''))[:16]}...")

estado("Tras el fork (A y B divergen, C puede quedar atrás)")

print("\n[demo] Nodo A mina 1 bloque extra para romper el empate...")
mine(BASE_A, "MinerA", n=1)

print("\n[demo] Resolviendo en B y C...")
resolve(BASE_B, "Nodo B")
resolve(BASE_C, "Nodo C")

estado("Final (los 3 deben coincidir con A)")

print("\n[demo] Demo completada. Presiona Ctrl+C para salir.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[demo] Cerrando.")
