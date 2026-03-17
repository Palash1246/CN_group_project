import socket
import random
import time
import ssl

HOST = '127.0.0.1'
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

        print("Connected to server")

        for _ in range(5):

            player = random.choice(players)
            score = random.randint(1, 10)

            message = f"UPDATE {player} {score}\n"

            client.send(message.encode())

            response = client.recv(1024).decode()
            print("Server:", response.strip())

            time.sleep(random.uniform(0.3, 1))

        # request leaderboard
        client.send("GET\n".encode())

        response = client.recv(4096).decode()

        print("\nLeaderboard:\n", response)

        client.close()

    except Exception as e:
        print("Client error:", e)


if __name__ == "__main__":
    run_client()