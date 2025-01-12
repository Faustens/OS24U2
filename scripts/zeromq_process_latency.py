import time
import os
import csv
import argparse
from datetime import datetime
import zmq
import multiprocessing as mp
import sys

# Funktion für den Publisher-Prozess
def publisher(num_iterations, start_event):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:5555")

    # Warte, bis das Event gesetzt wird
    start_event.wait()
    time.sleep(1)

    for i in range(num_iterations):
        # Sende eine Nachricht mit Zeitstempel an den Subscriber
        timestamp = time.perf_counter_ns()
        message = f"{timestamp}"
        socket.send_string(message)
        time.sleep(0.01)  # Leichtes Delay zwischen Nachrichten

# Funktion für den Subscriber-Prozess
def subscriber(num_iterations, latencies, start_event):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:5555")

    # Abonniere alle Nachrichten
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    # Signalisiere, dass der Subscriber bereit ist
    start_event.set()

    for i in range(num_iterations):
        # Empfange Nachrichten vom Publisher
        message = socket.recv_string()
        received_time = time.perf_counter_ns()

        # Berechne die Latenz
        sent_time = int(message)
        latency = (received_time - sent_time)  # Latenz in Millisekunden
        latencies.append(latency)

def measure_latency(num_iterations):
    # Start worker threads
    start_event = mp.Event()
    latencies = mp.Manager().list()

    process1 = mp.Process(target=publisher, args=(num_iterations, start_event))
    process2 = mp.Process(target=subscriber, args=(num_iterations, latencies, start_event))

    process1.start()
    process2.start()

    process1.join()
    process2.join()

    return latencies

# Save results to a CSV file
def save_results_to_csv(results, num_iterations):
    os.makedirs('../results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    filename = f"../results/zeromq_process_latency_{num_iterations}_{timestamp}.csv"

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Iteration", "Latency (ns)"])
        for i, latency in enumerate(results):
            writer.writerow([i + 1, latency])

    print(f"Results saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure spinlock latency between two worker threads.")
    parser.add_argument("num_iterations", type=int, help="Number of iterations for the latency measurement.")
    args = parser.parse_args()

    # Measure latencies
    results = measure_latency(args.num_iterations)

    # Save results
    save_results_to_csv(results, args.num_iterations)
