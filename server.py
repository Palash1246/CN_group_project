import socket
import threading
import ssl
from leaderboard import update_score, get_leaderboard

HOST = '0.0.0.0'
PORT = 5000


def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")

    try:
        while True:
            data = conn.recv(1024)

            if not data:
                print(f"[DISCONNECTED] {addr} closed the connection abruptly")
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

                update_score(player, score)
                conn.send("Score updated\n".encode())

            elif command == "GET":
                board = get_leaderboard()
                result = "\n".join([f"{player}: {score}" for player, score in board])
                conn.send((result + "\n").encode())

            else:
                conn.send("Invalid command\n".encode())

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")

    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr}")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # TLS / SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER STARTED] {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()

        try:
            conn = context.wrap_socket(conn, server_side=True)

        except ssl.SSLError as e:
            print(f"[SSL ERROR] Handshake failed from {addr}: {e}")
            conn.close()
            continue

        client_thread = threading.Thread(
            target=handle_client,
            args=(conn, addr)
        )

        client_thread.daemon = True
        client_thread.start()


if __name__ == "__main__":
    start_server()