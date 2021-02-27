from configparser import SectionProxy
from minimalog.minimal_log import MinimalLog
from user_configuration.settings_wrapper import get_user_configuration
ml = MinimalLog()
uconf = get_user_configuration()
parsers = uconf.parser.parsers
keyrings = uconf.hardcoded.keys


class QbitConfig:
    @staticmethod
    def get_all_sections_from_parser_(metadata=False, search=False, settings=False) -> SectionProxy:
        try:
            if metadata:
                return parsers.metadata_parser.sections()
            if search:
                return parsers.search_parser.sections()
            if settings:
                return parsers.user_settings_parser.sections()
            pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def get_keyring_for_(metadata=False, search=False, settings=False):
        # TODO assign return type
        try:
            if metadata:
                return keyrings.metadata_parser_keyring
            if search:
                return keyrings.search_parser_keyring
            if settings:
                return keyrings.user_config_parser_keyring
            pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @classmethod
    def get_keyrings(cls) -> tuple:
        try:
            mk = cls.get_keyring_for_(metadata=True)
            sk = cls.get_keyring_for_(search=True)
            uk = cls.get_keyring_for_(settings=True)
            return mk, sk, uk
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def get_parser_as_sortable_(metadata=False, search=False, settings=False) -> dict:
        try:
            parser = None
            if metadata:
                parser = parsers.metadata_parser
            if search:
                parser = parsers.search_parser
            if settings:
                parser = parsers.user_settings_parser
            assert parser is not None, 'no parser chosen!'
            parser_dict = dict()
            for section in parser.sections():
                parser_dict[section] = dict()
                for section_key in parser[section]:
                    parser_dict[section][section_key] = parser[section][section_key]
            return parser_dict
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def get_parser_at_section(section, metadata=False, search=True, settings=False) -> SectionProxy:
        try:
            assert isinstance(section, str), 'section is not a string'
            if metadata:
                mp = parsers.metadata_parser
                assert section in mp, 'section not found in parser'
                parser_at_section = mp[section]
                return parser_at_section
            if search:
                sp = parsers.search_parser
                assert section in sp, 'section not found in parser'
                parser_at_section = sp[section]
                return parser_at_section
            if settings:
                ucp = parsers.user_settings_parser
                assert section in ucp, 'section not found in parser'
                parser_at_section = ucp[section]
                return parser_at_section
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def get_parser_for_(metadata=False, search=False, settings=False):
        # TODO assign return type
        try:
            if metadata:
                return parsers.metadata_parser
            if search:
                return parsers.search_parser
            if settings:
                return parsers.user_settings_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @classmethod
    def get_parsers(cls) -> tuple:
        try:
            mp = cls.get_parser_for_(metadata=True)
            sp = cls.get_parser_for_(search=True)
            up = cls.get_parser_for_(settings=True)
            return mp, sp, up
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def read_parser_value_with_(key, section='DEFAULT',
                                metadata=False, search=False, settings=False) -> str:
        try:
            parser = None
            if metadata:
                assert section in parsers.metadata_parser, 'metadata section not found'
                parser = parsers.metadata_parser[section]
                assert key in parser, 'metadata key not found'
            if search:
                assert section in parsers.search_parser, 'search detail section not found'
                parser = parsers.search_parser[section]
                if key == keyrings.search_parser_keyring.TERM and key not in parser:
                    return section
                assert key in parser, 'search detail key not found'
            if settings:
                assert section in parsers.user_config_parser, 'user config section not found'
                parser = parsers.user_config_parser[section]
                assert key in parser, 'user config key not found'
            value = parser[key]
            return value
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def reset_search_ids():
        try:
            parser = parsers.search_parser
            keys = keyrings.search_parser_keyring
            for section in parser.sections():
                ml.log_event(f'reset search id for section \'{section}\'')
                parser[section][keys.ID] = str(0)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def set_search_rank_using_(self, sort_key):
        """
        1. sort the key:value pair of the dict into a tuple of 2 (key, value), sorted by sort_key's value
        2. assign a search rank to each search header based on previous sort
        3. write the search rank to the search detail parser
        :param sort_key:
        :return:
        """
        try:
            parser = parsers.search_parser
            search = keyrings.search_parser_keyring
            sdp_as_dict = self.get_parser_as_sortable_(search=True)
            sdp_as_dict_sorted = sorted(sdp_as_dict.items(), key=lambda k: k[1][sort_key])
            number_of_sections = len(sdp_as_dict_sorted)
            for search_rank in range(number_of_sections):
                header = sdp_as_dict_sorted[search_rank][0]
                parser[header][search.RANK] = str(search_rank)
                ml.log_event(f'search rank \'{search_rank}\' assigned to header \'{header}\'')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def write_config_to_disk():
        ml.log_event('writing parser configurations to disk')
        try:
            parsers_dict = parsers.parsers_keyed_by_file_path
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
                    ml.log_event(f'parser update for {parser}')
                    ml.log_event(f'successfully written parser to disk at \'{parser_path}\'')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def write_parser_value_with_key_(parser_key, value='', section='DEFAULT',
                                     metadata=False, search=False, settings=False) -> bool:
        try:
            if metadata:
                assert section in parsers.metadata_parser, 'metadata section not found'
                parser = parsers.metadata_parser[section]
                parser[parser_key] = str(value)
                return True
            if search:
                assert section in parsers.search_parser, 'search detail section not found'
                parser = parsers.search_parser[section]
                parser[parser_key] = str(value)
                return True
            if settings:
                assert section in parsers.user_config_parser, 'user config section not found'
                parser = parsers.user_config_parser
                parser[parser_key] = str(value)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)
