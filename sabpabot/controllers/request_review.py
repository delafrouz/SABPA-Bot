import dataclasses
import random

from typing import Tuple, Optional

from ..data_models.pull_request import PR_URGENCY, PullRequest
from ..data_models.team import Team
from ..data_models.user import User


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
        elif cls.is_reviewer_busy(pr, pr.reviewer):
            reviewer_response = f'کاربر {pr.reviewer.telegram_id} یه کم سرش شلوغه. اگه درخواست رو قبول نکرد یکی دیگه ' \
                                f'رو برای ریویو انتخاب کن.'
        else:
            isolated_team, reviewer_isolated = cls.is_reviewer_isolated(pr, pr.reviewer)
            if reviewer_isolated:
                reviewer_response = f'کاربر {pr.reviewer.telegram_id} عضو تیم {isolated_team.name} عه و نمی‌تونه از ' \
                                    f'شما پی‌آر ببینه. اگه درخواست رو قبول نکرد یکی دیگه رو برای ریویو انتخاب کن.'
            else:
                reviewer_response = f'{pr.reviewer.first_name} درخواست ریویوی اول پی‌آر {pr.pull_request.title} از ' \
                                    f'شما شده. ریویو می‌کنی؟ {pr.pull_request.reviewer}'

        if not pr.assignee:
            assignee_response = 'برای ریویوی دوم کسی رو انتخاب نکردی.'
        elif cls.is_reviewer_busy(pr, pr.assignee):
            assignee_response = f'کاربر {pr.assignee.telegram_id} یه کم سرش شلوغه. اگه درخواست رو قبول نکرد یکی دیگه ' \
                                f'رو برای ریویو انتخاب کن.'
        else:
            isolated_team, reviewer_isolated = cls.is_reviewer_isolated(pr, pr.assignee)
            if reviewer_isolated:
                assignee_response = f'کاربر {pr.assignee.telegram_id} عضو تیم {isolated_team.name} عه و نمی‌تونه از ' \
                                    f'شما پی‌آر ببینه. اگه درخواست رو قبول نکرد یکی دیگه رو برای ریویو انتخاب کن.'
            else:
                assignee_response = f'{pr.assignee.first_name} درخواست ریویوی دوم پی‌آر {pr.pull_request.title} از ' \
                                    f'شما شده. ریویو می‌کنی؟ {pr.pull_request.assignee}'

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
            reviewer = cls.choose_random_reviewer(team, owner, assignee)
        if pr_info['assignee']['value'] == 'random':
            assignee = cls.choose_random_reviewer(team, owner, reviewer)

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

    @classmethod
    def choose_random_reviewer(cls, team: Team, owner: User, other_reviewer: Optional[User]) -> User:
        from sabpabot.controllers.get_team import TeamController

        non_isolated_team_members = TeamController.get_non_isolated_members(team, owner)
        free_members = TeamController.get_free_members(non_isolated_team_members)

        if other_reviewer:
            final_candids = [candid for candid in free_members if candid != other_reviewer]
        else:
            final_candids = free_members
        print(f'final candids: ' + ', '.join(candid.full_name for candid in final_candids))

        random_reviewer = random.choice(final_candids)
        print(f'random reviewer is {random_reviewer.full_name}')
        return random_reviewer

    @classmethod
    def is_reviewer_busy(cls, pr: PR, reviewer: User) -> bool:
        from sabpabot.controllers.get_team import TeamController

        non_isolated_team_members = TeamController.get_non_isolated_members(pr.team, pr.owner)
        free_members = TeamController.get_free_members(non_isolated_team_members)
        for member in free_members:
            print(f'free member in {pr.team.name} is {member.first_name}')

        return reviewer not in free_members and reviewer in non_isolated_team_members

    @classmethod
    def is_reviewer_isolated(cls, pr: PR, reviewer: User) -> Tuple[Optional[Team], bool]:
        from sabpabot.controllers.get_team import TeamController

        non_isolated_team_members = TeamController.get_non_isolated_members(pr.team, pr.owner)
        if reviewer in non_isolated_team_members:
            return None, False

        reviewer_teams = reviewer.get_teams()
        owner_teams = pr.owner.get_teams()
        for team in reviewer_teams:
            if team.team_type == 'isolated':
                if team not in owner_teams:
                    return team, True
