import dataclasses
import random
from decimal import Decimal

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
    FINISHED_FLAG = '-f '

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
        pr, created = cls._get_or_create_pull_request(text=text, group_name=group_name, owner_username=owner_username)

        if not created:
            return f'تغییرات به صورت زیر اعمال شد:\n{str(pr.pull_request)}'

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
    def _get_or_create_pull_request(cls, text: str, group_name: str, owner_username: str) -> Tuple[PR, bool]:
        pr_info = cls._extract_review_flags(text, group_name, owner_username)
        created = False
        try:
            pr = PullRequest.get_from_db(group_name, pr_info['title']['value'])
        except Exception:
            created = True
        if created:
            pr = cls._create_pull_request(group_name, pr_info)
        else:
            pr = cls._update_pull_request(pr, pr_info)
        return pr, created


    @classmethod
    def _extract_review_flags(cls, text: str, group_name: str, owner_username: str) -> dict:
        flags_dict = {
            'team': {
                'value': '',
                'flag': cls.TEAM_FLAG,
                'necessary': False
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
                'necessary': False
            },
            'assignee': {
                'value': '',
                'flag': cls.ASSIGNEE_FLAG,
                'necessary': False
            },
            'changes': {
                'value': '',
                'flag': cls.CHANGE_FLAG,
                'necessary': False
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
    def _update_pull_request(cls, pr: PullRequest, pr_info: dict) -> PR:
        # Cannot change the team, group, title, owner, changes, status for now. Might change some in the future
        if pr_info['owner']['value'] != pr.owner:
            raise Exception('شما اجازه‌ی دسترسی به این پی‌آر رو نداری')

        reviewer, assignee = None, None
        if pr.reviewer:
            reviewer = User.get_from_db(pr.group_name, pr.reviewer)
        else:
            pr_info['reviewer']['necessary'] = True
        if pr.assignee:
            assignee = User.get_from_db(pr.group_name, pr.assignee)
        else:
            pr_info['assignee']['necessary'] = True
        for flag in pr_info:
            if pr_info[flag]['flag'] and pr_info[flag]['necessary'] and not pr_info[flag]['value']:
                raise Exception(f'فلگ {pr_info[flag]["flag"]} اجیاریه. لطفاً دوباره تلاش کن.')

        full_pr = cls.find_reviewer(
            pr=pr, pr_info=pr_info, current_reviewer=reviewer, proposed_reviewer=pr_info['reviewer']['value'],
            current_assignee=assignee, proposed_assignee=pr_info['assignee']['value']
        )

        _, is_reviewer_isolated = cls.is_reviewer_isolated(full_pr, full_pr.reviewer)
        _, is_assignee_isolated = cls.is_reviewer_isolated(full_pr, full_pr.assignee)

        pr.reviewer = full_pr.reviewer.telegram_id
        pr.assignee = full_pr.assignee.telegram_id
        pr.reviewer_confirmed = True
        pr.assignee_confirmed = True
        pr.can_reviewer_reject = is_reviewer_isolated or cls.is_reviewer_busy(full_pr, reviewer)
        pr.can_assignee_reject = is_assignee_isolated or cls.is_reviewer_busy(full_pr, assignee)
        pr.update_in_db(pr.group_name, pr.title)
        return cls.PR(
            pull_request=pr, team=full_pr.team, owner=full_pr.owner, reviewer=full_pr.reviewer,
            assignee=full_pr.assignee
        )

    @classmethod
    def _create_pull_request(cls, group_name: str, pr_info: dict) -> PR:
        pr_info['team']['necessary'] = True
        pr_info['reviewer']['necessary'] = True
        pr_info['assignee']['necessary'] = True
        pr_info['changes']['necessary'] = True
        for flag in pr_info:
            if pr_info[flag]['flag'] and pr_info[flag]['necessary'] and not pr_info[flag]['value']:
                raise Exception(f'فلگ {pr_info[flag]["flag"]} اجیاریه. لطفاً دوباره تلاش کن.')

        full_pr = cls.find_reviewer(
            pr=None, pr_info=pr_info, current_reviewer=None, proposed_reviewer=pr_info['reviewer']['value'],
            current_assignee=None, proposed_assignee=pr_info['assignee']['value']
        )

        added_changes = int(pr_info['changes']['value'].split()[0].strip())
        removed_changes = int(pr_info['changes']['value'].split()[1].strip())
        if added_changes < 0 or removed_changes < 0:
            raise Exception('تعداد خطوط تغییرات نمی‌تونه منفی باشه!')

        if pr_info['status']['value'] and pr_info['status']['value'] not in PR_URGENCY:
            raise Exception(f'استتوس پول ریکوئست باید جز {PR_URGENCY} باشه')
        urgency = pr_info['status']['value'] if pr_info['status']['value'] else 'normal'

        _, is_reviewer_isolated = cls.is_reviewer_isolated(full_pr, full_pr.reviewer)
        _, is_assignee_isolated = cls.is_reviewer_isolated(full_pr, full_pr.assignee)

        pr = PullRequest(
            owner=full_pr.owner.telegram_id, title=pr_info['title']['value'], group_name=group_name,
            team=full_pr.team.name, urgency=urgency,
            reviewer=full_pr.reviewer.telegram_id, assignee=full_pr.assignee.telegram_id,
            reviewer_confirmed=True, assignee_confirmed=True,
            can_reviewer_reject=is_reviewer_isolated or cls.is_reviewer_busy(full_pr, full_pr.reviewer),
            can_assignee_reject=is_assignee_isolated or cls.is_reviewer_busy(full_pr, full_pr.assignee),
            added_changes=added_changes, removed_changes=removed_changes
        )
        pr.set_in_db()
        return cls.PR(pull_request=pr, team=full_pr.team, owner=full_pr.owner, reviewer=full_pr.reviewer,
                      assignee=full_pr.assignee)

    @classmethod
    def find_reviewer(cls, pr: Optional[PullRequest], pr_info: dict,
                      current_reviewer: Optional[User], proposed_reviewer: Optional[str],
                      current_assignee: Optional[User], proposed_assignee: Optional[str]) -> PR:
        if pr:
            owner = User.get_from_db(pr.group_name, pr.owner)
            team = Team.get_from_db(pr.group_name, pr.team)
        else:
            owner = User.get_from_db(pr_info['group']['value'], pr_info['owner']['value'])
            team = Team.get_from_db(pr_info['group']['value'], pr_info['team']['value'])
        if not team:
            raise Exception('تیم پول‌ریکوئست رو درست وارد نکردی!')

        added_changes = int(pr_info['changes']['value'].split()[0].strip()) if not pr else pr.added_changes
        removed_changes = int(pr_info['changes']['value'].split()[1].strip()) if not pr else pr.removed_changes
        if added_changes < 0 or removed_changes < 0:
            raise Exception('تعداد خطوط تغییرات نمی‌تونه منفی باشه!')
        workload = pr.workload if pr else PullRequest.get_workload(added_changes, removed_changes)

        if proposed_reviewer and proposed_reviewer != 'random':
            if proposed_reviewer == pr_info['owner']['value']:
                raise Exception('نمی‌تونی خودت ریویوئر پول ریکوئست خودت باشی که!')
            current_reviewer = User.get_from_db(pr_info['group']['value'], proposed_reviewer)
        if proposed_assignee and proposed_assignee != 'random':
            if proposed_assignee == pr_info['owner']['value']:
                raise Exception('نمی‌تونی خودت ریویوئر پول ریکوئست خودت باشی که!')
            current_assignee = User.get_from_db(pr_info['group']['value'], proposed_assignee)

        if proposed_reviewer == 'random':
            current_reviewer = cls.choose_random_reviewer(team, owner, current_assignee)
        if (pr and pr.reviewer != current_reviewer) or not pr:
            current_reviewer.workload += workload
            current_reviewer.update_in_db(pr_info['group']['value'], current_reviewer.telegram_id)

        if proposed_assignee == 'random':
            current_assignee = cls.choose_random_reviewer(team, owner, current_reviewer)
        if (pr and pr.assignee != current_assignee) or not pr:
            current_assignee.workload += workload
            current_assignee.update_in_db(pr_info['group']['value'], current_assignee.telegram_id)

        return cls.PR(pull_request=pr, team=team, owner=owner, reviewer=current_reviewer, assignee=current_assignee)

    @classmethod
    def choose_random_reviewer(cls, team: Team, owner: User, other_reviewer: Optional[User]) -> User:
        from sabpabot.controllers.team_controller import TeamController

        non_isolated_team_members = TeamController.get_non_isolated_members(team, owner)
        free_members = TeamController.get_free_members(non_isolated_team_members)

        if other_reviewer:
            final_candids = [candid for candid in free_members if candid != other_reviewer]
        else:
            final_candids = free_members
        print(f'final candids: ' + ', '.join(candid.full_name for candid in final_candids))
        if not final_candids:
            raise Exception('ریویوئر به تعداد کافی در این تیم نیست')
        random_reviewer = random.choice(final_candids)
        print(f'random reviewer is {random_reviewer.full_name}')
        return random_reviewer

    @classmethod
    def is_reviewer_busy(cls, pr: PR, reviewer: User) -> bool:
        from sabpabot.controllers.team_controller import TeamController

        non_isolated_team_members = TeamController.get_non_isolated_members(pr.team, pr.owner)
        free_members = TeamController.get_free_members(non_isolated_team_members)
        return reviewer not in free_members and reviewer in non_isolated_team_members

    @classmethod
    def is_reviewer_isolated(cls, pr: PR, reviewer: User) -> Tuple[Optional[Team], bool]:
        from sabpabot.controllers.team_controller import TeamController

        non_isolated_team_members = TeamController.get_non_isolated_members(pr.team, pr.owner)
        if reviewer in non_isolated_team_members:
            return None, False

        reviewer_teams = reviewer.get_teams()
        owner_teams = pr.owner.get_teams()
        for team in reviewer_teams:
            if team.team_type == 'isolated':
                if team not in owner_teams:
                    return team, True
        return None, False

    @classmethod
    def get_reject_response(cls, rejecter_username: str, group_name: str, text: str) -> str:
        meaningful_text = text[text.find('-'):]
        flags = ['-' + e for e in meaningful_text.split('-') if e]
        title = ''
        rejecter_username = rejecter_username if rejecter_username.startswith('@') else f'@{rejecter_username}'
        rejecter = User.get_from_db(group_name, rejecter_username)

        for flag in flags:
            if flag.startswith('-p '):
                if len(flag.split('-p ')) < 2:
                    raise Exception('شماره‌ی پول‌ریکوئست رو درست وارد نکردی!')
                title = flag.split('-p ')[1].strip()
            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

        pr = PullRequest.get_from_db(group_name, title)

        if not pr:
            raise Exception(f'پی‌آر با شماره‌ی {title} پیدا نکردم!')

        if not (rejecter.telegram_id == pr.reviewer or rejecter.telegram_id == pr.assignee):
            raise Exception(f'شما ریویوئر پی‌آر با شماره‌ی {title} نیستی یا امکان ریجکت کردنشو نداری!')
        if rejecter.telegram_id == pr.reviewer and pr.can_reviewer_reject:
            pr.reviewer_confirmed = False
            pr.reviewer = None
            pr.update_in_db(group_name, title)
            rejecter.workload -= pr.workload
        if rejecter.telegram_id == pr.assignee and pr.can_assignee_reject:
            pr.assignee_confirmed = False
            pr.assignee = None
            pr.update_in_db(group_name, title)
            if pr.assignee != pr.reviewer:
                rejecter.workload -= pr.workload

        rejecter.update_in_db(group_name, rejecter.telegram_id)

        return f'کاربر {rejecter.first_name} پی‌آر {pr.title} شما رو رد کرد!! لطفاً یه بار دیگه ریویوئر انتخاب کن. {pr.owner}'

    @classmethod
    def get_finish_response(cls, finisher_username: str, group_name: str, text: str) -> str:
        meaningful_text = text[text.find('-'):]
        flags = ['-' + e for e in meaningful_text.split('-') if e]
        title = ''
        finisher_username = finisher_username if finisher_username.startswith('@') else f'@{finisher_username}'
        finisher = User.get_from_db(group_name, finisher_username)

        for flag in flags:
            flag.strip()
            if flag.startswith('-p '):
                if len(flag.split('-p ')) < 2:
                    raise Exception('شماره‌ی پول‌ریکوئست رو درست وارد نکردی!')
                title = flag.split('-p ')[1].strip()
            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')
        pr = PullRequest.get_from_db(group_name, title)

        if not pr:
            raise Exception(f'پی‌آر با شماره‌ی {title} پیدا نکردم!')

        if finisher.telegram_id == pr.reviewer:
            if not pr.review_finished:
                pr.review_finished = True
                pr.update_in_db(group_name, title)
                finisher.workload = max(finisher.workload - pr.workload, Decimal('0'))
                finisher.finished_reviews += 1
        if finisher.telegram_id == pr.assignee:
            if not pr.assign_finished:
                pr.assign_finished = True
                pr.update_in_db(group_name, title)
                if pr.assignee != pr.reviewer:
                    finisher.workload = max(finisher.workload - pr.workload, Decimal('0'))
                    finisher.finished_reviews += 1
        if not (finisher.telegram_id == pr.reviewer or finisher.telegram_id == pr.assignee):
            raise Exception(f'شما ریویوئر پی‌آر با شماره‌ی {title} نیستی!')

        finisher.update_in_db(group_name, finisher.telegram_id)

        result = f'کاربر {finisher.first_name} پی‌آر {pr.title} شما رو تموم کرد!! {pr.owner}'

        if finisher.finished_reviews % 5 == 0:
            result += f'\nکاربر {finisher.first_name} کلی پی‌آر دیده! به افتخارش دست بزنین! 🎉👏'

        return result

    @classmethod
    def get_prs(cls, text: str, group_name: str, sender_username: str) -> str:
        prs_info = cls._extract_get_prs_flags(text, group_name, sender_username)
        prs = PullRequest.get_all_prs(prs_info)
        if not prs:
            return 'پی‌آری با این مشخصات در گروه شما پیدا نشد.'
        return (
                'لیست پی‌آرهای مد نظر شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
                '\n- '.join(str(pr) for pr in prs)
        )

    @classmethod
    def _extract_get_prs_flags(cls, text: str, group_name: str, sender_username: str) -> dict:
        flags_dict = {
            'team': {
                'value': '',
                'flag': cls.TEAM_FLAG,
                'necessary': False
            },
            'title': {
                'value': '',
                'flag': cls.TITLE_FLAG,
                'necessary': False
            },
            'owner': {
                'value': '',
                'flag': cls.OWNER_FLAG,
                'necessary': False
            },
            'group_name': {
                'value': '',
                'flag': None,
                'necessary': False
            },
            'reviewer': {
                'value': '',
                'flag': cls.REVIEWER_FLAG,
                'necessary': False
            },
            'urgency': {
                'value': '',
                'flag': cls.STATUS_FLAG,
                'necessary': False
            },
            'finished': {
                'value': False,
                'flag': cls.FINISHED_FLAG,
                'necessary': False
            },
        }

        meaningful_text = text[text.find('-'):]
        flags = ['-' + e for e in meaningful_text.split('-') if e]
        flags_dict['group_name']['value'] = group_name

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
                    raise Exception('وضعیت ضرورت پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['urgency']['value'] = flag.split('-s ')[1].strip()

            elif flag.startswith('-r '):
                if len(flag.split('-r ')) < 2:
                    raise Exception('ریویوئر پول‌ریکوئست رو درست وارد نکردی!')
                flags_dict['reviewer']['value'] = flag.split('-r ')[1].strip()

            elif flag.startswith('-f ') or flag.endswith('-f'):
                flags_dict['finished']['value'] = True

            elif flag.startswith('-o ') or flag.endswith('-o'):
                flags_dict['owner']['value'] = sender_username

            elif not flag:
                continue

            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

        return flags_dict
