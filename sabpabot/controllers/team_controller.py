from decimal import Decimal
from typing import List, Tuple

from sabpabot.data_models.team import Team, TEAM_GROUP_TYPES
from sabpabot.data_models.user import User


class TeamController:
    MEMBER_FLAG = '-m '
    TEAM_FLAG = '-t '
    TEAM_NAME_FLAG = '-n '
    TEAM_TYPE_FLAG = '-t '

    @classmethod
    def get_teams_response(cls, text: str, group_name: str):
        team_info = cls._extract_get_team_flags(text, group_name)
        if team_info['team']['value']:
            return cls._get_one_team_info(team_info)
        if team_info['member']['value']:
            return cls._get_members_teams(team_info)
        return cls._get_all_teams_info(team_info)

    @classmethod
    def create_teams(cls, text: str, group_name: str) -> List[Tuple[Team, List[User]]]:
        teams = text.split(';')
        results = []
        for team_info in teams:
            team_info = team_info.strip()
            if team_info:
                results.append(cls.create_team_and_members(team_info.strip(), group_name))
        return results

    @classmethod
    def _get_one_team_info(cls, team_info: dict) -> str:
        team = Team.get_from_db(team_info['group']['value'], team_info['team']['value'])
        members = team.get_members()
        response = team.__str__() + '، اعضا:\n- ' + '\n- '.join(member.__str__() for member in members)
        return response

    @classmethod
    def _get_members_teams(cls, team_info: dict) -> str:
        member = User.get_from_db(team_info['group']['value'], team_info['member']['value'])
        teams = member.get_teams()
        response = f'تیم‌های کاربر {member.first_name}: ' + '، '.join(team.__str__() for team in teams)
        return response

    @classmethod
    def _get_all_teams_info(cls, team_info: dict) -> str:
        teams = Team.get_all_teams(team_info['group']['value'])
        if not teams:
            return 'در حال حاضر هیچ تیمی ساخته نشده است.'
        return(
                'لیست تیم‌های گروه شما موجود در سامانه‌ی برنامه ریزی پی‌آر:\n- ' +
                '\n- '.join(f'گروه {team.name} از نوع {team.team_type}' for team in teams))

    @classmethod
    def _extract_get_team_flags(cls, text: str, group_name: str) -> dict:
        flags_dict = {
            'team': {
                'value': '',
                'flag': cls.TEAM_FLAG,
            },
            'member': {
                'value': '',
                'flag': cls.MEMBER_FLAG,
            },
            'group': {
                'value': '',
                'flag': None,
            },
        }
        flags_dict['group']['value'] = group_name
        if not text:
            return flags_dict
        flags = ['-' + e for e in text.split('-') if e]

        for flag in flags:
            if flag.startswith('-t '):
                if len(flag.split('-t ')) < 2:
                    raise Exception('اسم تیم رو درست وارد نکردی!')
                flags_dict['team']['value'] = flag.split('-t ')[1].strip()

            elif flag.startswith('-m '):
                if len(flag.split('-m ')) < 2:
                    raise Exception('آی‌دی عضو رو درست مشخص نکردی!')
                flags_dict['member']['value'] = flag.split('-m ')[1].strip()
            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

        if flags_dict['team']['value'] and flags_dict['member']['value']:
            raise Exception('هر دو فلگ تیم و عضو رو نمی‌تونی با هم استفاده کنی. حداکثر فقط یکیش رو بزن')
        return flags_dict

    @classmethod
    def create_team_and_members(cls, team_info: str, group_name: str) -> Tuple[Team, List[User]]:
        """
        Create a team and members from the given team_info.
        """
        team_infos = cls._extract_create_team_flags(team_info, group_name)
        member_infos = team_infos['members']['value'].split()
        members = []
        idx = 0
        while idx < len(member_infos):
            member_id = member_infos[idx]

            if not member_id.startswith('@'):
                raise Exception('اطلاعات هر کاربر باید با آی‌دی تلگرامش شروع بشه!')
            if idx + 1 >= len(member_infos):
                raise Exception(f'اسم کاربر {member_id} رو وارد نکردی!')
            if member_infos[idx + 1].startswith('@'):
                raise Exception(f'اسم کاربر {member_id} رو وارد نکردی!')
            first_name = member_infos[idx + 1]
            last_name = member_infos[idx + 2] if idx + 2 < len(member_infos) else ''
            if last_name.startswith('@'):
                last_name = ''
            user = User.get_or_create(group_name=group_name,
                                      first_name=first_name,
                                      last_name=last_name,
                                      telegram_id=member_id,
                                      workload=Decimal(0))
            members.append(user)
            idx += (3 if last_name else 2)

        if team_infos['type']['value'] and team_infos['type']['value'] not in TEAM_GROUP_TYPES:
            raise Exception(f'تایپ تیم باید جز {TEAM_GROUP_TYPES} باشه')

        team = Team(name=team_infos['team']['value'],
                    group_name=team_infos['group']['value'],
                    team_type=team_infos['type']['value'])
        team.set_in_db()
        for member in members:
            member.add_team(team)
        return team, members

    @classmethod
    def _extract_create_team_flags(cls, team_info: str, group_name: str) -> dict:
        flags_dict = {
            'team': {
                'value': '',
                'flag': cls.TEAM_NAME_FLAG,
                'necessary': True
            },
            'members': {
                'value': '',
                'flag': cls.MEMBER_FLAG,
                'necessary': True
            },
            'type': {
                'value': '',
                'flag': cls.TEAM_TYPE_FLAG,
                'necessary': False
            },
            'group': {
                'value': '',
                'flag': None,
                'necessary': False
            },
        }
        flags_dict['group']['value'] = group_name
        meaningful_text = team_info[team_info.find('-'):]
        flags = ['-' + e for e in meaningful_text.split('-') if e]
        for flag in flags:
            flag = flag.strip()
            if not flag:
                continue

            if flag.startswith('-n '):
                if len(flag.split('-n ')) < 2:
                    raise Exception('اسم تیم رو درست وارد نکردی!')
                flags_dict['team']['value'] = flag.split('-n ')[1].strip()

            elif flag.startswith('-t '):
                if len(flag.split('-t ')) < 2:
                    raise Exception('تایپ تیم رو درست وارد نکردی!')
                flags_dict['type']['value'] = flag.split('-t ')[1].strip()

            elif flag.startswith('-m '):
                if len(flag.split('-m ')) < 2:
                    raise Exception('مشخصات اعضا رو درست وارد نکردی!')
                flags_dict['members']['value'] = flag.split('-m ')[1].strip()
            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')

        for flag in flags_dict:
            if flags_dict[flag]['flag'] and flags_dict[flag]['necessary'] and not flags_dict[flag]['value']:
                raise Exception(f'فلگ {flags_dict[flag]["flag"]} اجیاریه. لطفاً دوباره تلاش کن.')
        return flags_dict

    @classmethod
    def get_non_isolated_members(cls, team: Team, reference_user: User) -> List[User]:
        """
        Return all members inside team 'team' who are in an isoalted team where the reference_user is not a member
        :param team: a team to pick its non-isolated members
        :param reference_user: a user we want to compare other users' memberships against
        :return: a list of non-isolated members of the 'team' who are not in the same isolated team as reference_user
        """
        all_members = team.get_members()
        all_members = [member for member in all_members if member != reference_user]
        reference_users_teams = reference_user.get_teams()
        non_isolated_team_members = []
        for member in all_members:
            should_add = True
            teams = member.get_teams()
            for team in teams:
                if team.team_type == 'isolated' and team not in reference_users_teams:
                    should_add = False
            if should_add:
                non_isolated_team_members.append(member)
        return non_isolated_team_members

    @classmethod
    def get_free_members(cls, members: List[User]) -> List[User]:
        members = sorted(members, key=lambda m: m.workload, reverse=True)

        top_workloads = 2
        if 2 < len(members) < 4:
            top_workloads = 1
        elif len(members) <= 2:
            top_workloads = 0

        if top_workloads > 0:
            if members[top_workloads - 1].workload == members[top_workloads].workload:
                # This member is not really very busy
                top_workloads -= 1
                if top_workloads > 0:
                    if members[top_workloads - 1].workload == members[top_workloads].workload:
                        # This member is not really very busy
                        top_workloads -= 1

        return members[top_workloads:]
