import dataclasses
import random

from typing import Tuple, Optional

from ..data_models.pull_request import PR_URGENCY, PullRequest
from ..data_models.team import Team
from ..data_models.user import User


def choose_random_reviewer(text: str, group_name: str, owner: User, other_reviewer: Optional[User]) -> User:
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
    members_except_owner = [member for member in all_members if member.telegram_id != pr.owner]

    owner = User.get_from_db(pr.group_name, pr.owner)
    owner_teams = owner.get_teams()
    non_isolated_team_members = []
    for member in members_except_owner:
        should_add = True
        teams = member.get_teams()
        for team in teams:
            if team.team_type == 'isolated' and team not in owner_teams:
                should_add = False
        if should_add:
            non_isolated_team_members.append(member)

    team_members = sorted(non_isolated_team_members, key=lambda m: m.workload, reverse=True)

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


class PullRequestController:
    TITLE_FLAG = '-p '
    OWNER_FLAG = '-o '
    REVIEWER_FLAG = '-r '
    ASSIGNEE_FLAG = '-a '
    TEAM_FLAG = '-t '
    STATUS_FLAG = '-s '
    CHANGE_FLAG = '-c '

    @dataclasses.dataclass
    class PR:
        pull_request: PullRequest
        team: Team
        owner: User
        reviewer: User
        assignee: User

    @classmethod
    def get_review_response(cls, text: str, group_name: str, owner_username: str) -> str:
        owner_username = owner_username if owner_username.startswith('@') else '@' + owner_username
        pr = cls._get_or_create_pull_request(text=text, group_name=group_name, owner_username=owner_username)

        if owner_username != pr.owner.telegram_id:
            raise Exception('شما اجازه‌ی دسترسی به این پی‌آر رو نداری')

        reviewer_response = ''
        assignee_response = ''
        response_info = ''
        if not pr.reviewer:
            reviewer_response = 'برای ریویوی اول کسی رو انتخاب نکردی.'
        elif is_reviewer_busy(pr.pull_request, pr.reviewer):
            reviewer_response = f'کاربر {pr.reviewer.telegram_id} یه کم سرش شلوغه. اگه درخواست رو قبول نکرد یکی دیگه ' \
                                f'رو برای ریویو انتخاب کن.'
        else:
            isolated_team, reviewer_isolated = is_reviewer_isolated(pr.pull_request, pr.reviewer)
            if reviewer_isolated:
                reviewer_response = f'کاربر {pr.reviewer.telegram_id} عضو تیم {isolated_team.name} عه و نمی‌تونه از ' \
                                    f'شما پی‌آر ببینه. اگه درخواست رو قبول نکرد یکی دیگه رو برای ریویو انتخاب کن.'
            else:
                reviewer_response = f'{pr.reviewer.first_name} درخواست ریویوی اول پی‌آر {pr.pull_request.title} از ' \
                                    f'شما شده. ریویو می‌کنی؟ {pr.pull_request.reviewer}'

        if not pr.assignee:
            assignee_response = 'برای ریویوی دوم کسی رو انتخاب نکردی.'
        elif is_reviewer_busy(pr.pull_request, pr.assignee):
            assignee_response = f'کاربر {pr.assignee.telegram_id} یه کم سرش شلوغه. اگه درخواست رو قبول نکرد یکی دیگه ' \
                                f'رو برای ریویو انتخاب کن.'
        else:
            isolated_team, reviewer_isolated = is_reviewer_isolated(pr.pull_request, pr.assignee)
            if reviewer_isolated:
                assignee_response = f'کاربر {pr.assignee.telegram_id} عضو تیم {isolated_team.name} عه و نمی‌تونه از ' \
                                    f'شما پی‌آر ببینه. اگه درخواست رو قبول نکرد یکی دیگه رو برای ریویو انتخاب کن.'
            else:
                assignee_response = f'{pr.assignee.first_name} درخواست ریویوی دوم پی‌آر {pr.pull_request.title} از ' \
                                    f'شما شده. ریویو می‌کنی؟ {pr.pull_request.reviewer}'

        if (reviewer_response != 'برای ریویوی اول کسی رو انتخاب نکردی.'
                or assignee_response != 'برای ریویوی دوم کسی رو انتخاب نکردی.'):
            response_info = f'اطلاعات پی‌آر با تغییرات +{pr.pull_request.added_changes}/-{pr.pull_request.removed_changes}' \
                            f' اینجا موجوده: https://github.com/nobitex/core/pull/{pr.pull_request.title}' \
                            f'. چک کن ببین واگعیه یا کیکه'

        if response_info and pr.pull_request.urgency != 'normal':
            if pr.pull_request.urgency == 'critical':
                response_info += '\n این پی‌آر حیاتیه لطفا همین الان ریویو کنین❗️❗️'
            elif pr.pull_request.urgency == 'urgent':
                response_info += '\n این پی آر مهمه لطفا تا آخر امروز ریویو کنین⚠️⚠️'

        return f'{reviewer_response}\n\n{assignee_response}\n\n{response_info}'.strip()

    @classmethod
    def get_accept_response(cls, text: str, group_name: str, owner_username: str) -> str:
        pass

    @classmethod
    def get_finish_response(cls, text: str, group_name: str, owner_username: str) -> str:
        pass

    @classmethod
    def _get_or_create_pull_request(cls, text: str, group_name: str, owner_username: str) -> PR:
        pr_info = cls._extract_review_flags(text, group_name, owner_username)

        owner = User.get_from_db(group_name, pr_info['owner']['value'])

        team = Team.get_from_db(group_name, pr_info['team']['value'])
        if not team:
            raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')

        reviewer, assignee = None, None
        if pr_info['reviewer']['value'] != 'random':
            if pr_info['reviewer']['value'] == pr_info['owner']['value']:
                raise Exception('نمی‌تونی خودت ریویوئر پول ریکوئست خودت باشی که!')
            reviewer = User.get_from_db(group_name, pr_info['reviewer']['value'])
        if pr_info['assignee']['value'] != 'random':
            if pr_info['assignee']['value'] == pr_info['owner']['value']:
                raise Exception('نمی‌تونی خودت ریویوئر پول ریکوئست خودت باشی که!')
            assignee = User.get_from_db(group_name, pr_info['assignee']['value'])
        if pr_info['reviewer']['value'] == 'random':
            reviewer = choose_random_reviewer(text, group_name, owner, assignee)
        if pr_info['assignee']['value'] == 'random':
            assignee = choose_random_reviewer(text, group_name, owner, reviewer)

        added_changes = int(pr_info['changes']['value'].split()[0].strip())
        removed_changes = int(pr_info['changes']['value'].split()[1].strip())
        if added_changes < 0 or removed_changes < 0:
            raise Exception('تعداد خطوط تغییرات نمی‌تونه منفی باشه!')

        if pr_info['status']['value'] and pr_info['status']['value'] not in PR_URGENCY:
            raise Exception(f'استتوس پول ریکوئست باید جز {PR_URGENCY} باشه')

        pr = PullRequest.get_or_create(owner=owner.telegram_id,
                                       title=pr_info['title']['value'],
                                       group_name=group_name,
                                       team=team.name,
                                       urgency=pr_info['status']['value'],
                                       reviewer=reviewer.telegram_id,
                                       assignee=assignee.telegram_id,
                                       added_changes=added_changes,
                                       removed_changes=removed_changes)
        return cls.PR(pull_request=pr, team=team, owner=owner, reviewer=reviewer, assignee=assignee)

    @classmethod
    def _extract_review_flags(cls, text: str, group_name: str, owner_username: str) -> dict:
        flags_dict = {
            'team': {
                'value': '',
                'flag': cls.TEAM_FLAG,
                'necessary': True
            },
            'title': {
                'value': '',
                'flag': cls.TITLE_FLAG,
                'necessary': True
            },
            'owner': {
                'value': '',
                'flag': None,
                'necessary': False
            },
            'group': {
                'value': '',
                'flag': None,
                'necessary': False
            },
            'reviewer': {
                'value': '',
                'flag': cls.REVIEWER_FLAG,
                'necessary': True
            },
            'assignee': {
                'value': '',
                'flag': cls.ASSIGNEE_FLAG,
                'necessary': True
            },
            'changes': {
                'value': '',
                'flag': cls.CHANGE_FLAG,
                'necessary': True
            },
            'status': {
                'value': '',
                'flag': cls.STATUS_FLAG,
                'necessary': False
            },
        }
        meaningful_text = text[text.find('-'):]
        flags = ['-' + e for e in meaningful_text.split('-') if e]
        flags_dict['owner']['value'] = owner_username
        flags_dict['group']['value'] = group_name

        for flag in flags:
            if flag.startswith('-p '):
                if len(flag.split('-p ')) < 2:
                    raise Exception('شماره‌ی پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['title']['value'] = flag.split('-p ')[1].strip()

            elif flag.startswith('-t '):
                if len(flag.split('-t ')) < 2:
                    raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['team']['value'] = flag.split('-t ')[1].strip()

            elif flag.startswith('-s '):
                if len(flag.split('-s ')) < 2:
                    raise Exception('استتوس پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['status']['value'] = flag.split('-t ')[1].strip()

            elif flag.startswith('-r '):
                if len(flag.split('-r ')) < 2:
                    raise Exception('ریویوئر پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['reviewer']['value'] = flag.split('-r ')[1].strip()

            elif flag.startswith('-a '):
                if len(flag.split('-a ')) < 2:
                    raise Exception('اساینی پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['assignee']['value'] = flag.split('-a ')[1].strip()

            elif flag.startswith('-c '):
                if len(flag.split('-c ')) < 2:
                    raise Exception('تغییرات پول ریکوئست رو درست وارد نکردی!')
                flags_dict['changes']['value'] = flag.split('-c ')[1]

            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

        for flag in flags_dict:
            if flags_dict[flag]['flag'] and flags_dict[flag]['necessary'] and not flags_dict[flag]['value']:
                raise Exception(f'فلگ {flags_dict[flag]["flag"]} اجیاریه. لطفاً دوباره تلاش کن.')
        return flags_dict
