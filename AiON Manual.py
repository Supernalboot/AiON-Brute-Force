import requests
import json
import os
import time  # For sleep

def manual_api_test(input_value, output_file="AiONdatabase.json"):

    if len(input_value) > 9:
        print("Input value is too long! Please enter a value with 9 or fewer characters.")
        return
    
    """Send a POST request with the given input_value, save and print the parsed response."""
    badge = "timeTunnel346591457"
    try:
        response = requests.post(
            "https://qu4n7um-7ime-7unne7-4aa2.bungie.workers.dev/",
            headers={
                "Content-Type": "application/json",
                "X-Time-Badge": badge
            },
            json={"input": input_value}
        )
        if response.status_code == 429:
            print(f"Rate limited on input {input_value}! Waiting 60 seconds before retrying...")
            for remaining in range(60, 0, -1):
                print(f"\rRetrying in {remaining} seconds...", end='', flush=True)
                time.sleep(1)
            print("\rRetrying now!                      ")
            return manual_api_test(input_value, output_file)  # Retry the same value

        try:
            data = response.json()
            if isinstance(data, dict) and data.get("correct") is True:
                messages = data.get("messages", [])
                value = "CORRECT"
            else:
                messages = []
                value = "INCORRECT INPUT"
        except ValueError:
            messages = []
            value = "INCORRECT INPUT"

        # Print the result messages to the console
        if messages:
            display_message = "\n".join(m.replace('\xa0', '\n') for m in messages)
            print(f"Input: {input_value} | VALUE: {value}\nMessages:\n{display_message}")
        else:
            print(f"Input: {input_value} | VALUE: {value}")

        # Load or create the output file
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    results = json.load(f)
            except Exception as e:
                print(f"Error loading {output_file}: {e}")
                results = {}
        else:
            results = {}

        # Save/update the result (no zero padding)
        key = str(input_value)
        results[key] = {"VALUE": value, "MESSAGE": messages}
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Saved result for {key} to {output_file}")

    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    output_file = "AiONdatabase.json"
    # Load results once for checking
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception as e:
            print(f"Error loading {output_file}: {e}")
            results = {}
    else:
        results = {}

    print("Manual API Test Mode (type 'exit' to quit)")
    while True:
        input_value = input("Enter the value to use for 'input': ").strip()
        if input_value.lower() == "exit":
            break
        key = str(input_value)
        if key in results:
            saved_value = results[key]["VALUE"]
            saved_messages = results[key]["MESSAGE"]
            if saved_messages:
                display_message = "\n".join(m.replace('\xa0', '\n') for m in saved_messages)
                print(f"Saved result for {key} | VALUE: {saved_value}\nMessages:\n{display_message}")
            else:
                print(f"Saved result for {key} | VALUE: {saved_value}")
            continue  # Skip the API call if result is already saved

        manual_api_test(input_value, output_file)
        # Reload results after writing to file
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    results = json.load(f)
            except Exception as e:
                print(f"Error loading {output_file}: {e}")
                results = {}