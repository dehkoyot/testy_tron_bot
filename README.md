# Telegram Tron Bot

This Telegram bot allows users to create Tron wallets, deposit funds, and trade coins on the SunPump Meme platform. The bot also supports a referral system.

## Features
- Create Tron wallet for each user (or import your own wallet)
- Securely store private keys
- Buy/Sell operations on SunPump Meme
- Referral system

## Installation

1. Clone the repository.
2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Create .env file and put your TELEGRAM_BOT_TOKEN there.
4. Register free account at https://www.trongrid.io/ and get your API key. Put it in .env file.
5. Run the bot:
    ```bash
    python main.py
    ```

## Security
Private keys are encrypted using `cryptography.fernet`. The encryption key is stored in `secret.key`.