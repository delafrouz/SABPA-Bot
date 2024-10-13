from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from sabpabot.controllers.pull_request_controller import PullRequestController

MAX_MESSAGE_SIZE = 4096


async def prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    text = input_message[input_message.find('-'):] if '-' in input_message else ''
    group_name = update.message.chat.title or update.message.from_user.username
    sender: str = update.message.from_user.username
    sender = sender if sender.startswith('@') else f'@{sender}'
    result = PullRequestController.get_prs(text, group_name, sender)

    while len(result) > MAX_MESSAGE_SIZE:
        sub_result = result[:MAX_MESSAGE_SIZE].rsplit('\n', 1)[0]
        await update.message.reply_text(sub_result, parse_mode=ParseMode.MARKDOWN)
        result = result[len(sub_result) + 1:]
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
