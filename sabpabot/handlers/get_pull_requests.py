from telegram import Update
from telegram.ext import ContextTypes

from sabpabot.data_models.pull_request import PullRequest


async def prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.chat.title or update.message.from_user.username
    prs = PullRequest.get_all_prs(group_name)

    if not prs:
        await update.message.reply_text('در حال حاضر هیچ پی‌آری ساخته نشده است.')
        return
    await update.message.reply_text(
        'لیست پی‌آرهای گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
        '\n- '.join(f'پی‌آر {pr.title} با تغییرات +{pr.added_changes}/-{pr.removed_changes} از {pr.owner} با ریویوئر '
                    f'اول {pr.reviewer} و ریویوئر دوم {pr.assignee} و وضعیت {pr.status} از جنس {pr.urgency}' for pr
                    in prs))
