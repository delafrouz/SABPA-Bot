from sabpabot.data_models.team import Team


async def get_team_by_name(text: str, group_name: str) -> str:
    if not '-t ' in text:
        raise Exception('اسم تیم رو وارد نکردی.')
    text = text[text.find('-n ') + 3:].strip()
    if len(text) <= 0:
        raise Exception('اسم تیم رو وارد نکردی.')
    team = await Team.get_from_db(group_name, text)
    return team.__str__()
