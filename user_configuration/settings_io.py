from configparser import SectionProxy
from minimalog.minimal_log import MinimalLog
from string import digits
from user_configuration.settings_wrapper import get_user_configuration
ml = MinimalLog()
digits_or_sign = digits + '-'
uconf = get_user_configuration()
parsers = uconf.parser.parsers
keyrings = uconf.hardcoded.keys


class QbitConfig:
    @staticmethod
    def get_keyring_for_(metadata=False, search=False, settings=False):
        try:  # FIXME p3, assign return type
            if metadata:
                return keyrings.metadata_parser_keyring
            if search:
                return keyrings.search_parser_keyring
            if settings:
                return keyrings.user_config_parser_keyring
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @classmethod
    def get_keyrings(cls) -> tuple:
        try:
            mk = cls.get_keyring_for_(metadata=True)
            sk = cls.get_keyring_for_(search=True)
            uk = cls.get_keyring_for_(settings=True)
            return mk, sk, uk
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def get_parser_at_default(search=False, settings=False):
        try:  # FIXME p3, assign return type
            parser, key = None, 'DEFAULT'
            if search:
                parser = parsers.search_parser
            if settings:
                parser = parsers.user_settings_parser
            return parser[key]
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def get_parser_at_section(section, metadata=False, search=True, settings=False) -> SectionProxy:
        try:
            assert isinstance(section, str), 'section is not a string'
            if metadata:
                mp = parsers.metadata_added_parser
                assert section in mp, ml.log('section not found in parser')
                parser_at_section = mp[section]
                return parser_at_section
            if search:
                sp = parsers.search_parser
                assert section in sp, ml.log('section not found in parser')
                parser_at_section = sp[section]
                return parser_at_section
            if settings:
                ucp = parsers.user_settings_parser
                assert section in ucp, ml.log('section not found in parser')
                parser_at_section = ucp[section]
                return parser_at_section
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def get_parser_for_(meta_add=False, meta_find=False, search=False, settings=False):
        # TODO assign return type
        try:
            if meta_add:
                return parsers.metadata_added_parser
            if meta_find:
                return parsers.metadata_failed_parser
            if search:
                return parsers.search_parser
            if settings:
                return parsers.user_settings_parser
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @classmethod
    def get_parsers(cls) -> tuple:
        try:
            ma = cls.get_parser_for_(meta_add=True)
            mf = cls.get_parser_for_(meta_find=True)
            sp = cls.get_parser_for_(search=True)
            up = cls.get_parser_for_(settings=True)
            return ma, mf, sp, up
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @classmethod
    def get_result_metadata_at_key_(cls, key: str, result: dict):
        try:
            return int(result[key]) if _is_int_(result[key]) else result[key]
        except Exception as e_err:
            print(e_err.args[0])

    @staticmethod
    def get_search_parser_as_sortable() -> dict:
        try:
            parser = parsers.search_parser
            assert parser is not None, ml.log('no parser chosen!')
            parser_dict = dict()
            for section in parser.sections():
                parser_dict[section] = dict()
                for section_key in parser[section]:
                    parser_dict[section][section_key] = parser[section][section_key]
            return parser_dict
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    def is_search_key_provided_for_(self, section, regex=False, seed=False, size=False) -> bool:
        try:
            sp = self.get_parser_for_(search=True)[section]
            key = keyrings.search_parser_keyring
            if regex:
                has_regex = True if key.REGEX_FILENAME in sp else False
                return has_regex
            if seed:
                has_seed = True if key.MIN_SEED in sp else False
                return has_seed
            if size:
                has_size = True if key.SIZE_MIN_BYTES in sp or key.SIZE_MAX_BYTES in sp else False
                return has_size
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def read_parser_value_with_(key, section='DEFAULT', meta_add=False,
                                meta_find=False, search=True, settings=False) -> str:
        try:
            no_key, p_section = False, None
            if meta_add:
                assert section in parsers.metadata_added_parser, ml.log(f'meta_a section \'{section}\' not found')
                p_section = parsers.metadata_added_parser[section]
                assert key in p_section, ml.log(ml.log(f'metadata key \'{key}\' not found'))
            elif meta_find:
                assert section in parsers.metadata_failed_parser, ml.log(f'meta_f section \'{section}\' not found')
                p_section = parsers.metadata_failed_parser[section]
                assert key in p_section, ml.log(f'metadata key \'{key}\' not found')
            elif settings:
                if section != keyrings.user_config_parser_keyring.DEFAULT:
                    assert section in parsers.user_config_parser, ml.log(f'user config section \'{section}\' not found')
                p_section = parsers.user_config_parser[section]
                assert key in p_section, ml.log(f'user config key \'{key}\' not found')
            elif search:  # MUST be last since defaults true
                assert section in parsers.search_parser, ml.log(f'search detail section \'{section}\' not found')
                p_section = parsers.search_parser[section]
                if key == keyrings.search_parser_keyring.TERM and key not in p_section:
                    return section
            value = p_section[key]
            return value
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def reset_search_ids():
        try:
            parser = parsers.search_parser
            keys = keyrings.search_parser_keyring
            for section in parser.sections():
                ml.log(f'reset search id for section \'{section}\'')
                parser[section][keys.ID] = str(0)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def write_config_to_disk():
        ml.log('writing parser configurations to disk')
        try:
            parsers_dict = parsers.parsers_keyed_by_file_path
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
                    ml.log(f'parser update for {parser}')
                    ml.log(f'successfully written parser to disk at \'{parser_path}\'')
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def write_parser_section_with_key_(parser_key, value='', section='DEFAULT',
                                       mp=None, search=True, settings=False):
        try:
            p_section = None
            if mp:
                assert section in mp, ml.log(f'metadata parser section is being created \'{section}\'')
                p_section = mp[section]
            elif settings:
                assert section in parsers.user_config_parser, ml.log(f'user config section is being created \'{section}\'')
                p_section = parsers.user_config_parser[section]
            elif search:  # MUST be last as search defaults true
                assert section in parsers.search_parser, ml.log(f'search section is being created \'{section}\'')
                p_section = parsers.search_parser[section]
            p_section[parser_key] = str(value)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)


def _is_int_(value) -> bool:
    try:
        for char in list(str(value)):
            if char not in digits_or_sign:
                return False
        return True
    except Exception as e_err:
        print(e_err.args[0])
