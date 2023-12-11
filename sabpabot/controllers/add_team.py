from decimal import Decimal
from typing import Tuple, List

from sabpabot.data_models.team import Team, TEAM_GROUP_TYPES
from sabpabot.data_models.user import User


async def create_team_and_members(team_info: str, group_name: str) -> Tuple[Team, List[User]]:
    """
    Create a team and members from the given team_info.
    """
    team_name = ''
    members = []
    group_type = ''
    meaningful_text = team_info[team_info.find('-'):]
    flags = ['-' + e for e in meaningful_text.split('-') if e]
    for flag in flags:
        flag = flag.strip()
        print(f'flag is {flag}')
        if not flag:
            continue
        try:
            if flag.startswith('-n '):
                if len(flag.split('-n ')) < 2:
                    raise Exception('اسم تیم رو درست وارد نکردی!')
                team_name = flag.split('n ')[1].strip()

            elif flag.startswith('-t '):
                if len(flag.split('-t ')) < 2:
                    raise Exception('تایپ تیم رو درست وارد نکردی!')
                group_type = flag.split('t ')[1].strip()
                if group_type not in TEAM_GROUP_TYPES:
                    print(f'{group_type} is not a valid group type!')
                    raise Exception(f'تایپ تیم باید جز {TEAM_GROUP_TYPES} باشه')

            elif flag.startswith('-m '):
                if len(flag.split('-m ')) < 2:
                    raise Exception('مشخصات اعضا رو درست وارد نکردی!')
                member_infos = flag.split('m ')[1].strip().split()
                idx = 0
                while idx < len(member_infos):
                    member_id = member_infos[idx]
                    print(f'member {idx}: {member_id}')
                    if not member_id.startswith('@'):
                        raise Exception('اطلاعات هر کاربر باید با آی‌دی تلگرامش شروع بشه!')
                    if idx + 1 >= len(member_infos):
                        raise Exception(f'اسم کاربر {member_id} رو وارد نکردی!')
                    if member_infos[idx + 1].startswith('@'):
                        raise Exception(f'اسم کاربر {member_id} رو وارد نکردی!')
                    first_name = member_infos[idx + 1]
                    last_name = member_infos[idx +
                                             2] if idx + 2 < len(member_infos) else ''
                    if last_name.startswith('@'):
                        last_name = ''
                    user = await User.get_or_create(group_name=group_name,
                                                    first_name=first_name,
                                                    last_name=last_name,
                                                    telegram_id=member_id,
                                                    workload=Decimal(0))
                    members.append(user)
                    idx += (3 if last_name else 2)
            else:
                raise Exception('این پیغام رو بلد نبودم هندل کنم. برای راهنمایی دوباره /help رو ببین.')
        except Exception as e:
            raise e
    team = Team(name=team_name,
                group_name=group_name,
                team_type=group_type)
    await team.set_in_db()
    for member in members:
        await member.add_team(team)
        await member.set_in_db()
    return team, members


async def create_teams(text: str, group_name: str) -> List[Tuple[Team, List[User]]]:
    teams = text.split(';')
    results = []
    for team_info in teams:
        results.append(await create_team_and_members(team_info.strip(), group_name))
    return results
