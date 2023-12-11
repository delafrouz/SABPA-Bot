import asyncio
from typing import Dict, Union, List

from sabpabot.data_models.user import User
from sabpabot.mongo_access import mongo_db


TEAM_GROUP_TYPES = {'general', 'isolated'}


class Team:
    TEAM_COLLECTION = 'Teams'
    MEMBERSHIP_COLLECTION = 'TeamMembership'

    def __init__(self, name: str = '', group_name: str = '', team_type: str = 'general') -> None:
        self.name: str = name
        self.group_name = group_name
        self.team_type = team_type if team_type else 'general'

    async def add_member(self, user: User):
        try:
            await mongo_db[self.MEMBERSHIP_COLLECTION].insert_one(
                {'group_name': self.group_name, 'user_id': user.telegram_id, 'team_name': self.name}
            )
        except Exception as e:
            raise Exception(f'نتونستم کاربر {user.telegram_id[1:]} رو بندازم توی تیم {self.name}! :(')

    async def get_members(self) -> List[User]:
        try:
            db_user_ids = (
                mongo_db[self.MEMBERSHIP_COLLECTION]
                .find(
                    {'group_name': self.group_name, 'team_name': self.name},
                    {'_id': 0, 'group_name': 0, 'user_id': 1, 'team_name': 0}
                )
            )
            user_ids = [user_id['user_id'] for user_id in db_user_ids]
            user_coroutines = [User.get_from_db(group_name=self.group_name, telegram_id=user_id) for user_id in user_ids]
            users = await asyncio.gather(*user_coroutines)
            return users
        except Exception as e:
            return []

    def to_json(self) -> Dict:
        return {
            'name': self.name,
            'group_name': self.group_name,
            'team_type': self.team_type
        }

    @staticmethod
    def from_json(info: Dict) -> 'Team':
        name = info.get('name', '')
        team_type = info.get('team_type', 'general')
        group_name = info.get('group_name', '')
        return Team(name=name, group_name=group_name, team_type=team_type)

    @classmethod
    async def get_from_db(cls, group_name: str, name: str) -> 'Team':
        try:
            team_info = \
                await mongo_db[cls.TEAM_COLLECTION].find_one({'group_name': group_name, 'name': name})
            team = Team.from_json(team_info)
            if not team:
                raise Exception(f'نتونستم تیم {name} رو پیدا کنم! :(')
        except Exception as e:
            raise Exception(f'نتونستم تیم {name} رو پیدا کنم! :(')
        return team

    async def set_in_db(self):
        try:
            await mongo_db[self.TEAM_COLLECTION].insert_one(self.to_json())
        except Exception as e:
            raise Exception(f'نتونستم تیم {self.name} رو بریزم توی دیتابیس! :(')

    @classmethod
    async def get_all_teams(cls, group_name: str) -> Union[List['Team'], None]:
        try:
            db_teams = await mongo_db[cls.TEAM_COLLECTION].find({'group_name': group_name})
            teams = [Team.from_json(db_team) for db_team in db_teams]
            return teams
        except Exception as e:
            raise Exception(f'نتونستم تیمی توی گروه {group_name} پیدا کنم! :(')

    def __hash__(self):
        return hash(f'{self.group_name}_{self.name}')

    def __eq__(self, other: 'Team'):
        return (self.__hash__() == other.__hash__() and self.name == other.name
                and self.team_type == other.team_type)

    def __str__(self):
        return f'تیم {self.name} از نوع {self.team_type}'
