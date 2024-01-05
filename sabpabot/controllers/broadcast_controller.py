class BroadcastController:
    VERSION_FLAG = '-v '

    @classmethod
    def broadcast(cls, text: str) -> str:
        from sabpabot.constants import VERSIONING_MESSAGES

        broadcast_info = cls._extract_broadcast_flags(text)
        if broadcast_info['version']['value']:
            return VERSIONING_MESSAGES[broadcast_info['version']['value']]['message']
        return ''

    @classmethod
    def _extract_broadcast_flags(cls, text) -> dict:
        flags_dict = {
            'version': {
                'value': '',
                'flag': cls.VERSION_FLAG,
                'necessary': False
            }
        }

        meaningful_text = text[text.find('-'):]
        flags = ['-' + e for e in meaningful_text.split('-') if e]

        for flag in flags:
            if flag.startswith(cls.VERSION_FLAG):
                if len(flag.split(cls.VERSION_FLAG)) < 2:
                    raise Exception('ورژن رو درست وارد نکردی!')
                flags_dict['version']['value'] = flag.split(cls.VERSION_FLAG)[1].strip()
        return flags_dict
