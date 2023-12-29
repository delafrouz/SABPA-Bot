from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.controllers.team_controller import TeamController


async def get_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    input_message = update.message.text
    flags_start = input_message.find('-')
    text = input_message[flags_start:] if flags_start >= 0 else ''
    try:
        response = TeamController.get_teams_response(text, group_name)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f'نتونستم اطلاعات بدم چون که {e}')
        raise e
