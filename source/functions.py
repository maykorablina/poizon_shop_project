from dotenv import load_dotenv
import os
import json

def update_yuan_rate(new_rate):
    try:
        with open('.env', "r", encoding="utf-8") as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith("YUAN_RATE="):
                lines[i] = f"YUAN_RATE={new_rate}\n"
                break
        with open('.env', "w", encoding="utf-8") as file:
            file.writelines(lines)
        print(f"YUAN_RATE is updated to {new_rate}")
    except Exception as e:
        print(f"Error while updating YUAN_RATE: {e}")

def load_tariffs():
    with open("source/tariffs.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        return data

def save_tariffs(data):
    with open("source/tariffs.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)