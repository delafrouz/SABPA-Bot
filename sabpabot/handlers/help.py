from telegram import Update
from telegram.ext import ContextTypes


async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from sabpabot.constants import HELP_COMMAND_MESSAGE
    await update.message.reply_text(HELP_COMMAND_MESSAGE)
