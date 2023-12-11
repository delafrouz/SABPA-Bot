
from decimal import Decimal

from sabpabot.data_models.pull_request import PullRequest
from sabpabot.data_models.user import User


async def finish_review(finisher_username: str, group_name: str, text: str) -> str:
    meaningful_text = text[text.find('-'):]
    flags = ['-' + e for e in meaningful_text.split('-') if e]
    title = ''
    finisher_username = finisher_username if finisher_username.startswith('@') else f'@{finisher_username}'
    finisher = await User.get_from_db(group_name, finisher_username)

    for flag in flags:
        flag.strip()
        if flag.startswith('-p '):
            if len(flag.split('-p ')) < 2:
                raise Exception('شماره‌ی پول‌ریکوئست رو درست وارد نکردی!')
            title = flag.split('-p ')[1].strip()
        else:
            raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')
    pr = await PullRequest.get_from_db(group_name, title)

    if not pr:
        raise Exception(f'پی‌آر با شماره‌ی {title} پیدا نکردم!')

    if finisher == pr.reviewer:
        pr.review_finished = True
        await pr.set_in_db()
    elif finisher == pr.assignee:
        pr.assign_finished = True
        await pr.set_in_db()
    else:
        raise Exception(f'شما ریویوئر پی‌آر با شماره‌ی {title} نیستی!')

    finisher.workload = max(finisher.workload-pr.workload, Decimal('0'))
    finisher.finished_reviews += 1
    await finisher.set_in_db()

    result = f'کاربر {finisher.first_name} پی‌آر {pr.title} شما رو تموم کرد!! {pr.owner}'

    if finisher.finished_reviews % 5 == 0:
        result += f'\nکاربر {finisher.first_name} کلی پی‌آر دیده! به افتخارش دست بزنین! 🎉👏'

    return result
