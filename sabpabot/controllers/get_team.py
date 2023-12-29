from typing import List

from sabpabot.data_models.team import Team
from sabpabot.data_models.user import User


class TeamController:
    MEMBER_FLAG = '-m '
    TEAM_FLAG = '-t '

    @classmethod
    def get_teams_response(cls, text: str, group_name: str):
        team_info = cls._extract_team_flags(text, group_name)
        if team_info['team']['value']:
            return cls._get_one_team_info(team_info)
        if team_info['member']['value']:
            return cls._get_members_teams(team_info)
        return cls._get_all_teams_info(team_info)

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
    def _extract_team_flags(cls, text: str, group_name: str) -> dict:
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
