from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
import re


def round_to_50(number):
    return ((number + 49) // 50) * 50
def screen(text):
    text = str(text)
    markdown_symbols = r'*_~`[]()'
    escaped_symbols = re.escape(markdown_symbols)
    return re.sub(f"([{escaped_symbols}])", r"\\\1", text)

def calc_date(plus):
    current_date = datetime.now()
    new_date1 = current_date + timedelta(days=int(plus[0]))
    new_date2 = current_date + timedelta(days=int(plus[1]))
    return (new_date1.strftime("%d.%m"), new_date2.strftime("%d.%m"))

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

