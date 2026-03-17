# Secure Multiplayer Leaderboard System

Socket Programming Mini Project

## Overview

This project implements a **secure client–server leaderboard system** using low-level socket programming.

Multiple clients connect to a server simultaneously and update player scores. The server maintains a shared leaderboard and responds to client requests in real time.

The project demonstrates core networking concepts including:

* TCP socket communication
* TLS encrypted communication
* Concurrent client handling
* Custom protocol design
* Performance evaluation under load

---

# System Architecture

The project follows a **Client–Server Architecture**.

* The **server** listens for incoming TLS-secured TCP connections.
* Each client connection is handled in a **separate thread**.
* Clients send commands to update scores or retrieve the leaderboard.
* A shared leaderboard is maintained with **thread-safe access using locks**.

```
             +--------------------+
             |       Server       |
             |  TLS + TCP Socket  |
             |  Thread per Client |
             +----------+---------+
                        |
        ---------------------------------------
        |          |          |          |
      Client     Client     Client     Client
        |          |          |          |
     UPDATE      UPDATE      UPDATE      GET
```

---

# Features

* TCP socket communication
* TLS encrypted client-server communication
* Multi-client concurrency using threads
* Thread-safe leaderboard using locks
* Client simulation for stress testing
* Real-time leaderboard retrieval
* Performance measurement (latency & throughput)
* Error handling for invalid commands and disconnections
* Modular project structure

---

# Technologies Used

* Python
* TCP Socket Programming
* TLS / SSL Encryption
* Multithreading
* Multiprocessing

---

# Project Structure

```
SocketProg/
│
├── server.py          # TLS-enabled multi-client server
├── client.py          # Client program sending score updates
├── test_clients.py    # Stress testing script
├── leaderboard.py     # Thread-safe leaderboard logic
├── cert.pem           # TLS certificate
├── key.pem            # TLS private key
└── README.md
```

---

# Communication Protocol

The system uses a **simple text-based custom protocol**.

## 1. Update Score

```
UPDATE <player_name> <score>
```

Example:

```
UPDATE Alice 10
```

This increases the player's score cumulatively.

Example internal leaderboard update:

```
Alice: 25
Bob: 15
```

---

## 2. Retrieve Leaderboard

```
GET
```

Example server response:

```
Alice: 35
Bob: 20
Charlie: 15
```

Leaderboard results are sorted in **descending score order**.

---

# TLS Certificate Setup

Before running the server, TLS certificates must be generated.

Run the following command:

```
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem
```

This generates:

```
cert.pem
key.pem
```

These files enable **TLS encrypted communication between clients and the server**.

---

# How to Run the Project

## 1. Navigate to the Project Folder

```
cd [name of the folder which contains all the codes]
```

---

## 2. Generate TLS Certificates (first time only)

```
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem
```

---

## 3. Start the Server

```
python server.py
```

Expected output:

```
[SERVER STARTED] 127.0.0.1:5000
```

The server will now listen for client connections.

---

## 4. Run a Single Client

Open another terminal and run:

```
python client.py
```

You should see something like:

```
Connected to server
Server: Score updated
Server: Score updated

Leaderboard:
Palash: 15
Prajna: 10
Shristi: 8
```

---

## 5. Run Stress Test (Multiple Clients)

To simulate concurrent users:

```
python test_clients.py
```

Example:

```
Number of clients: 20
```

This launches multiple clients simultaneously sending update requests.

---

# Performance Evaluation

The system performance was evaluated using the `test_clients.py` script.

Metrics measured:

* Average response latency
* Total execution time
* Throughput (requests per second)

Example output:

```
Performance Results
-------------------
Total Clients: 20
Total Requests: 100
Total Time: 2.35 seconds
Average Latency: 0.019 seconds
Throughput: 42.55 requests/second
```

### Observations

* The server successfully handled multiple concurrent connections.
* Thread-based concurrency enabled parallel request processing.
* TLS encryption introduced minimal latency overhead.
* The system remained stable under high client load.

---

# Fault Tolerance and Error Handling

The system includes several mechanisms to ensure robustness.

### Abrupt Client Disconnections

If a client disconnects unexpectedly, the server detects the closed socket and logs the event.

Example:

```
[DISCONNECTED] ('127.0.0.1', 53421)
```

### SSL/TLS Handshake Failures

Invalid TLS clients are rejected safely.

Example:

```
[SSL ERROR] Handshake failed from ('127.0.0.1', 53421)
```

### Invalid Commands

If a client sends an unsupported command, the server responds with:

```
Invalid command
```

---

# Key Concepts Demonstrated

* Low-level socket programming
* Secure communication using TLS
* Concurrent client handling using threads
* Synchronization using locks
* Client-server architecture
* Stress testing using multiprocessing
* Performance evaluation

---

# Future Improvements

Possible extensions include:

* Database-backed persistent leaderboard
* Web interface for viewing leaderboard
* Client authentication system
* Distributed server architecture
* Advanced monitoring and logging

---

# Project Context

Computer Networks Lab
Socket Programming Mini Project
PES University
