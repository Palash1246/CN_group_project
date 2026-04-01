# Secure Multiplayer Leaderboard System

Socket Programming Mini Project — PES University

---

## Overview

This project implements a **secure client–server leaderboard system** using low-level socket programming in Python.

Multiple clients connect to a server simultaneously and update player scores. The server maintains a shared leaderboard and responds to client requests in real time. All communication is encrypted using TLS/SSL.

The project demonstrates core networking concepts including:

* TCP socket communication
* TLS encrypted communication
* Concurrent client handling with threads
* Custom application-layer protocol design
* Client name registration handshake
* Server-side capacity enforcement (50-client limit)
* Performance evaluation under load
* GUI dashboards for server, client, and stress testing

---

## System Architecture

The project follows a **Client–Server Architecture**.

* The **server** listens for incoming TLS-secured TCP connections.
* Each client connection is handled in a **separate thread**.
* After the SSL handshake, the server performs a **name registration handshake** — it asks the client for their name before accepting any commands.
* Clients send commands to update scores or retrieve the leaderboard.
* A shared leaderboard is maintained with **thread-safe access using locks**.
* The server enforces a **hard limit of 50 concurrent clients**. Any connection beyond this receives a `SERVER_FULL` response and is rejected gracefully.

```
            +---------------------------+
            |          Server           |
            |  TLS + TCP Socket         |
            |  Thread per Client        |
            |  Max 50 Clients           |
            +------------+--------------+
                          |
        ------------------------------------------
        |          |            |          |
      Client     Client       Client     Client
        |          |            |          |
    NAME?      NAME?        NAME?      NAME?
    UPDATE     UPDATE       UPDATE      GET
```

---

## Features

* TCP socket communication
* TLS/SSL encrypted client-server communication
* Multi-client concurrency using threads
* Thread-safe leaderboard using locks
* **Client name registration** — server asks each client for a name on connect; all server logs are tagged with that name
* **50-client hard cap** — server sends `SERVER_FULL max=50` and closes the socket for connections beyond the limit; all clients handle this response gracefully
* Client simulation for automated stress testing
* Real-time leaderboard retrieval
* Performance measurement (latency & throughput)
* Error handling for invalid commands, disconnections, and SSL failures
* **GUI dashboards** — full tkinter GUIs for server, client, and stress tester
* **Cross-network support** via ngrok tunneling

---

## Technologies Used

* Python 3.8+
* TCP Socket Programming
* TLS / SSL Encryption (`ssl` module)
* Multithreading (`threading` module)
* Multiprocessing (`multiprocessing` module)
* Tkinter (GUI)
* ngrok (optional, for cross-network demos)

---

## Project Structure

```
SocketProg/
│
├── server.py              # TLS-enabled multi-client server (terminal)
├── server_gui.py          # Server with live GUI dashboard
│
├── client.py              # Automated client — random score updates (terminal)
├── client_man.py          # Manual client — type commands yourself (terminal)
├── client_gui.py          # Client with full GUI (manual + auto modes)
│
├── test_clients.py        # Stress testing script (terminal)
├── stress_test_gui.py     # Stress test with GUI dashboard + latency chart
│
├── leaderboard.py         # Thread-safe leaderboard logic (shared by server files)
│
├── cert.pem               # TLS certificate (generate once, share with clients)
├── key.pem                # TLS private key (server only — never share)
└── README.md
```

---

## Communication Protocol

The system uses a **simple text-based custom protocol** over TLS/TCP.

### 0. Name Registration Handshake (on every new connection)

Immediately after the SSL handshake, the server initiates a name registration exchange:

```
Server → Client:   NAME?
Client → Server:   Alice
```

All subsequent server log entries for that session are tagged with the client's name.

If the server is already at 50 clients, it skips the handshake and instead sends:

```
Server → Client:   SERVER_FULL max=50
```

The client closes the connection immediately on receiving this.

---

### 1. Update Score

```
UPDATE <player_name> <score>
```

Example:

```
UPDATE Alice 10
```

Scores are **cumulative** — each UPDATE adds to the player's existing total.

Server response:

```
Score updated
```

---

### 2. Retrieve Leaderboard

```
GET
```

Example server response:

```
Alice: 35
Bob: 20
Charlie: 15
```

Results are sorted in **descending score order**.

---

### 3. Error Responses

| Situation | Server response |
|---|---|
| Invalid command | `Invalid command` |
| Non-integer score | `Invalid score format` |
| Server at 50-client limit | `SERVER_FULL max=50` |

---

## TLS Certificate Setup

Before running the server for the first time, generate a self-signed TLS certificate:

```bash
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem
```

Press Enter through all prompts. This generates:

```
cert.pem   ← share this with all clients
key.pem    ← keep this on the server only
```

> ⚠️ Both files must be in the same directory as the scripts when you run them.

---

## How to Run

### Same Network (LAN / same WiFi)

All machines must be on the same WiFi. Use the server machine's local IP address (e.g. `10.30.201.35`) in the client HOST field.

### Different Networks (via ngrok)

Install and run ngrok on the server machine before starting the server:

```bash
ngrok tcp 5000
```

ngrok will display a public forwarding address like:

```
Forwarding   tcp://4.tcp.ngrok.io:12345  ->  localhost:5000
```

