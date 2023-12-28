from sabpabot.handlers.accept_review import accept
from sabpabot.handlers.add_team import add_team
from sabpabot.handlers.finish_review import finish
from sabpabot.handlers.get_pull_requests import prs
from sabpabot.handlers.get_teams import get_teams, get_team
from sabpabot.handlers.get_users import users
from sabpabot.handlers.help import get_help
from sabpabot.handlers.request_review import review
from sabpabot.handlers.start import start

HANDLERS = [
    {
        'command_name': 'start',
        'handler_method': start,
        'description': '',
        'help_text': 'دستور آغاز به کار بات',
        'usage_sample': '/start@SabpaBot',
    },
    {
        'command_name': 'addteam',
        'handler_method': add_team,
        'description': 'Add a new team',
        'help_text': 'برای اضافه کردن چندین تیم. این کامند فلگ‌های اجباری اسم -n و اعضا رو -m داره. فلگ تایپ گروه -t '
                     'هم اختیاریه و می‌تونه general یا isolated باشه. می‌تونین هم‌زمان چندتا تیم رو با ; جدا و اضافه '
                     'کنین. گروهی که جنرال باشه همه می‌تونن بهشون درخواست ریویو بدن ولی به اعضای تیم‌های isolated فقط '
                     'خود هم‌تیمی‌هاشون می‌تونن درخواست بدن.',
        'usage_sample': '/addteam@SabpaBot -n group name -t isoalted|general -m @member1 member1_first_name '
                        'member1_last_name @member2 member2_first_name ; -n group2 -t general -m @member2 '
                        'name_does_not_matter_now @member3 new_user_first_name',
    },
    {
        'command_name': 'team',
        'handler_method': get_team,
        'description': "Get a team's information",
        'help_text': 'برای گرفتن اطلاعات یه تیم می‌تونی از این دستور استفاده کنی. در این دستور فلگ -t اسم گروه رو '
                     'مشخص می‌کنه و اجباریه.',
        'usage_sample': '/team@SabpaBot -t group_name',
    },
    {
        'command_name': 'teams',
        'handler_method': get_teams,
        'description': 'Get the list of all teams and their info',
        'help_text': 'برای گرفتن لیست تیم های گروه از این دستور استفاده کن. فلگی هم لازم نداره',
        'usage_sample': '/teams@SabpaBot',
    },
    {
        'command_name': 'review',
        'handler_method': review,
        'description': 'Request a PR review',
        'help_text': 'با این کامند می‌تونین درخواست ریویو بدین. فلگ پول‌ریکوئست با -p و فلگ -t که اسم گروه رو مشخص '
                     'می‌کنه اجباری هستن. با فلگ اختیاری -s می‌تونی وضعیت پول‌ریکوئستت رو مشخص کنی که normal هست یا '
                     'urgent یا critical. برای مشخص کردن ریویوئر اول از -r و برای مشخص کردن ریویوئر دوم از -a استفاده '
                     'کن. بعد از این فلگ‌ها یا باید آی‌دی تلگرام فردی رو بزنی یا مقدار random رو بزن که خود بات برات '
                     'از یه نفر درخواست ریویو کنه. با فلگ -c هم اول تعداد خط‌های اضافه‌شده و بعد تعداد خط‌های کم‌شده '
                     'رو بگو.',
        'usage_sample': '/review@SabpaBot -p pr_number -t team_name -s normal|urgent|critical -r '
                        'first_reviewer_id|random -a second_reviewer_id|random -c 150 50',
    },
    {
        'command_name': 'accept',
        'handler_method': accept,
        'description': 'Accept a PR review request',
        'help_text': 'برای قبول درخواست ریویویی که اومده سمتتون می‌تونین از این کامند استفاده کنین. با فلگ اجباری -p '
                     'شماره‌ی پول‌ریکوئست رو مشخص کنین.',
        'usage_sample': '/accept@SabpaBot -p pr_number',
    },
    {
        'command_name': 'finish',
        'handler_method': finish,
        'description': 'Finish a PR review',
        'help_text': 'برای اعلام پایان ریویویی که اومده سمتتون می‌تونین از این کامند استفاده کنین. با فلگ اجباری -p '
                     'شماره‌ی پول‌ریکوئست رو مشخص کنین.',
        'usage_sample': '/finish@SabpaBot -p pr_number',
    },
    {
        'command_name': 'users',
        'handler_method': users,
        'description': "Get the list of group's users",
        'help_text': 'با این کامند لیست کاربران گروه رو دریافت کنین. نیاز به هیچ فلگی نداره.',
        'usage_sample': '/users@SabpaBot',
    },
    {
        'command_name': 'prs',
        'handler_method': prs,
        'description': "Get the list of group's PRs",
        'help_text': 'لیست تمام پی‌آرهای گروه رو بدون هیچ فلگی دریافت کنین',
        'usage_sample': '/prs@SabpaBot',
    },
    {
        'command_name': 'help',
        'handler_method': get_help,
        'description': 'List all command_names and their usages',
        'help_text': 'لیست کامل دستورها و نمونه‌شون رو دریافت کنین',
        'usage_sample': '/help@SabpaBot',
    },
]
