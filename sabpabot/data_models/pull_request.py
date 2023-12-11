import math
from decimal import Decimal
from typing import Union, List, Dict

from sabpabot.mongo_access import mongo_db

PR_URGENCY = {'normal', 'urgent', 'critical'}


class PullRequest:
    PR_LINE_TO_POINT = 30
    PR_COLLECTION = 'PullRequests'

    def __init__(self, owner: str, title: str, group_name: str, team: str = '', reviewer: str = '',
                 assignee: str = '', reviewer_confirmed: bool = False, assignee_confirmed: bool = False,
                 review_finished: bool = False, assign_finished: bool = False, urgency: str = 'normal',
                 added_changes: int = 0, removed_changes: int = 0):
        self.owner: str = owner
        self.title: str = title
        self.group_name: str = group_name
        self.team: str = team
        self.reviewer: str = reviewer
        self.assignee: str = assignee
        self.reviewer_confirmed: bool = reviewer_confirmed
        self.assignee_confirmed: bool = assignee_confirmed
        self.review_finished: bool = review_finished
        self.assign_finished: bool = assign_finished
        self.urgency: str = urgency
        self.added_changes: int = added_changes
        self.removed_changes: int = removed_changes

    @property
    def workload(self) -> Decimal:
        return Decimal(math.ceil((self.added_changes + self.removed_changes) / self.PR_LINE_TO_POINT)) * Decimal(0.1)

    @property
    def status(self) -> str:
        if not self.reviewer:
            return 'no_reviewer'
        if not self.assignee:
            return 'no_assignee'
        if self.review_finished and self.assign_finished:
            return 'done'
        if self.review_finished or self.assign_finished:
            return 'half_done'
        return 'pending_review'

    def to_json(self) -> Dict:
        return {
            'owner': self.owner,
            'title': self.title,
            'group_name': self.group_name,
            'team': self.team if self.team else '',
            'reviewer': self.reviewer if self.reviewer else '',
            'assignee': self.assignee if self.assignee else '',
            'reviewer_confirmed': self.reviewer_confirmed,
            'assignee_confirmed': self.assignee_confirmed,
            'review_finished': self.review_finished,
            'assign_finished': self.assign_finished,
            'urgency': self.urgency,
            'added_changes': self.added_changes,
            'removed_changes': self.removed_changes,
        }

    @staticmethod
    def from_json(info: Dict) -> 'PullRequest':
        owner = info.get('owner', '')
        title = info.get('title', '')
        group_name = info.get('group_name', '')
        team = info.get('team', '')
        reviewer = info.get('reviewer', '')
        assignee = info.get('assignee', '')
        reviewer_confirmed = info.get('reviewer_confirmed', False)
        assignee_confirmed = info.get('assignee_confirmed', False)
        review_finished = info.get('review_finished', False)
        assign_finished = info.get('assign_finished', False)
        urgency = info.get('urgency', 'normal')
        added_changes = info.get('added_changes', 0)
        removed_changes = info.get('removed_changes', 0)
        return PullRequest(owner=owner, title=title, group_name=group_name, team=team, reviewer=reviewer,
                           assignee=assignee, reviewer_confirmed=reviewer_confirmed,
                           assignee_confirmed=assignee_confirmed, review_finished=review_finished,
                           assign_finished=assign_finished, urgency=urgency, added_changes=added_changes,
                           removed_changes=removed_changes)

    @classmethod
    def get_from_db(cls, group_name: str, title: str) -> 'PullRequest':
        try:
            pr_info = \
                mongo_db[cls.PR_COLLECTION].find_one({'group_name': group_name, 'title': title})
            pr = PullRequest.from_json(pr_info)
            if not pr:
                raise Exception(f'نتونستم پول ریکوئست {title} رو پیدا کنم! :(')
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئست {title} رو پیدا کنم! :(')
        return pr

    def set_in_db(self):
        try:
            mongo_db[self.PR_COLLECTION].insert_one(self.to_json())
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئست {self.title} رو بریزم توی دیتابیس! :(')

    @classmethod
    def get_or_create(cls, owner: str, title: str, group_name: str, team: str,
                      urgency: str, reviewer: str, assignee: str,
                      added_changes: int, removed_changes: int) -> 'PullRequest':
        try:
            pr = cls.get_from_db(group_name, title)
            if pr:
                pr.team = team if team else pr.team
                pr.urgency = urgency if urgency else pr.urgency
                pr.reviewer = reviewer if reviewer else pr.reviewer
                pr.assignee = assignee if assignee else pr.assignee
                pr.added_changes = added_changes if added_changes else pr.added_changes
                pr.removed_changes = removed_changes if removed_changes else pr.removed_changes
                return pr
        except Exception as e:
            pr = PullRequest(owner=owner, title=title, group_name=group_name, team=team, reviewer=reviewer,
                             assignee=assignee, urgency=urgency, added_changes=added_changes,
                             removed_changes=removed_changes)
            pr.set_in_db()
            return pr

    @classmethod
    def get_all_prs(cls, group_name: str, **kwargs) -> Union[List['PullRequest'], None]:
        try:
            db_prs = mongo_db[cls.PR_COLLECTION].find({'group_name': group_name, **kwargs})
            prs = [PullRequest.from_json(db_pr) for db_pr in db_prs]
            return prs
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئستی توی گروه {group_name} پیدا کنم! :(')

    @classmethod
    def get_user_reviews(cls, group_name: str, telegram_id: str, reviewer_confirmed: bool = True,
                         review_finished: bool = False) -> Union[List['PullRequest'], None]:
        return cls.get_all_prs(
            group_name, reviewer=telegram_id, reviewer_confirmed=reviewer_confirmed, review_finished=review_finished
        )

    @classmethod
    def get_user_assigns(cls, group_name: str, telegram_id: str, assignee_confirmed: bool = False,
                         assign_finished: bool = False) -> Union[List['PullRequest'], None]:
        return cls.get_all_prs(
            group_name, reviewer=telegram_id, assignee_confirmed=assignee_confirmed, assign_finished=assign_finished
        )

    def update_in_db(self, group_name: str, title: str):
        try:
            update_keys = self.to_json()
            update_keys.pop('group_name')
            update_keys.pop('title')
            mongo_db[self.PR_COLLECTION].update_one({'group_name': group_name, 'title': title},
                                                    {'$set': update_keys})
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئست {title} رو پیدا کنم! :(')
