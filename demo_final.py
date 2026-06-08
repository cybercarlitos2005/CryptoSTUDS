import subprocess
import sys
import threading
import time
import requests

PORT_A = 5000
PORT_B = 5001
BASE_A = f"http://localhost:{PORT_A}"
BASE_B = f"http://localhost:{PORT_B}"

YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def titulo(n, texto):
    print(f"\n{YELLOW}{'─'*60}{RESET}")
    print(f"{BOLD}{YELLOW}  PASO {n}: {texto}{RESET}")
    print(f"{YELLOW}{'─'*60}{RESET}")

def ok(msg):   print(f"  {GREEN}[OK]{RESET} {msg}")
def info(msg): print(f"  {CYAN}->{RESET} {msg}")
def err(msg):  print(f"  {RED}[X]{RESET} {msg}")

def get(url):
    return requests.get(url, timeout=20).json()

def post(url, body):
    return requests.post(url, json=body, timeout=20).json()

def run_node(port):
    subprocess.run(
        [sys.executable, "api/node_app.py", "--port", str(port)],
        check=False,
    )

print(f"\n{BOLD}{'='*60}")
print(f"   CryptoStuds — Demo Final (Clase 5.4)")
print(f"{'='*60}{RESET}")

titulo(1, "Iniciar nodos")

for port in (PORT_A, PORT_B):
    threading.Thread(target=run_node, args=(port,), daemon=True).start()
    info(f"Nodo arrancando en :{port} ...")

time.sleep(3)

for base, label in ((BASE_A, "Nodo A :5000"), (BASE_B, "Nodo B :5001")):
    try:
        d = get(f"{base}/chain")
        ok(f"{label} activo — {d['length']} bloque(s) en cadena")
    except Exception as e:
        err(f"{label} no responde: {e}")

titulo(2, "Crear wallets secp256k1 (Carlitos, Emilio, Carlos y Gael)")

carlitos = get(f"{BASE_A}/wallet/new")["address"]
emilio   = get(f"{BASE_A}/wallet/new")["address"]
carlos   = get(f"{BASE_A}/wallet/new")["address"]
gael     = get(f"{BASE_A}/wallet/new")["address"]

ok(f"Carlitos -> {carlitos}")
ok(f"Emilio   -> {emilio}")
ok(f"Carlos   -> {carlos}")
ok(f"Gael     -> {gael}")

titulo(3, "Registrar peers mutuamente")

post(f"{BASE_A}/nodes/register", {"nodes": [BASE_B]})
post(f"{BASE_B}/nodes/register", {"nodes": [BASE_A]})
ok("Nodo A conoce a B")
ok("Nodo B conoce a A")

titulo(4, "Financiar a Carlitos y minar el primer bloque")

r1 = post(f"{BASE_A}/transaction/new", {"from": "SISTEMA", "to": carlitos, "amount": 1000})
ok(f"SISTEMA -> Carlitos : 1000 CryptoStuds  (pendientes: {r1.get('pending', '?')})")

bloque1 = get(f"{BASE_A}/mine?miner={carlitos}")
ok(f"Bloque #{bloque1['index']} minado — Carlitos recibe 1000 + 50 de recompensa")
info(f"Hash        : {bloque1['hash']}")
info(f"Merkle Root : {bloque1['merkle_root']}")
info(f"Nonce       : {bloque1['nonce']}")

titulo(5, "Enviar transacciones firmadas con ECDSA y minar el segundo bloque")

r2 = post(f"{BASE_A}/transaction/new", {"from": carlitos, "to": emilio, "amount": 250})
ok(f"Carlitos -> Emilio  :  250 CryptoStuds  (pendientes: {r2.get('pending', '?')})")

r3 = post(f"{BASE_A}/transaction/new", {"from": carlitos, "to": carlos, "amount": 150})
ok(f"Carlitos -> Carlos  :  150 CryptoStuds  (pendientes: {r3.get('pending', '?')})")

r4 = post(f"{BASE_A}/transaction/new", {"from": carlitos, "to": gael, "amount": 100})
ok(f"Carlitos -> Gael    :  100 CryptoStuds  (pendientes: {r4.get('pending', '?')})")

