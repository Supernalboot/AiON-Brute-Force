import requests
import time
import json
import os
from filelock import FileLock
import threading
from tqdm import tqdm

def bungieAPICall(input_value):
    """Send a POST request with the given input_value and return the parsed response.
    If rate limited (429), wait and retry the same value."""
    try:
        response = requests.post(
            "https://qu4n7um-7ime-7unne7-4aa2.bungie.workers.dev/",
            headers={
                "Content-Type": "application/json",
                "X-Time-Badge": "timeTunnel346591457"
            },
            json={"input": input_value}
        )
        if response.status_code == 429:
            print(f"Rate limited on input {input_value}! Waiting 5 minutes before retrying...")
            for remaining in range(300, 0, -1):
                print(f"\rRetrying in {remaining} seconds...", end='', flush=True)
                time.sleep(1)
            print("\rRetrying now!                      ")
            return bungieAPICall(input_value)  # Retry the same value
        
        try:
            data = response.json()
            if isinstance(data, dict) and data.get("correct") is True:
                messages = data.get("messages", [])
                value = "CORRECT"
            else:
                messages =data.get("messages", [])
                value = "INCORRECT INPUT"
        except ValueError:
            messages = data.get("messages", [])
            value = "INCORRECT INPUT"
        return {"VALUE": value, "MESSAGE": messages}
    except Exception as e:
        return {"VALUE": str(e), "MESSAGE": []}

# Make sure the file is unlocked for loading (used for multithreading)
def safe_load_json(filepath):
    lock = FileLock(filepath.replace(":", "_") + ".lock")
    with lock:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except Exception as e:
                    print(f"\nFATAL: Error loading {filepath}: {e}")
                    print("The JSON file may be corrupted. Please fix or restore the file and restart the script.")
                    exit(1)  # Halt the script on load error
        else:
            return {}

# Make sure the file is unlocked for saving (used for multithreading)
def safe_save_json(filepath, data):
    lock = FileLock(filepath.replace(":", "_") + ".lock")
    with lock:
        # Sort by key length, then lexicographically
        sorted_data = dict(sorted(data.items(), key=lambda x: (len(x[0]), x[0])))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, indent=2)

# some magic my brain conjured to make the incrementing work for the input
def special_input_generator():
    """Yield all possible numbers with leading zeros, from 1 to 9 digits, in the required order."""
    for i in range(1, 10):
        yield str(i)
    for length in range(2, 10):
        for i in range(0, 10**length):
            val = str(i).zfill(length)
            yield val

def count_total_inputs():
    """Count total number of possible inputs for tqdm progress bar."""
    total = 0
    for length in range(1, 10):
        total += 10**length
    return total

# Main function for single-threaded operation
def single_thread_worker(delay_seconds=4, output_file="AiONdatabase.json"):
    results = safe_load_json(output_file)

    print("Starting special input generator loop (single thread)...")
    total = count_total_inputs()

    with tqdm(total=total, desc="Progress", unit="codes") as pbar:
        for input_value in special_input_generator():
            if input_value in results:
                pbar.update(1)
                continue
            print(f"Calling API for: {input_value}")
            result = bungieAPICall(input_value)
            results[input_value] = result

            messages = result.get("MESSAGE", [])
            if messages:
                display_message = "\n".join(m.replace('\xa0', '\n') for m in messages)
                tqdm.write(f"Input: {input_value} | VALUE: {result['VALUE']}\nMessages:\n{display_message}")
            else:
                tqdm.write(f"Input: {input_value} | VALUE: {result['VALUE']}")

            safe_save_json(output_file, results)
            pbar.update(1)
            # Check for KeyboardInterrupt during sleep
            try:
                for _ in range(int(delay_seconds * 10)):
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nExiting single thread worker...")
                break

# Main function for multithreading
def multi_thread_worker(thread_id, num_threads, delay_seconds, output_file, status_dict, stop_event):
    total = count_total_inputs() // num_threads
    processed = 0
    with tqdm(total=total, desc=f"Thread {thread_id} (approx)", position=thread_id, unit="codes") as pbar:
        while not stop_event.is_set():
            results = safe_load_json(output_file)
            for input_value in special_input_generator():
                if stop_event.is_set():
                    break
                try:
                    if (int(input_value) % num_threads) != thread_id:
                        continue
                except ValueError:
                    continue
                if input_value in results:
                    pbar.update(1)
                    continue
                print(f"[Thread {thread_id}] Calling API for: {input_value}")
                result = bungieAPICall(input_value)
                if stop_event.is_set():
                    break
                results[input_value] = result

                messages = result.get("MESSAGE", [])
                if messages:
                    display_message = "\n".join(m.replace('\xa0', '\n') for m in messages)
                    tqdm.write(f"[Thread {thread_id}] Input: {input_value} | VALUE: {result['VALUE']}\nMessages:\n{display_message}")
                else:
                    tqdm.write(f"[Thread {thread_id}] Input: {input_value} | VALUE: {result['VALUE']}")

                safe_save_json(output_file, results)
                processed += 1
                status_dict[thread_id] = f"{input_value} ({processed} processed)"
                pbar.update(1)
                # Check for stop_event during sleep
                for _ in range(int(delay_seconds * 10)):
                    if stop_event.is_set():
                        break
                    time.sleep(0.1)
                if stop_event.is_set():
                    break

def status_board(status_dict, num_threads, stop_event):
    while not stop_event.is_set():
        print("\n=== STATUS BOARD ===")
        for i in range(num_threads):
            print(f"Thread {i}: {status_dict.get(i, 'Starting...')}")
        print("====================\n")
        time.sleep(10)

if __name__ == "__main__":
    print("Select mode:")
    print("1. Single Thread")
    print("2. Multi Thread")
    mode = input("Enter 1 or 2: ").strip()

    if mode == "1":
        delay_input = input("Delay between requests (seconds, default 4): ").strip()
        delay = float(delay_input) if delay_input else 4
        single_thread_worker(delay_seconds=delay, output_file="AiONdatabase.json")
    elif mode == "2":
        num_threads = int(input("Number of threads: ").strip())
        delay_input = input("Delay between requests (seconds, default 4): ").strip()
        delay = float(delay_input) if delay_input else 4
        threads = []
        status_dict = {}
        stop_event = threading.Event()
        for i in range(num_threads):
            t = threading.Thread(target=multi_thread_worker, args=(i, num_threads, delay, "AiONdatabase.json", status_dict, stop_event))
            threads.append(t)
            t.start()
        try:
            status_board(status_dict, num_threads, stop_event)
        except KeyboardInterrupt:
            print("Exiting status board and stopping threads...")
            stop_event.set()
        for t in threads:
            t.join()
    else:
        print("Invalid selection.")
