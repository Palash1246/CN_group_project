import socket
import threading
import ssl
from leaderboard import update_score, get_leaderboard

HOST = '0.0.0.0'
PORT = 5000

MAX_CLIENTS = 50                          # hard cap on simultaneous connections
_client_count = 0                         # current connected client count
_count_lock   = threading.Lock()          # protects _client_count


def handle_client(conn, addr):
    # ------------------------------------------------------------------ #
    #  SSL connection established – ask the client to identify itself     #
    # ------------------------------------------------------------------ #
    print(f"\n[SSL CONNECTED] Secure connection established with {addr}")

    client_name = "Unknown"

    try:
        # 1. Prompt the client for their name
        conn.send("NAME?\n".encode())

        name_data = conn.recv(1024).decode().strip()
        if name_data:
            client_name = name_data

        print(f"[CLIENT IDENTIFIED] '{client_name}' connected from {addr}")

        # ------------------------------------------------------------------ #
        #  Main command loop                                                   #
        # ------------------------------------------------------------------ #
        while True:
            data = conn.recv(1024)

            if not data:
                print(f"[DISCONNECTED] '{client_name}' ({addr}) closed the connection abruptly")
                break

            data = data.decode()
            message = data.strip().split()

            if len(message) == 0:
                continue

            command = message[0]

            if command == "UPDATE" and len(message) == 3:
                player = message[1]

                try:
                    score = int(message[2])
                except ValueError:
                    conn.send("Invalid score format\n".encode())
                    continue

                new_total = update_score(player, score)
                print(f"[UPDATE] '{client_name}' ({addr}) → player '{player}' +{score}  (total: {new_total})")
                conn.send("Score updated\n".encode())

            elif command == "GET":
                print(f"[GET]    '{client_name}' ({addr}) requested the leaderboard")
                board = get_leaderboard()
                result = "\n".join([f"{player}: {score}" for player, score in board])
                conn.send((result + "\n").encode())

            else:
                print(f"[INVALID] '{client_name}' ({addr}) sent unknown command: {message}")
                conn.send("Invalid command\n".encode())

    except Exception as e:
        print(f"[ERROR] '{client_name}' ({addr}): {e}")

    finally:
        conn.close()
        with _count_lock:
            global _client_count
            _client_count -= 1
        print(f"[DISCONNECTED] '{client_name}' ({addr}) session ended  |  active clients: {_client_count}")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # TLS / SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER STARTED] Listening on {HOST}:{PORT}  (max clients: {MAX_CLIENTS})")

    while True:
        conn, addr = server.accept()

        try:
            conn = context.wrap_socket(conn, server_side=True)

        except ssl.SSLError as e:
            print(f"[SSL ERROR] Handshake failed from {addr}: {e}")
            conn.close()
            continue

        # ── breaking point: reject if at capacity ─────────────────────────
        with _count_lock:
            global _client_count
            if _client_count >= MAX_CLIENTS:
                print(f"[LIMIT REACHED] Rejecting {addr} — already at {MAX_CLIENTS} clients")
                try:
                    conn.send(f"SERVER_FULL max={MAX_CLIENTS}\n".encode())
                except Exception:
                    pass
                conn.close()
                continue
            _client_count += 1
            print(f"[ACCEPTED] {addr}  |  active clients: {_client_count}/{MAX_CLIENTS}")
        # ──────────────────────────────────────────────────────────────────

        client_thread = threading.Thread(
            target=handle_client,
            args=(conn, addr)
        )

        client_thread.daemon = True
        client_thread.start()


if __name__ == "__main__":
    start_server()
