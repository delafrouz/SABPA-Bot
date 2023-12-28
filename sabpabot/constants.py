# ---------------------------------- #
# Constants for command messages
# ---------------------------------- #
from sabpabot.handlers.handlers import HANDLERS

START_COMMAND_MESSAGE = 'سلام! به سامانه‌ی برنامه‌ریزی پی‌آر (سبپا) خوش اومدی. برای دریافت لیست کامندها دستور /help ' \
                        'رو اجرا کن. چی کار می‌تونم برات بکنم؟'


HELP_COMMAND_MESSAGE = 'سلام! به سامانه ی برنامه ریزی پی‌آر خوش اومدی. ما هنوز به گیت‌هاب وصل نیستیم و این بات صرفا ' \
                       'برای برنامه‌ریزی بهتر پی‌آرهامون ساخته شده. این لیست کامندها و نحوه‌ی استفاده ازشونه:\n\n'
for handler in HANDLERS:
    HELP_COMMAND_MESSAGE += f'کامند /{handler["command_name"]}: {handler["help_text"]}\n\n'
    HELP_COMMAND_MESSAGE += f'sample: {handler["usage_sample"]}\n----------\n'
