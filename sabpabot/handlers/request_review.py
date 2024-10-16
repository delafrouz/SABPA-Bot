from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.controllers.pull_request_controller import PullRequestController


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):

    input_message = update.message.text
    owner: str = update.message.from_user.username
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username

    try:
        result = PullRequestController.get_review_response(text, group_name, owner)
    except Exception as e:
        await update.message.reply_text(f'نتونستم درخواست ریویو بدم چون که {e}')
        raise e
    await update.message.reply_text(result)
