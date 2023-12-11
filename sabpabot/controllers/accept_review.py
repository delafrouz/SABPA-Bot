from sabpabot.data_models.pull_request import PullRequest
from sabpabot.data_models.user import User


async def accept_review(accepter_username: str, group_name: str, text: str) -> str:
    meaningful_text = text[text.find('-'):]
    flags = ['-' + e for e in meaningful_text.split('-') if e]
    title = ''
    accepter_username = accepter_username if accepter_username.startswith('@') else f'@{accepter_username}'
    accepter = await User.get_from_db(group_name, accepter_username)

    for flag in flags:
        if flag.startswith('-p '):
            if len(flag.split('-p ')) < 2:
                raise Exception('شماره‌ی پول‌ریکوئست رو درست وارد نکردی!')
            title = flag.split('-p ')[1].strip()
        else:
            raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

    pr = await PullRequest.get_from_db(group_name, title)

    if not pr:
        raise Exception(f'پی‌آر با شماره‌ی {title} پیدا نکردم!')

    if accepter.telegram_id == pr.reviewer:
        pr.reviewer_confirmed = True
        await pr.set_in_db()
    elif accepter.telegram_id == pr.assignee:
        pr.assignee_confirmed = True
        await pr.set_in_db()
    else:
        raise Exception(f'شما ریویوئر پی‌آر با شماره‌ی {title} نیستی!')

    accepter.workload += pr.workload
    await accepter.set_in_db()

    return f'کاربر {accepter.first_name} پی‌آر {pr.title} شما رو قبول کرد!! {pr.owner}'
