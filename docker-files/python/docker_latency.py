import argparse
import time
import csv
import socket
from datetime import datetime

# Worker-Funktion für den parent_worker
def parent_worker(host, port, num_iterations):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"Parent worker listening on {host}:{port}")

    conn, addr = server.accept()
    print(f"Connection established with {addr}")

    time.sleep(1)

    for _ in range(num_iterations):
        timestamp_ns = time.perf_counter_ns()
        conn.send(str(timestamp_ns).encode())
        time.sleep(0.1)

    conn.close()
    server.close()

# Worker-Funktion für den child_worker
def child_worker(host, port, num_iterations):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"Child worker connected to {host}:{port}")

    latencies = []
    i=0

    while i < num_iterations:
        inmsg = client.recv(1024).decode()
        if inmsg == '': pass
        timestamp_sent = int(inmsg)
        timestamp_received = time.perf_counter_ns()
        latency = timestamp_received - timestamp_sent
        latencies.append(latency)
        i = i+1

    client.close()

    # Ergebnisse in eine CSV-Datei schreiben
    timestamp = datetime.now()
    filename = f"../results/docker_latencies_{num_iterations}_{timestamp.strftime('%Y%m%d%H%M')}.csv"

    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Iteration", "Latency (ns)"])
        for i, latency in enumerate(latencies):
            csv_writer.writerow([i + 1, latency])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure latency between two processes in different Docker containers.")
    parser.add_argument("type", choices=["parent", "child"], help="Specify the worker type: parent or child.")
    parser.add_argument("host", type=str, help="The host IP address for the socket connection.")
    parser.add_argument("port", type=int, help="The port number for the socket connection.")
    parser.add_argument("num_iterations", type=int, help="Number of latency measurements.")

    args = parser.parse_args()

    if args.type == "parent":
        parent_worker(args.host, args.port, args.num_iterations)
    elif args.type == "child":
        child_worker(args.host, args.port, args.num_iterations)
