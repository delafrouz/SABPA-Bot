from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.controllers.accept_review import accept_review


async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    accepter: str = update.message.from_user.username
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username

    try:
        result = accept_review(accepter, group_name, text)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f'این درخواست ریویو رو نتونستم از طرفت قبول کنم چون که {e}')
        raise e