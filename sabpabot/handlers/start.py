from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from sabpabot.constants import START_COMMAND_MESSAGE
    await update.message.reply_text(START_COMMAND_MESSAGE)
