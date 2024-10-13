from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from sabpabot.controllers.pull_request_controller import PullRequestController


async def prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    text = input_message[input_message.find('-'):] if '-' in input_message else ''
    group_name = update.message.chat.title or update.message.from_user.username
    sender: str = update.message.from_user.username
    sender = sender if sender.startswith('@') else f'@{sender}'
    result = PullRequestController.get_prs(text, group_name, sender)

    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