rx = post(f"{BASE_A}/transaction/new", {"from": carlitos, "to": emilio, "amount": 99999})
if "error" in rx:
    ok(f"Intento de doble gasto BLOQUEADO: {rx['error']}")
else:
    err("El intento de doble gasto NO fue bloqueado — revisar")

bloque2 = get(f"{BASE_A}/mine?miner={carlitos}")
ok(f"Bloque #{bloque2['index']} minado")
info(f"Hash        : {bloque2['hash']}")
info(f"Merkle Root : {bloque2['merkle_root']}")
info(f"Nonce       : {bloque2['nonce']}")
info(f"Peers notificados: {bloque2.get('peers_notified', [])}")

time.sleep(1)

titulo(6, "Verificar saldos y Merkle Root del bloque")

bal_carlitos = get(f"{BASE_A}/balance/{carlitos}")["balance"]
bal_emilio   = get(f"{BASE_A}/balance/{emilio}")["balance"]
bal_carlos   = get(f"{BASE_A}/balance/{carlos}")["balance"]
bal_gael     = get(f"{BASE_A}/balance/{gael}")["balance"]

ok(f"Carlitos : {bal_carlitos} CryptoStuds")
ok(f"Emilio   : {bal_emilio} CryptoStuds")
ok(f"Carlos   : {bal_carlos} CryptoStuds")
ok(f"Gael     : {bal_gael} CryptoStuds")

cadena = get(f"{BASE_A}/chain")
ultimo_bloque = cadena["chain"][-1]
info(f"Merkle Root en cadena: {ultimo_bloque.get('merkle_root', 'N/A')}")

validez = get(f"{BASE_A}/chain/valid")
ok(f"Integridad de cadena local: {'[OK] válida' if validez['valid'] else '[X] inválida'}")

if bal_carlitos == 600 and bal_emilio == 250 and bal_carlos == 150 and bal_gael == 100:
    print(f"  {GREEN}{BOLD}  [OK] Saldos correctos{RESET}")
else:
    print(f"  {RED}  Saldos inesperados — revisar{RESET}")

titulo(7, "Sincronizar Nodo B con /nodes/resolve")

antes_b = get(f"{BASE_B}/chain")["length"]
info(f"Nodo B antes del consenso: {antes_b} bloque(s)")

r = get(f"{BASE_B}/nodes/resolve")
ok(f"Resultado : {r['message']}")
info(f"Nodo B ahora : {r['length']} bloque(s)")

titulo(8, "Verificar consistencia final en ambos nodos")

len_a = get(f"{BASE_A}/chain")["length"]
len_b = get(f"{BASE_B}/chain")["length"]

info(f"Nodo A (:5000) -> {len_a} bloque(s)")
info(f"Nodo B (:5001) -> {len_b} bloque(s)")

if len_a == len_b:
    print(f"\n  {GREEN}{BOLD}[OK] Ambos nodos sincronizados — longitud {len_a}{RESET}")
else:
    print(f"\n  {RED}[X] Desincronizados: A={len_a}, B={len_b}{RESET}")

print(f"\n{YELLOW}{'='*60}{RESET}")
print(f"{BOLD}{YELLOW}   CryptoStuds — Demo Completada{RESET}")
print(f"{YELLOW}{'='*60}{RESET}")
print(f"""
  {GREEN}[OK]{RESET} Blockchain con PoW (dificultad 4 ceros)
  {GREEN}[OK]{RESET} Árbol de Merkle en cada bloque
  {GREEN}[OK]{RESET} Wallets con par de claves secp256k1
  {GREEN}[OK]{RESET} Transacciones firmadas con ECDSA
  {GREEN}[OK]{RESET} Validación de firma y prevención de doble gasto
  {GREEN}[OK]{RESET} API REST con Flask
  {GREEN}[OK]{RESET} Red P2P con consenso de cadena más larga
  {GREEN}[OK]{RESET} Propagación automática de bloques
""")
print(f"  {CYAN}Interfaz web: docs/index.html{RESET}")
print(f"  {CYAN}(abre en el navegador con los nodos corriendo){RESET}\n")
print(f"{YELLOW}  Presiona Ctrl+C para cerrar los nodos.{RESET}\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n  Cerrando CryptoStuds. ¡Hasta luego!\n")
