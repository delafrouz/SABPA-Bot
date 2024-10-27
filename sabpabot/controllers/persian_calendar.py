from dateutil.relativedelta import relativedelta
from khayyam import JalaliDate
from khayyam.algorithms_pure import get_days_in_jalali_month
from telegram_bot_calendar import DetailedTelegramCalendar
from telegram_bot_calendar.base import rows, DAY, SELECT, NOTHING, max_date, min_date, MONTH


class PersianCalendar(DetailedTelegramCalendar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.days_of_week['fa'] = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']
        self.months['fa'] = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]

    def _build_days(self, *args, **kwargs):
        jalali_date = JalaliDate(self.current_date)
        days_num = get_days_in_jalali_month(jalali_date.year, jalali_date.month)

        start = self.current_date.replace(day=1)
        days = self._get_period(DAY, start, days_num)

        days_buttons = rows(
            [
                self._build_button(d.day if d else self.empty_day_button, SELECT if d else NOTHING, DAY, d,
                                   is_random=self.is_random)
                for d in days
            ],
            self.size_day
        )

        days_of_week_buttons = [[
            self._build_button(self.days_of_week[self.locale][i], NOTHING) for i in range(7)
        ]]

        # mind and maxd are swapped since we need maximum and minimum days in the month
        # without swapping next page can generated incorrectly
        nav_buttons = self._build_nav_buttons(DAY, diff=relativedelta(months=1),
                                              maxd=max_date(start, MONTH),
                                              mind=min_date(start + relativedelta(days=days_num - 1), MONTH))

        self._keyboard = self._build_keyboard(days_of_week_buttons + days_buttons + nav_buttons)