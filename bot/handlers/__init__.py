from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
from telegram.ext import Application
from bot.handlers.command_handlers import start, import_wallet, handle_private_key, cancel, WAITING_FOR_PRIVATE_KEY
from bot.handlers.callback_handlers import button_callback_handler, buy, handle_contract_address, sell, handle_token_selection, WAITING_FOR_CONTRACT_ADDRESS, WAITING_FOR_TOKEN_SELECTION
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

def register_handlers(application: Application) -> None:
    # Disable obsolete PTBUserWarning.
    filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

    import_wallet_handler = ConversationHandler(
        entry_points=[CommandHandler("import_wallet", import_wallet), CallbackQueryHandler(import_wallet, pattern='import_wallet')],
        states={
            WAITING_FOR_PRIVATE_KEY: [CallbackQueryHandler(cancel, pattern='cancel'), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_private_key)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='cancel')],
    )

    buy_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy, pattern='buy')],
        states={
            WAITING_FOR_CONTRACT_ADDRESS: [CallbackQueryHandler(cancel, pattern='cancel'), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contract_address)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='cancel')],
    )

    sell_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(sell, pattern='sell')],
        states={
            WAITING_FOR_TOKEN_SELECTION: [CallbackQueryHandler(cancel, pattern='cancel'), CallbackQueryHandler(handle_token_selection)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='cancel')],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(import_wallet_handler)
    application.add_handler(buy_handler)
    application.add_handler(sell_handler)
    application.add_handler(CallbackQueryHandler(button_callback_handler))