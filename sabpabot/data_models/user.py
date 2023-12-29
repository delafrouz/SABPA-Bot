from decimal import Decimal
from typing import Union, List, Dict, Set

from sabpabot.mongo_access import mongo_db


class User:
    USER_COLLECTION = 'Users'
    MEMBERSHIP_COLLECTION = 'TeamMembership'

    def __init__(self, first_name: str, last_name: str, telegram_id: str, workload: Decimal, group_name: str,
                 finished_reviews: int = 0) -> None:
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.telegram_id: str = telegram_id
        self.workload: Decimal = workload
        self.group_name: str = group_name
        self.finished_reviews: int = finished_reviews

    def add_team(self, team: 'Team'):
        try:
            mongo_db[self.MEMBERSHIP_COLLECTION].insert_one(
                {'group_name': self.group_name, 'user_id': self.telegram_id, 'team_name': team.name}
            )
        except Exception as e:
            raise Exception(f'نتونستم کاربر {self.telegram_id[1:]} رو بندازم توی تیم {team.name}! :(')

    def get_teams(self) -> List['Team']:
        from sabpabot.data_models.team import Team
        try:
            db_team_names = (
                mongo_db[self.MEMBERSHIP_COLLECTION]
                .find(
                    {'group_name': self.group_name, 'user_id': self.telegram_id},
                    {'_id': 0, 'team_name': 1}
                )
            )
            team_names = [db_team_name['team_name'] for db_team_name in db_team_names]
            teams = [Team.get_from_db(group_name=self.group_name, name=team_name) for team_name in team_names]
            return teams
        except Exception as e:
            return []

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def to_json(self) -> Dict:
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'telegram_id': self.telegram_id,
            'workload': str(self.workload),
            'group_name': self.group_name,
            'finished_reviews': self.finished_reviews
        }

    @staticmethod
    def from_json(info: Dict) -> 'User':
        first_name = info.get('first_name', '')
        last_name = info.get('last_name', '')
        telegram_id = info.get('telegram_id', '')
        workload = max(Decimal(info.get('workload', 0)), Decimal('0'))
        group_name = info.get('group_name', '')
        finished_reviews = info.get('finished_reviews', 0)
        return User(first_name=first_name, last_name=last_name, telegram_id=telegram_id, workload=workload,
                    group_name=group_name, finished_reviews=finished_reviews)

    @classmethod
    def get_from_db(cls, group_name: str, telegram_id: str) -> 'User':
        try:
            user_info = \
                mongo_db[cls.USER_COLLECTION].find_one({'group_name': group_name, 'telegram_id': telegram_id})
            user = User.from_json(user_info)
            if not user:
                raise Exception(f'نتونستم کاربر {telegram_id[1:]} رو پیدا کنم! :(')
        except Exception as e:
            raise Exception(f'نتونستم کاربر {telegram_id[1:]} رو پیدا کنم! :(')
        return user

    def set_in_db(self):
        try:
            mongo_db[self.USER_COLLECTION].insert_one(self.to_json())
        except Exception as e:
            raise Exception(f'نتونستم کاربر {self.telegram_id[1:]} رو بریزم توی دیتابیس! :(')

    @classmethod
    def get_or_create(cls, group_name: str, first_name: str, last_name: str, telegram_id: str,
                      workload: Decimal, teams: Union[Set, None] = None) -> 'User':
        try:
            user = cls.get_from_db(group_name, telegram_id)
            if user:
                if teams:
                    for team in teams:
                        user.add_team(team)
            return user
        except Exception as e:
            pass
        user = User(first_name=first_name, last_name=last_name, telegram_id=telegram_id, workload=workload,
                    group_name=group_name)
        user.set_in_db()
        return user

    def __hash__(self):
        return hash(f'{self.group_name}_{self.telegram_id}')

    def __eq__(self, other: 'User'):
        return self.__hash__() == other.__hash__() and self.telegram_id == other.telegram_id

    def __str__(self):
        return f'کاربر {self.full_name} با آی‌دی {self.telegram_id} و حجم کار {f"{self.workload:.{3}f}"}'

    @classmethod
    def get_all_users(cls, group_name: str) -> Union[List['User'], None]:
        try:
            db_users = mongo_db[cls.USER_COLLECTION].find({'group_name': group_name})
            users = [User.from_json(db_user) for db_user in db_users]
            return users
        except Exception as e:
            raise Exception(f'نتونستم کاربری توی گروه {group_name} پیدا کنم! :(')

    def update_in_db(self, group_name: str, telegram_id: str):
        try:
            update_keys = self.to_json()
            update_keys.pop('group_name')
            update_keys.pop('telegram_id')
            mongo_db[self.USER_COLLECTION].update_one({'group_name': group_name, 'telegram_id': telegram_id},
                                                      {'$set': update_keys})
        except Exception as e:
            raise Exception(f'نتونستم کاربر {self.telegram_id[1:]} رو پیدا کنم! :(')
