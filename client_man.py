import socket
import ssl

HOST = '10.30.201.35'
PORT = 5000


def run_client():
    try:
        # Create TLS context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Create socket and wrap with TLS
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
                client_name = "ManualClient"
            client.send((client_name + "\n").encode())
            print(f"[REGISTERED] Connected as '{client_name}'")

        # ------------------------------------------------------------------ #
        #  Manual command loop                                                #
        # ------------------------------------------------------------------ #
        while True:
            msg = input("\nEnter command (UPDATE <name> <score> / GET / exit): ").strip()

            if msg.lower() == "exit":
                break

            client.send((msg + "\n").encode())

            response = client.recv(4096).decode()
            print("Server:", response.strip())

        # Close connection after exiting loop
        client.close()
        print("[DISCONNECTED] Connection closed.")

    except Exception as e:
        print("Client error:", e)


if __name__ == "__main__":
    run_client()
