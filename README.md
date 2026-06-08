# CryptoStuds

**Proyecto Final — Criptografía | Ingeniería en Ciberseguridad | UABCS**
**Opción A: Blockchain Core desde Cero (Python)**

Integrantes: Carlitos · Emilio · Carlos · Gael

---

## ¿Qué es?

CryptoStuds es una blockchain peer-to-peer simplificada hecha en Python, con su propia
criptomoneda. Permite crear monederos, firmar y enviar transacciones, minar bloques mediante
Prueba de Trabajo y sincronizar varios nodos en red. Incluye una interfaz web para usar todo
desde el navegador.

El detalle técnico de cada concepto (Árbol de Merkle, firmas ECDSA, consenso, etc.) se
desarrolla en el informe del proyecto.

---

## Estructura

```
CryptoSTUDS/
├── backend/        # Lógica: bloque, cadena, transacción, monedero, nodo
├── api/            # API REST en Flask
├── docs/           # Interfaz web (index.html)
├── demo_final.py   # Demostración automática
├── requirements.txt
└── render.yaml     # Configuración de despliegue
```

---

## Cómo ponerlo en marcha localmente

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Levantar un nodo de manera local

```
python api/node_app.py --port 5000
```

### 3. Abrir la interfaz

Abre `docs/index.htm` en el navegador y, en el campo *NODO*, conecta a `http://localhost:5000`.

### 4. (Opcional) Demostración automática

```bash
python demo_final.py
```

Crea monederos, envía transacciones firmadas, mina bloques y verifica la cadena de forma
automática.

---

## Uso en línea (desde cualquier dispositivo)

- **Interfaz web:** la carpeta `docs/` se publica con **GitHub Pages**
  (*Settings -> Pages -> rama `main`, carpeta `/docs`*).
- **Nodo:** se despliega en **Render** como Web Service. El archivo `render.yaml` ya trae la
  configuración; solo se conecta el repositorio y se elige el plan gratuito. Render entrega una
  URL pública que se pega en el campo *NODO* de la web.

 ### Web: 
 ```
 https://cybercarlitos2005.github.io/CryptoSTUDS/
```
 ### Nodo render: 
 ```
 https://cryptostuds.onrender.com 
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/chain` | Devuelve la cadena completa |
| GET | `/mine?miner=<dir>` | Mina un bloque nuevo |
| GET | `/wallet/new` | Genera un monedero |
| POST | `/transaction/new` | Envía una transacción |
| GET | `/balance/<dir>` | Consulta el saldo |
