from typing import List

from sabpabot.data_models.team import Team
from sabpabot.data_models.user import User


def get_team_by_name(text: str, group_name: str) -> str:
    if not '-t ' in text:
        raise Exception('اسم تیم رو وارد نکردی.')
    text = text[text.find('-n ') + 3:].strip()
    if len(text) <= 0:
        raise Exception('اسم تیم رو وارد نکردی.')
    team = Team.get_from_db(group_name, text)
    return team.__str__()


class TeamController:
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
