# CN_group_project


# Secure Multiplayer Leaderboard System

**Socket Programming Mini Project**

## Overview

This project implements a **secure client–server leaderboard system** using low-level socket programming.
Multiple clients connect to a server and update player scores concurrently.
The server maintains a shared leaderboard and responds to client requests in real time.

The system demonstrates key networking concepts including **TCP communication, TLS encryption, concurrency handling, protocol design, and performance testing with multiple clients**.

---

# System Architecture

The project follows a **Client–Server Architecture**.

* The **server** listens for incoming TLS-secured TCP connections.
* Each client connection is handled in a **separate thread** to support concurrency.
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
* TLS-encrypted client–server communication
* Multi-client concurrency using threads
* Thread-safe shared leaderboard using locks
* Client simulation for stress testing
* Real-time leaderboard retrieval
* Error handling for invalid commands
* Modular project structure

---

# Technologies Used

* **Python**
* **TCP Socket Programming**
* **TLS / SSL Encryption**
* **Multithreading**
* **Multiprocessing**

---

# Project Structure

```
SocketProg/
│
├── server.py          # TLS-enabled multi-client server
├── client.py          # Client program that sends score updates
├── test_clients.py    # Stress test script to simulate many clients
├── leaderboard.py     # Thread-safe leaderboard logic
├── cert.pem           # TLS certificate
├── key.pem            # TLS private key
└── README.md
```

---

# Communication Protocol

Clients communicate with the server using simple text commands.

### Update Player Score

```
UPDATE <player_name> <score>
```

Example:

```
UPDATE Alice 10
```

This increases Alice's score by 10.

---

### Get Leaderboard

```
GET
```

Example response:

```
Alice: 25
Bob: 20
Charlie: 15
```

Leaderboard is sorted in **descending order of score**.

---

# How to Run the Project

## 1. Navigate to Project Folder

```
cd SocketProg
```

---

## 2. Generate TLS Certificate (first time only)

```
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem
```

This generates the TLS certificate used by the server.

---

## 3. Start the Server

```
python server.py
```

Expected output:

```
[SERVER STARTED] 127.0.0.1:5000
```

The server now waits for incoming client connections.

---

## 4. Run a Single Client

Open another terminal and run:

```
python client.py
```

Example output:

```
Connected to server
Server: Score updated
Server: Score updated

Leaderboard:
Alice: 20
Bob: 15
Charlie: 10
```

---

## 5. Run Stress Test (Multiple Clients)

To simulate multiple concurrent users:

```
python test_clients.py
```

Example:

```
Number of clients: 20
Starting Client 0
Starting Client 1
Starting Client 2
```

This launches multiple clients simultaneously to test system scalability.

---

# Performance Evaluation

The system can be tested under different loads by increasing the number of simulated clients.

Example tests:

| Clients | Observation                 |
| ------- | --------------------------- |
| 1       | Instant response            |
| 10      | Minor latency               |
| 50      | Higher CPU usage but stable |

Metrics considered:

* Response time
* Throughput
* Server stability
* Concurrent client handling

---

# Key Concepts Demonstrated

* Low-level socket programming
* Secure communication using TLS
* Concurrent client handling using threads
* Synchronization using locks
* Client-server architecture
* Stress testing with multiple processes

---

# Future Improvements

Possible extensions include:

* Persistent storage using a database
* Web interface for leaderboard display
* Authentication for clients
* Distributed leaderboard servers
* Advanced performance monitoring



Socket Programming Mini Project
