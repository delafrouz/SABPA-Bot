import math
from decimal import Decimal
from typing import Dict, List, Union

from sabpabot.handlers.request_review import review
from sabpabot.mongo_access import mongo_db

PR_URGENCY = {'normal', 'urgent', 'critical'}


class PullRequest:
    PR_LINE_TO_POINT = 30
    PR_COLLECTION = 'PullRequests'

    def __init__(self, owner: str, title: str, group_name: str, team: str = '', reviewer: str = '',
                 assignee: str = '', reviewer_confirmed: bool = False, assignee_confirmed: bool = False,
                 can_reviewer_reject: bool = False, can_assignee_reject: bool = False,
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
        self.can_reviewer_reject: bool = can_reviewer_reject
        self.can_assignee_reject: bool = can_assignee_reject
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
            'can_reviewer_reject': self.can_reviewer_reject,
            'can_assignee_reject': self.can_assignee_reject,
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
        can_reviewer_reject = info.get('can_reviewer_reject', False)
        can_assignee_reject = info.get('can_assignee_reject', False)
        review_finished = info.get('review_finished', False)
        assign_finished = info.get('assign_finished', False)
        urgency = info.get('urgency', 'normal')
        added_changes = info.get('added_changes', 0)
        removed_changes = info.get('removed_changes', 0)
        return PullRequest(owner=owner, title=title, group_name=group_name, team=team, reviewer=reviewer,
                           assignee=assignee, reviewer_confirmed=reviewer_confirmed,
                           assignee_confirmed=assignee_confirmed, review_finished=review_finished,
                           can_reviewer_reject=can_reviewer_reject, can_assignee_reject=can_assignee_reject,
                           assign_finished=assign_finished, urgency=urgency, added_changes=added_changes,
                           removed_changes=removed_changes)

    @classmethod
    def get_from_db(cls, group_name: str, title: str) -> 'PullRequest':
        try:
            pr_info = \
                mongo_db[cls.PR_COLLECTION].find_one({'group_name': group_name, 'title': title})
            if not pr_info:
                raise Exception(f'نتونستم پول ریکوئست {title} رو پیدا کنم! :(')
            pr = PullRequest.from_json(pr_info)
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئست {title} رو پیدا کنم! :(')
        return pr

    def set_in_db(self):
        try:
            mongo_db[self.PR_COLLECTION].insert_one(self.to_json())
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئست {self.title} رو بریزم توی دیتابیس! :(')

    @classmethod
    def get_all_prs(cls, filters: dict) -> Union[List['PullRequest'], None]:
        query = {}
        if 'team' in filters and filters['team']['value']:
            query['team'] = filters['team']['value']
        if 'title' in filters and filters['title']['value']:
            query['title'] = filters['title']['value']
        if 'owner' in filters and filters['owner']['value']:
            query['owner'] = filters['owner']['value']
        if 'group_name' in filters and filters['group_name']['value']:
            query['group_name'] = filters['group_name']['value']
        if 'urgency' in filters and filters['urgency']['value']:
            query['urgency'] = filters['urgency']['value']
        finished = filters['finished']['value'] if 'finished' in filters else False
        if 'reviewer' in filters and filters['reviewer']['value']:
            query['$or'] = [
                {'reviewer': filters['reviewer']['value'], 'review_finished': finished},
                {'assignee': filters['reviewer']['value'], 'assign_finished': finished},
            ]
        elif finished:
            query['review_finished'] = True
            query['assign_finished'] = True
        else:
            query['$or'] = [{'review_finished': False}, {'assign_finished': False}]
        try:
            db_prs = mongo_db[cls.PR_COLLECTION].find(query)
            prs = [PullRequest.from_json(db_pr) for db_pr in db_prs]
            return prs
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئستی توی گروه {query["group_name"]} پیدا کنم! :(')

    def update_in_db(self, group_name: str, title: str):
        try:
            update_keys = self.to_json()
            update_keys.pop('group_name')
            update_keys.pop('title')
            mongo_db[self.PR_COLLECTION].update_one({'group_name': group_name, 'title': title},
                                                    {'$set': update_keys})
        except Exception as e:
            raise Exception(f'نتونستم پول ریکوئست {title} رو پیدا کنم! :(')

    def __str__(self):
        reviewer_str = f'{"با" if self.reviewer else "بدون"} ریویوئر اول{" " if self.reviewer else ""}{self.reviewer}'
        assignee_str = f'{"با" if self.assignee else "بدون"} ریویوئر دوم{" " if self.assignee else ""}{self.assignee}'
        pr_link = f'[{self.title}](https://github.com/nobitex/core/pull/{self.title})'
        return (f'پی‌آر {pr_link} با تغییرات +{self.added_changes}/-{self.removed_changes} از {self.owner}'
                f' در تیم {self.team} {reviewer_str} و {assignee_str} و وضعیت '
                f'{self.status} از جنس {self.urgency}'
                )

    @classmethod
    def get_workload(cls, added_changes, removed_changes) -> Decimal:
        return Decimal(math.ceil((added_changes + removed_changes) / cls.PR_LINE_TO_POINT)) * Decimal(0.1)
