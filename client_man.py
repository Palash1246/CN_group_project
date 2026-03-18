import socket
import ssl

HOST = '127.0.0.1'
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
        print("Connected to server")

        # Manual input loop
        while True:
            msg = input("Enter command (UPDATE name score / GET / exit): ")

            if msg.lower() == "exit":
                break

            client.send((msg + "\n").encode())

            response = client.recv(4096).decode()
            print("Server:", response.strip())

        # Close connection after exiting loop
        client.close()

    except Exception as e:
        print("Client error:", e)


if __name__ == "__main__":
    run_client()