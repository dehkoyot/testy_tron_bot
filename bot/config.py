import json
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


if not os.path.exists("secret.key"):
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
else:
    with open("secret.key", "rb") as key_file:
        key = key_file.read()

with open('contracts/trc20_abi.json', 'r') as abi_file:
    trc20_abi = json.load(abi_file)

ENCRYPTION_KEY = key
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TRON_API_KEY = os.environ.get("TRON_API_KEY")

SUNPUMP_ROUTER_ADDRESS = "TZFs5ch1R1C4mmjwrrmZqeqbUgGpxY1yWB"
WTRX_CONTRACT_ADDRESS = "TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR"
TRC20_ABI = trc20_abi

AMOUNT_TRX_TO_SPEND = 100_000  # Amount to spend in TRX to buy memcoins
TOKEN_SELL_PERCENTAGE = 0.1  # Sell 10% of token balance
MAX_SLIPPAGE = 0.02  # 2% slippage (same as default on SunPump)
UNLIMITED_AMOUNT_TO_SPEND = 2 ** 256 - 1  # Maximum uint256 value