import time
from loguru import logger
from telegram.ext import Application
from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import register_handlers


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN set for the bot")
        raise ValueError("No TELEGRAM_BOT_TOKEN set for the bot")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    register_handlers(application)

    logger.info("Starting the bot")

    while True:
        try:
            application.run_polling()
        except Exception as e:
            logger.exception(f"An error occurred while running the bot: {e}")
            time.sleep(10)


if __name__ == '__main__':
    main()