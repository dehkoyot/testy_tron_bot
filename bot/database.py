import json
import os
from loguru import logger

DATA_FILE = "user_data.json"


def ensure_data_file_exists():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        logger.info(f"Created new {DATA_FILE} file.")


def load_user_data():
    ensure_data_file_exists()
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_user_data(user_data):
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)


def get_user_by_id(user_id):
    user_data = load_user_data()
    return user_data.get(str(user_id))


def save_user(user_id, address, encrypted_private_key, referral_code):
    user_data = load_user_data()

    user_data[str(user_id)] = {
        "address": address,
        "private_key": encrypted_private_key,
        "referral_code": referral_code or user_data.get(str(user_id), {}).get("referral_code")
    }

    save_user_data(user_data)
    logger.info(f"Saved or updated wallet for user {user_id} in {DATA_FILE}.")
