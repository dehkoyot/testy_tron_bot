from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from tronpy.keys import is_base58check_address
from loguru import logger
from bot.trading.trading_utils import buy_token, sell_token
from bot.wallet.wallet import get_decrypted_private_key
from bot.database import get_user_by_id
from bot.wallet.wallet import get_wallet_balance
from bot.handlers.command_handlers import show_home, import_wallet, ConversationHandler

WAITING_FOR_CONTRACT_ADDRESS = 2
WAITING_FOR_TOKEN_SELECTION = 3


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        user = get_user_by_id(user_id)

        if query.data == 'buy':
            await buy(update, context)
        elif query.data == 'sell':
            await sell(update, context)
        elif query.data == 'import_wallet':
            await import_wallet(update, context)
        elif query.data in ['home', 'refresh']:
            await show_home(update, context, user)

    except Exception as e:
        logger.exception(f"An error occurred in button_callback_handler: {e}")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message or update.callback_query.message

    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "I will buy some tokens for you for 0.1 TRX. Please provide the contract address of the token you want to buy:",
        reply_markup=reply_markup
    )
    return WAITING_FOR_CONTRACT_ADDRESS


async def handle_contract_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user = get_user_by_id(user_id)

    contract_address = update.message.text

    if not is_base58check_address(contract_address):
        logger.warning(f"User {user_id} provided an invalid contract address.")
        keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "The contract address you provided is invalid. Please try again or press Cancel to stop the process.",
            reply_markup=reply_markup
        )
        return WAITING_FOR_CONTRACT_ADDRESS

    context.user_data['contract_address'] = contract_address

    private_key = get_decrypted_private_key(user['private_key'])
    user_address = user['address']

    success = buy_token(contract_address, user_address, private_key)

    if success:
        await update.message.reply_text("✅ Successfully purchased tokens!")
    else:
        await update.message.reply_text("❌ Failed to purchase tokens.")

    await show_home(update, context, user)
    return ConversationHandler.END


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message or update.callback_query.message

    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    user = get_user_by_id(user_id)

    _, trc20_balance = await get_wallet_balance(user)

    buttons = [ 
        [InlineKeyboardButton(f"{token.upper()}: {info['amount']}", callback_data=f"{token}:{info['contract_address']}")]
        for token, info in trc20_balance.items()
    ]
    buttons.append([InlineKeyboardButton("Cancel", callback_data='cancel')])

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(
        "Select a token to sell:",
        reply_markup=reply_markup
    )

    return WAITING_FOR_TOKEN_SELECTION


async def handle_token_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data.split(':')
    token_symbol = data[0]
    contract_address = data[1]

    user_id = query.from_user.id
    user = get_user_by_id(user_id)

    private_key = get_decrypted_private_key(user['private_key'])
    user_address = user['address']

    success = sell_token(contract_address, user_address, private_key)

    if success:
        await query.message.reply_text(f"✅ Successfully sold 10% of {token_symbol.upper()} tokens!")
    else:
        await query.message.reply_text(f"❌ Failed to sell {token_symbol.upper()} tokens.")

    await show_home(update, context, user)
    return ConversationHandler.END