# usage_tracker.py
import json
import os
from datetime import datetime

USAGE_FILE = 'usage.json'
MONTHLY_LIMIT = 1000

def load_usage():
    if not os.path.exists(USAGE_FILE):
        reset_usage()
    with open(USAGE_FILE, 'r') as f:
        return json.load(f)

def save_usage(data):
    with open(USAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def reset_usage():
    current_month = datetime.now().strftime("%Y-%m")
    data = {
        "month": current_month,
        "count": 0
    }
    save_usage(data)

def get_usage():
    data = load_usage()
    current_month = datetime.now().strftime("%Y-%m")

    if data['month'] != current_month:
        reset_usage()
        return {"month": current_month, "count": 0}

    return data

def increment_usage():
    data = get_usage()
    data['count'] += 1
    save_usage(data)
    return data['count']

def is_limit_reached():
    data = get_usage()
    return data['count'] >= MONTHLY_LIMIT