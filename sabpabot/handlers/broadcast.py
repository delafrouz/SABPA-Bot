from telegram import Update
from telegram.ext import ContextTypes


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from sabpabot.controllers.broadcast_controller import BroadcastController

    input_message = update.message.text
    messenger: str = update.message.from_user.username
    messenger = messenger if messenger.startswith('@') else f'@{messenger}'
    text = input_message[input_message.find('-'):] if '-' in input_message else input_message[input_message.find(' '):]

    if messenger == '@DelafrouzMir':
        result = BroadcastController.broadcast(text)
        await update.message.reply_text(result)
