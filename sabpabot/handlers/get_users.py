from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.data_models.user import User


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    users = User.get_all_users(group_name)
    if not users:
        await update.message.reply_text('در حال حاضر هیچ کاربری ساخته نشده است.')
        return
    await update.message.reply_text(
        'لیست کاربرهای گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
        '\n- '.join(f'کاربر {user.full_name} با حجم کاری {f"{user.workload:.{3}f}"} و {user.finished_reviews} پی‌آر '
                    f'تموم شده' for user in users))
