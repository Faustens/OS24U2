import time
import os
import csv
import argparse
from datetime import datetime
from threading import Thread
import threading

# Worker thread 1 function
def worker1(semaphore, shared_data, latency_results, start_event, end_event):
    start_event.wait()  # Wait for the signal to start
    for i in range(len(latency_results)):
        semaphore.acquire()
        shared_data[0] = time.perf_counter_ns()  # Record the start time
        shared_data[1] = True  # Indicate that data is ready for worker2
        semaphore.release()

        # Wait for worker2 to respond
        while shared_data[1]:
            pass

        # Record latency
        latency_results[i] = shared_data[2]
        print(f"[INFO] Value \"{shared_data[2]}\"ns saved.")
    end_event.set()

# Worker thread 2 function
def worker2(semaphore, shared_data, end_event):
    while not end_event.is_set():
        semaphore.acquire()
        if shared_data[1]:  # Check if data is ready from worker1
            end_time = time.perf_counter_ns()
            shared_data[2] = end_time - shared_data[0]  # Calculate latency
            shared_data[1] = False  # Reset the flag
        semaphore.release()

def measure_semaphore_latency(num_iterations):
    semaphore = threading.Semaphore()
    shared_data = [0, False, 0]  # [Start time, Flag, Latency]
    latency_results = [None] * num_iterations

    # Start worker threads
    start_event = threading.Event()
    end_event = threading.Event()
    thread1 = Thread(target=worker1, args=(semaphore, shared_data, latency_results, start_event, end_event))
    thread2 = Thread(target=worker2, args=(semaphore, shared_data, end_event))

    thread1.start()
    thread2.start()

    start_event.set()  # Signal threads to start

    thread1.join()
    thread2.join()

    return latency_results

# Save results to a CSV file
def save_results_to_csv(results, num_iterations):
    os.makedirs('../results', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    filename = f"../results/semaphore_latency_{num_iterations}_{timestamp}.csv"

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
    results = measure_semaphore_latency(args.num_iterations)

    # Save results
    save_results_to_csv(results, args.num_iterations)
