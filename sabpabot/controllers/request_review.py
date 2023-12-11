import random

from typing import Tuple, Union, Optional

from ..data_models.pull_request import PR_URGENCY, PullRequest
from ..data_models.team import Team
from ..data_models.user import User


def choose_random_reviewer(text: str, group_name: str, owner: User, other_reviewer: Union[User, None]) -> User:
    meaningful_text = text[text.find('-'):]
    flags = ['-' + e for e in meaningful_text.split('-') if e]
    team = None
    for flag in flags:
        if flag.startswith('-t '):
            if len(flag.split('-t ')) < 2:
                raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')
            team = Team.get_from_db(group_name, flag.split('-t ')[1].strip())
            if not team:
                raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')

    all_members = team.get_members()
    team_members = sorted([member for member in all_members if member.telegram_id != owner.telegram_id],
                          key=lambda m: m.workload,
                          reverse=True)
    owner_teams = owner.get_teams()
    non_isolated_team_members = []
    for member in team_members:
        should_add = True
        teams = member.get_teams()
        for team in teams:
            if team.team_type == 'isolated' and team not in owner_teams:
                should_add = False
        if should_add:
            non_isolated_team_members.append(member)

    print(f'non_isolated_team_members: {non_isolated_team_members}')

    top_workloads = 2
    if 2 < len(non_isolated_team_members) < 4:
        top_workloads = 1
    elif len(non_isolated_team_members) <= 2:
        top_workloads = 0

    if top_workloads > 0:
        if non_isolated_team_members[top_workloads - 1].workload == non_isolated_team_members[top_workloads].workload:
            # This member is not really very busy
            top_workloads -= 1
            if top_workloads > 0:
                if non_isolated_team_members[top_workloads - 1].workload == \
                        non_isolated_team_members[top_workloads].workload:
                    # This member is not really very busy
                    top_workloads -= 1

    candids = non_isolated_team_members[top_workloads:]
    print(f'candids: ' + ', '.join(candid.full_name for candid in candids))
    if other_reviewer:
        final_candids = [candid for candid in candids if candid != other_reviewer]
    else:
        final_candids = candids
    print(f'final candids: ' + ', '.join(candid.full_name for candid in final_candids))

    random_reviewer = random.choice(final_candids)
    print(f'random reviewer is {random_reviewer.full_name}')
    return random_reviewer


def is_reviewer_busy(pr: PullRequest, reviewer: User) -> bool:
    pr_team = Team.get_from_db(pr.group_name, pr.team)
    all_members = pr_team.get_members()
    team_members = sorted([
        member for member in all_members
        if member.telegram_id != pr.owner
    ], key=lambda m: m.workload, reverse=True)
    top_workloads = 2
    if 2 < len(team_members) < 4:
        top_workloads = 1
    elif len(team_members) <= 2:
        top_workloads = 0

    if top_workloads <= 0:
        return False

    if team_members[top_workloads - 1].workload == team_members[top_workloads].workload:
        # This member is not really very busy
        top_workloads -= 1
        if top_workloads > 0:
            if team_members[top_workloads - 1].workload == team_members[top_workloads].workload:
                # This member is not really very busy
                top_workloads -= 1
    if top_workloads <= 0:
        return False

    for member in team_members[:top_workloads]:
        if member == reviewer:
            return True
    return False


def is_reviewer_isolated(pr: PullRequest, reviewer: User) -> Tuple[Optional[Team], bool]:
    reviewer_teams = reviewer.get_teams()
    owner = User.get_from_db(pr.group_name, pr.owner)
    owner_teams = owner.get_teams()
    for team in reviewer_teams:
        if team.team_type == 'isolated':
            if team in owner_teams:
                return team, False
            return team, True
    return None, False


