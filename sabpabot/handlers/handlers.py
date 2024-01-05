from sabpabot.handlers.accept_review import accept
from sabpabot.handlers.add_team import add_team
from sabpabot.handlers.finish_review import finish
from sabpabot.handlers.get_pull_requests import prs
from sabpabot.handlers.get_teams import get_teams
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
        'command_name': 'teams',
        'handler_method': get_teams,
        'description': 'Get the list of all teams and their info',
        'help_text': 'برای گرفتن لیست تیم های گروه از این دستور استفاده کن. در صورتی که این کامند رو بدون هیچ فلگی '
                     'استفاده کنی، لیست تمام تیم‌های گروه رو میده. اگر با فلگ -t استفاده کنی، باید اسم یک تیم رو در '
                     'ادامه وارد کنی تا مشخصات و اعضای اون تیم رو ببینی. اگر از فلگ -m استفاده کنی، باید آی‌دی یک '
                     'کاربر رو در ادامه وارد کنی تا تیم‌هایی که این کاربر عضوشه رو ببینی. هم‌زمان نمی‌تونی از هر دو '
                     'فلگ -t و -m استفاده کنی.',
        'usage_sample': '/teams@SabpaBot \nor /teams@SabpaBot -t team_name \nor /teams@SabpaBot -m @member',
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
        'help_text': 'لیست تمام پی‌آرهای گروه رو دریافت کنین. این دستور هم با فلگ و هم بدون فلگ می‌تونه استفاده بشه. '
                     'اگه فلگ -f رو خالی وارد کردید، لیست پی‌آرهای تمام‌شده برگردانده میشه، وگرنه فقط پی‌آرهای ناتمام رو'
                     'نشون میدیم. اگه فلگ -o رو بزنین، لیست پی‌آرها محدود به پی‌آرهایی میشه که خودتون ایجاد کردید. '
                     'اگه فلگ -t رو به همراه اسم تیم وارد کنین، پی‌آرهای داخل اون تیم نمایش داده میشن. اگه فلگ -r رو'
                     'به همراه آی‌دی شخص مورد نظر وارد کنی، پی‌آرهایی که اون شخص ریویوئر اول یا دومش هست نمایش داده '
                     'میشن. اگر فلگ -s با یک استتوس وارد بشه، پی‌آرهایی با اون استتوس بهتون نمایش داده میشن. در نهایت،'
                     ' اگر فلگ -p رو به همراه شماره‌ی پی‌آر وارد کنی می‌تونی استتوس یک پی‌آر رو به طور خاص ببینی.',
        'usage_sample': '/prs@SabpaBot \nor /prs@SabpaBot -f \nor /prs@SabpaBot -f -o \nor /prs@SabpaBot -f -r @Khodam'
                        '\nor /prs@SabpaBot -o -r @Somebody -t core -s urgent \nor /prs@SabpaBot -f -p 1500'
                        '\nor /prs@SabpaBot -p 1500',
    },
    {
        'command_name': 'help',
        'handler_method': get_help,
        'description': 'List all command_names and their usages',
        'help_text': 'لیست کامل دستورها و نمونه‌شون رو دریافت کنین',
        'usage_sample': '/help@SabpaBot',
    },
]
