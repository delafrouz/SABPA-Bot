from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.controllers.get_team import get_team_by_name
from sabpabot.data_models.team import Team


async def get_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    print(f'group name is {group_name}')
    teams = Team.get_all_teams(group_name)
    if not teams:
        await update.message.reply_text('در حال حاضر هیچ تیمی ساخته نشده است.')
        return
    await update.message.reply_text(
        'لیست تیم‌های گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
        '\n- '.join(f'گروه {team.name} از نوع {team.team_type}' for team in teams))


async def get_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    text = input_message[input_message.find('-'):]
    group_name = update.message.chat.title or update.message.from_user.username
    try:
        team = get_team_by_name(text, group_name)
        print(f'team is {team}')
        await update.message.reply_text(team)
    except Exception as e:
        await update.message.reply_text(f"نتونستم تیم رو پیدا کنم چون که {e}")
        raise e
