from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from tronpy.keys import PrivateKey
import tronpy
from bot.wallet.wallet import create_wallet, get_wallet_balance, cipher
from bot.database import get_user_by_id, save_user
from loguru import logger

WAITING_FOR_PRIVATE_KEY = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_id = update.message.from_user.id
        args = context.args

        logger.info(f"User {user_id} started the bot with args: {args}")

        user = get_user_by_id(user_id)

        if user:
            await show_home(update, context, user)
        else:
            if args and args[0].startswith("ref_"):
                ref_code = args[0]
                await update.message.reply_text(f"You were invited by {ref_code}")

            address, encrypted_private_key = create_wallet(user_id)
            referral_code = f"ref_{user_id}"

            save_user(user_id, address, encrypted_private_key, referral_code)

            user = {
                "user_id": user_id,
                "address": address,
                "private_key": encrypted_private_key,
                "referral_code": referral_code
            }

            await update.message.reply_text(
                f"Welcome! Your Tron wallet has been created.\n"
                f"Address: {address}\n"
                f"Share this referral link: https://t.me/testy_tron_bot?start={
                    referral_code}"
            )
            await show_home(update, context, user)

    except Exception as e:
        logger.error(f"Failed to create wallet for user {user_id}: {e}")


async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict = None) -> None:
    try:
        message = ""

        if not user:
            user_id = update.message.from_user.id
            user = get_user_by_id(user_id)
            message = update.message or update.callback_query.message
            await message.reply_text("Create a wallet first by typing /start.")
            return

        try:
            trx_balance, trc20_tokens = await get_wallet_balance(user)

            message = (
                f"🚀 Great news! You're all set and ready to trade. Tap the button below to start trading!\n\n"
                f"💼 Your Portfolio:\n"
                f"🔹TRX: {trx_balance:,.6f}\n"
            )
            message += "\n".join([
                f"🔹{(token.upper())}: {info['amount']:,.6f}" for token, info in trc20_tokens.items()
            ])

            keyboard = [
                [InlineKeyboardButton("Buy", callback_data='buy'), InlineKeyboardButton(
                    "Sell", callback_data='sell')],
                [InlineKeyboardButton(
                    "Import Another Wallet", callback_data='import_wallet')],
                [InlineKeyboardButton("Home", callback_data='home'), InlineKeyboardButton(
                    "Refresh", callback_data='refresh')]
            ]

        except tronpy.exceptions.AddressNotFound:
            address = user['address']
            message = (
                f"Your wallet has been created but is not yet activated on the blockchain.\n"
                f"Please deposit some TRX to your wallet to start trading:\n\n"
                f"{address}\n\n"
                f"⏳ Sometimes it takes a few minutes for the blockchain to recognize the deposit.\n\n"
                f"Learn more about Tron account activation: https://developers.tron.network/docs/account#account-activation"
            )

            keyboard = [
                [InlineKeyboardButton(
                    "I deposited TRX. Check my balance.", callback_data='refresh')],
                [InlineKeyboardButton(
                    "Import Another Wallet", callback_data='import_wallet')],
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        reply = update.message or update.callback_query.message
        await reply.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.exception(f"An unexpected error occurred in show_home: {e}")


async def import_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message or update.callback_query.message
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "Please provide your private key to import your wallet. Be careful, and make sure to keep your key secure.",
        reply_markup=reply_markup
    )
    return WAITING_FOR_PRIVATE_KEY


async def handle_private_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Received private key from user {update.message.from_user.id}")

    user_id = update.message.from_user.id
    private_key_input = update.message.text

    try:
        wallet_key = PrivateKey(bytes.fromhex(private_key_input))
        address = wallet_key.public_key.to_base58check_address()

        encrypted_private_key = cipher.encrypt(
            private_key_input.encode()).decode()

        save_user(user_id, address, encrypted_private_key, referral_code=None)

        logger.info(f"User {user_id} imported a wallet with address {address}")

        await update.message.reply_text(
            f"Your wallet has been successfully imported. Address: {address}"
        )

        user = get_user_by_id(user_id)
        await show_home(update, context, user)

        return ConversationHandler.END

    except ValueError:
        logger.warning(f"User {user_id} provided an invalid private key.")

        keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "The private key you provided is invalid. Please try again or press Cancel to stop the process.",
            reply_markup=reply_markup
        )
        return WAITING_FOR_PRIVATE_KEY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Operation has been canceled.")

    user_id = query.from_user.id
    user = get_user_by_id(user_id)

    await show_home(update, context, user)

    return ConversationHandler.END