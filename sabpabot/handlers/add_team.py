from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.controllers.team_controller import TeamController


async def add_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username
    print(f'group name is {group_name}')
    try:
        results = TeamController.create_teams(text, group_name)
        message_reply = ''
        for (team, members) in results:
            message_reply += (f'تیم {team.name} با این اعضا ساخته شد: ' +
                              '، '.join(member.first_name for member in members)) + '\n'
        await update.message.reply_text(message_reply)

    except Exception as e:
        await update.message.reply_text(f"نتونستم تیم رو بسازم چون که {e}")
        raise e