Give teammates `4.tcp.ngrok.io` as the HOST and `12345` as the PORT.

---

### Step 1 — Server Machine

**Terminal 1** — start ngrok (if cross-network):
```bash
ngrok tcp 5000
```

**Terminal 2** — start the server (choose one):
```bash
python server.py        # terminal version
python server_gui.py    # GUI version (recommended)
```

Expected output:
```
[SERVER STARTED] Listening on 0.0.0.0:5000  (max clients: 50)
```

---

### Step 2 — Client Machines

Each client machine needs: `client_gui.py` (or `client.py` / `client_man.py`) and `cert.pem`.

**GUI client (recommended):**
```bash
python client_gui.py
```
- Set Host and Port to the server's address (local IP or ngrok address)
- Enter your name
- Click **Connect**
- Use **Manual mode** to type commands, or **Auto mode** to fire random updates

**Terminal automated client:**
```bash
python client.py
```

**Terminal manual client:**
```bash
python client_man.py
```

---

### Step 3 — Stress Test

Run on any machine (can be the same as a client):

```bash
python stress_test_gui.py    # GUI version (recommended)
python test_clients.py       # terminal version
```

Set the number of clients (max 50), requests per client, and click **▶ Run Test**.

---

## GUI Overview

### `server_gui.py` — Server Dashboard

| Panel | Contents |
|---|---|
| Left | Host/Port config, Start/Stop buttons, Reset Leaderboard, live connected clients list |
| Centre | Live leaderboard table with 🥇🥈🥉 medals, auto-refreshes every 2 seconds |
| Right | Colour-coded activity log (green = UPDATE, yellow = GET, purple = connect, red = error) |

### `client_gui.py` — Client Dashboard

| Panel | Contents |
|---|---|
| Left | Host/Port/Name fields, Connect/Disconnect, Manual/Auto mode selector |
| Centre | **Manual mode**: UPDATE form + GET button + raw command input. **Auto mode**: sliders for count, delay, score range + progress bar |
| Right | Activity Log tab + Leaderboard tab (populated on GET) |

### `stress_test_gui.py` — Stress Test Dashboard

| Section | Contents |
|---|---|
| Config | Host, Port, client count slider (1–50), requests per client |
| Progress | Live progress bar, completed / errors / elapsed counters |
| Results | Total requests, avg/min/max latency, throughput, error count |
| Chart | Latency distribution histogram drawn on canvas |

---

## Performance Evaluation

Metrics measured by `test_clients.py` and `stress_test_gui.py`:

* Average response latency per request
* Minimum and maximum latency
* Total execution time
* Throughput (requests per second)

Example output:

```
Performance Results
-------------------
Total Clients:    20
Total Requests:   100
Total Time:       2.35 seconds
Average Latency:  19.00 ms
Min Latency:       8.20 ms
Max Latency:      54.10 ms
Throughput:       42.55 requests/second
```

### Observations

* The server successfully handled multiple concurrent connections up to the 50-client cap.
* Thread-based concurrency enabled parallel request processing.
* TLS encryption introduced minimal latency overhead.
* The system remained stable under high client load.
* The 50-client breaking point was enforced correctly — excess connections received `SERVER_FULL` and disconnected without crashing the server.

---

## Fault Tolerance and Error Handling

### Abrupt Client Disconnections

If a client disconnects unexpectedly, the server detects the empty recv and logs the event, then frees the client slot.

```
[DISCONNECTED] 'Alice' (('192.168.1.5', 53421)) session ended  |  active clients: 2
```

### SSL/TLS Handshake Failures

Invalid or non-TLS clients are rejected safely without affecting other connections.

```
[SSL ERROR] Handshake failed from ('192.168.1.5', 53421)
```

### Invalid Commands

```
Invalid command
```

### Server at Capacity

When the 50-client limit is reached, new connections are rejected immediately after the SSL handshake:

```
[LIMIT REACHED] Rejecting ('192.168.1.8', 54210) — already at 50 clients
```

The client receives:
```
SERVER_FULL max=50
```

---

## File Distribution Checklist

| File | Server machine | Client machines |
|---|---|---|
| `server.py` / `server_gui.py` | ✅ | ❌ |
| `leaderboard.py` | ✅ | ❌ |
| `cert.pem` | ✅ | ✅ (required) |
| `key.pem` | ✅ | ❌ (never share) |
| `client.py` / `client_gui.py` | optional | ✅ |
| `client_man.py` | optional | ✅ |
| `test_clients.py` / `stress_test_gui.py` | optional | ✅ |

---

## Key Concepts Demonstrated

* Low-level socket programming
* Secure communication using TLS/SSL
* Custom application-layer protocol with handshake
* Concurrent client handling using threads
* Synchronization using locks (race condition prevention)
* Server-side capacity enforcement and graceful rejection
* Client-server architecture
* Stress testing using multiprocessing
* Performance evaluation (latency, throughput)
* GUI development with tkinter

---

## Future Improvements

* Database-backed persistent leaderboard (SQLite / PostgreSQL)
* Web interface for viewing leaderboard in a browser
* Client authentication with username/password
* Distributed server architecture with load balancing
* Advanced monitoring and logging to file
* Reconnect logic on client side if connection drops

---

## Project Context

Computer Networks Lab
Socket Programming Mini Project
PES University