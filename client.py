import socket
import random
import time
import ssl

HOST = '10.30.201.35'
PORT = 5000

players = ["Palash", "Prajna", "Shristi", "Ojas", "Ojas2"]


def run_client():

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = context.wrap_socket(sock, server_hostname=HOST)
        client.connect((HOST, PORT))

        print("[SSL CONNECTED] Secure connection established with server")

        # ------------------------------------------------------------------ #
        #  Name registration handshake                                        #
        # ------------------------------------------------------------------ #
        prompt = client.recv(1024).decode().strip()   # receives "NAME?" or "SERVER_FULL"

        # ── breaking point: server at capacity ────────────────────────────
        if prompt.startswith("SERVER_FULL"):
            limit = prompt.split("=")[-1] if "=" in prompt else "50"
            print(f"[REJECTED] Server is full (max {limit} clients). Try again later.")
            client.close()
            return
        # ─────────────────────────────────────────────────────────────────

        if prompt == "NAME?":
            client_name = input("Enter your client name: ").strip()
            if not client_name:
                client_name = "AutoClient"
            client.send((client_name + "\n").encode())
            print(f"[REGISTERED] Connected as '{client_name}'")

        # ------------------------------------------------------------------ #
        #  Send 5 random score updates                                        #
        # ------------------------------------------------------------------ #
        for _ in range(5):

            player = random.choice(players)
            score = random.randint(1, 10)

            message = f"UPDATE {player} {score}\n"
            print(f"Sending: {message.strip()}")

            client.send(message.encode())

            response = client.recv(1024).decode()
            print("Server:", response.strip())

            time.sleep(random.uniform(0.3, 1))

        # ------------------------------------------------------------------ #
        #  Request leaderboard                                                #
        # ------------------------------------------------------------------ #
        client.send("GET\n".encode())

        response = client.recv(4096).decode()
        print("\nLeaderboard:\n", response)

        client.close()

    except Exception as e:
        print("Client error:", e)


if __name__ == "__main__":
    run_client()
