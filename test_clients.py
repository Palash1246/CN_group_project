import multiprocessing
import time
import socket
import ssl
import random

HOST = "127.0.0.1"
PORT = 5000

players = ["Alice", "Bob", "Charlie", "David", "Eva"]
REQUESTS_PER_CLIENT = 5


def run_client(client_id, results):

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client = context.wrap_socket(sock, server_hostname=HOST)

    try:
        client.connect((HOST, PORT))

        for _ in range(REQUESTS_PER_CLIENT):

            player = random.choice(players)
            score = random.randint(1, 10)

            msg = f"UPDATE {player} {score}\n"

            start = time.time()

            client.send(msg.encode())
            client.recv(1024)

            end = time.time()

            results.append(end - start)

    except Exception as e:
        print(f"Client {client_id} error:", e)

    finally:
        client.close()


if __name__ == "__main__":

    NUMBER_OF_CLIENTS = int(input("Number of clients: "))

    manager = multiprocessing.Manager()
    results = manager.list()

    processes = []

    start_time = time.time()

    for i in range(NUMBER_OF_CLIENTS):

        p = multiprocessing.Process(
            target=run_client,
            args=(i, results)
        )

        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    end_time = time.time()

    total_requests = NUMBER_OF_CLIENTS * REQUESTS_PER_CLIENT
    total_time = end_time - start_time

    avg_latency = sum(results) / len(results)
    throughput = total_requests / total_time

    print("\nPerformance Results")
    print("-------------------")
    print(f"Total Clients: {NUMBER_OF_CLIENTS}")
    print(f"Total Requests: {total_requests}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Throughput: {throughput:.2f} requests/second")