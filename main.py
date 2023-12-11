import os

from telegram import Update  #upm package(python-telegram-bot)
from telegram.ext import Application, Updater, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes  #upm package(python-telegram-bot)

from sabpabot.constants import START_COMMAND_MESSAGE, HELP_COMMAND_MESSAGE
from sabpabot.controllers.add_team import create_teams
from sabpabot.controllers.request_review import create_request_response
from sabpabot.controllers.get_team import get_team_by_name
from sabpabot.controllers.accept_review import accept_review
from sabpabot.controllers.finish_review import finish_review
from sabpabot.data_models.pull_request import PullRequest
from sabpabot.data_models.team import Team
from sabpabot.data_models.user import User

TOKEN = os.getenv('SATPA_BOT_TOKEN')
BOT_USERNAME = os.getenv('SATPA_BOT_USERNAME')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_COMMAND_MESSAGE)


async def add_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username
    print(f'group name is {group_name}')
    try:
        results = await create_teams(text, group_name)
        message_reply = ''
        for (team, members) in results:
            message_reply += (f'تیم {team.name} با این اعضا ساخته شد: ' +
                              '، '.join(member.first_name for member in members)) + '\n'
        await update.message.reply_text(message_reply)

    except Exception as e:
        await update.message.reply_text(f"نتونستم تیم رو بسازم چون که {e}")
        raise e


async def get_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    text = input_message[input.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username
    try:
        team = await get_team_by_name(text, group_name)
        print(f'team is {team}')
        await update.message.reply_text(team)
    except Exception as e:
        await update.message.reply_text(f"نتونستم تیم رو پیدا کنم چون که {e}")
        raise e


async def get_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    print(f'group name is {group_name}')
    teams = await Team.get_all_teams(group_name)
    if not teams:
        await update.message.reply_text('در حال حاضر هیچ تیمی ساخته نشده است.')
        return
    await update.message.reply_text(
        'لیست تیم‌های گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
        '\n- '.join(f'گروه {team.name} از نوع {team.team_type}' for team in teams))


async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    owner: str = update.message.from_user.username
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username

    try:
        result = await create_request_response(text, group_name, owner)
    except Exception as e:
        await update.message.reply_text(f'نتونستم درخواست ریویو بدم چون که {e}')
        raise e
    await update.message.reply_text(result)


async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    accepter: str = update.message.from_user.username
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username

    try:
        result = await accept_review(accepter, group_name, text)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f'این درخواست ریویو رو نتونستم از طرفت قبول کنم چون که {e}')
        raise e


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_message = update.message.text
    finisher: str = update.message.from_user.username
    text = input_message[input_message.find('-'):]

    group_name = update.message.chat.title or update.message.from_user.username

    try:
        result = await finish_review(finisher, group_name, text)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f'این درخواست ریویو رو نتونستم از طرفت تموم کنم چون که {e}')
        raise e


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    users = await User.get_all_users(group_name)
    if not users:
        await update.message.reply_text('در حال حاضر هیچ کاربری ساخته نشده است.')
        return
    await update.message.reply_text(
        'لیست کاربرهای گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
        '\n- '.join(f'کاربر {user.full_name} با حجم کاری {f"{user.workload:.{3}f}"} و {user.finished_reviews} پی‌آر تموم شده' for user in users))


async def prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    prs = await PullRequest.get_all_prs(group_name)

    if not prs:
        await update.message.reply_text('در حال حاضر هیچ پی‌آری ساخته نشده است.')
        return
    await update.message.reply_text(
        'لیست پی‌آرهای گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
        '\n- '.join(f'پی‌آر {pr.title} با تغییرات +{pr.added_changes}/-{pr.removed_changes} از {pr.owner} با ریویوئر اول {pr.reviewer} و ریویوئر دوم {pr.assignee} و وضعیت {pr.status} از جنس {pr.urgency}' for pr in prs))


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_COMMAND_MESSAGE)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('addteam', add_team))
    app.add_handler(CommandHandler('team', get_team))
    app.add_handler(CommandHandler('teams', get_teams))
    app.add_handler(CommandHandler('review', review))
    app.add_handler(CommandHandler('accept', accept))
    app.add_handler(CommandHandler('finish', finish))
    app.add_handler(CommandHandler('users', users))
    app.add_handler(CommandHandler('prs', prs))
    app.add_handler(CommandHandler('help', help))

    app.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()