def request_review(text: str, group_name: str, owner_username: str) -> PullRequest:
    meaningful_text = text[text.find('-'):]
    flags = ['-' + e for e in meaningful_text.split('-') if e]
    title = ''
    owner_username = owner_username if owner_username.startswith('@') else f'@{owner_username}'
    owner = User.get_from_db(group_name, owner_username)
    reviewer = None
    assignee = None
    team = None
    urgency = 'normal'
    added_changes = 0
    removed_changes = 0

    for flag in flags:
        if flag.startswith('-p '):
            if len(flag.split('-p ')) < 2:
                raise Exception('شماره‌ی پول‌ریکوئست رو درست وارد نکردی!')
            title = flag.split('-p ')[1].strip()

        elif flag.startswith('-t '):
            if len(flag.split('-t ')) < 2:
                raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')
            team = Team.get_from_db(group_name, flag.split('-t ')[1].strip())
            if not team:
                raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')

        elif flag.startswith('-s '):
            if len(flag.split('-s ')) < 2:
                raise Exception('استتوس پول‌ریکوئست رو درست وارد نکردی!')
            urgency = flag.split('-s ')[1].strip()
            if urgency not in PR_URGENCY:
                raise Exception(f'استتوس پول ریکوئست باید جز {PR_URGENCY} باشه')

        elif flag.startswith('-r '):
            if len(flag.split('-r ')) < 2:
                raise Exception('ریویوئر پول‌ریکوئست رو درست وارد نکردی!')
            reviewer_name = flag.split('-r ')[1].strip()
            if reviewer_name == 'random':
                reviewer = choose_random_reviewer(text, group_name, owner, assignee)
            else:
                if reviewer_name == owner_username:
                    raise Exception('نمی‌تونی خودت ریویوئر پول ریکوئست خودت باشی که!')
                reviewer = User.get_from_db(group_name, reviewer_name)

        elif flag.startswith('-a '):
            if len(flag.split('-a ')) < 2:
                raise Exception('اساینی پول‌ریکوئست رو درست وارد نکردی!')
            assignee_name = flag.split('-a ')[1].strip()
            if assignee_name == 'random':
                assignee = choose_random_reviewer(text, group_name, owner, reviewer)
            else:
                if assignee_name == owner_username:
                    raise Exception('نمی‌تونی خودت ریویوئر پول ریکوئست خودت باشی که!')
                assignee = User.get_from_db(group_name, assignee_name)

        elif flag.startswith('-c '):
            if len(flag.split('-c ')) < 2:
                raise Exception('تغییرات پول ریکوئست رو درست وارد نکردی!')
            changes = flag.split('-c ')[1]
            if len(changes.split()) < 2:
                raise Exception('تغییرات مثبت و منفی پول ریکوئست رو درست وارد نکردی!')
            added_changes = int(changes.split()[0].strip())
            removed_changes = int(changes.split()[1].strip())

        else:
            raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

    return PullRequest.get_or_create(owner=owner.telegram_id,
                                     title=title,
                                     group_name=group_name,
                                     team=team.name,
                                     urgency=urgency,
                                     reviewer=reviewer.telegram_id,
                                     assignee=assignee.telegram_id,
                                     added_changes=added_changes,
                                     removed_changes=removed_changes)


def create_request_response(text: str, group_name: str, owner_username: str) -> str:
    owner_username = owner_username if owner_username.startswith('@') else '@' + owner_username
    pr = request_review(text=text, group_name=group_name, owner_username=owner_username)

    if owner_username != pr.owner:
        raise Exception('شما اجازه‌ی دسترسی به این پی‌آر رو نداری')
    pr.set_in_db()
    reviewer = User.get_from_db(pr.group_name, pr.reviewer)
    assignee = User.get_from_db(pr.group_name, pr.assignee)

    reviewer_response = ''
    assignee_response = ''
    response_info = ''
    if not reviewer:
        reviewer_response = 'برای ریویوی اول کسی رو انتخاب نکردی.'
    elif is_reviewer_busy(pr, reviewer):
        reviewer_response = f'کاربر {reviewer.first_name} یه کم سرش شلوغه. لطفا یکی دیگه رو انتخاب کن.'
    else:
        isolated_team, reviewer_isolated = is_reviewer_isolated(pr, reviewer)
        if reviewer_isolated:
            reviewer_response = f'کاربر {reviewer.first_name} عضو تیم {isolated_team.name} عه و نمی‌تونه از شما پی‌آر ببینه.'
        else:
            reviewer_response = f'{reviewer.first_name} درخواست ریویوی اول پی‌آر {pr.title} از شما شده. ریویو می‌کنی؟ {pr.reviewer}'

    if not assignee:
        assignee_response = 'برای ریویوی دوم کسی رو انتخاب نکردی.'
    elif is_reviewer_busy(pr, assignee):
        assignee_response = f'کاربر {assignee.first_name} یه کم سرش شلوغه. لطفا یکی دیگه رو انتخاب کن.'
    else:
        isolated_team, reviewer_isolated = is_reviewer_isolated(pr, assignee)
        if reviewer_isolated:
            assignee_response = f'کاربر {assignee.first_name} عضو تیم {isolated_team.name} عه و نمی‌تونه از شما پی‌آر ببینه.'
        else:
            assignee_response = f'{assignee.first_name} درخواست ریویوی دوم پی‌آر {pr.title} از شما شده. ریویو می‌کنی؟ {pr.assignee}'

    if reviewer_response != 'برای ریویوی اول کسی رو انتخاب نکردی.' or assignee_response != 'برای ریویوی دوم کسی رو انتخاب نکردی.':
        response_info = f'اطلاعات پی‌آر با تغییرات +{pr.added_changes}/-{pr.removed_changes} اینجا موجوده: https://github.com/nobitex/core/pull/{pr.title}. چک کن ببین واگعیه یا کیکه'

    if response_info and pr.urgency != 'normal':
        if pr.urgency == 'critical':
            response_info += '\n این پی‌آر حیاتیه لطفا همین الان ریویو کنین❗️❗️'
        elif pr.urgency == 'urgent':
            response_info += '\n این پی آر مهمه لطفا تا آخر امروز ریویو کنین⚠️⚠️'

    return f'{reviewer_response}\n\n{assignee_response}\n\n{response_info}'.strip()
