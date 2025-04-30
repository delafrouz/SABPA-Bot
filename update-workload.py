from sabpabot.data_models.pull_request import PullRequest
from sabpabot.data_models.user import User


def get_current_workloads(group_name):
    all_prs = PullRequest.get_all_prs({'group_name': {'value': group_name}})

    if not all_prs:
        return {}

    users_workload = {}
    for pr in all_prs:
        if not pr.review_finished:
            users_workload[pr.reviewer] = users_workload.get(pr.reviewer, 0) + pr.workload

        if not pr.assign_finished:
            users_workload[pr.assignee] = users_workload.get(pr.assignee, 0) + pr.workload

    return users_workload


def update_workloads(group_name):
    users_workload = get_current_workloads(group_name)

    users = User.get_all_users(group_name)
    if not users:
        return
    
    for user in users:
        if user.telegram_id in users_workload:
            user.workload = users_workload[user.telegram_id]
        else:
            user.workload = 0

        user.update_in_db(group_name, user.telegram_id)


if __name__ == '__main__':
    GROUP_NAME = ''
    update_workloads(GROUP_NAME)