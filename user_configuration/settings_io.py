from configparser import ConfigParser
from configparser import SectionProxy
from minimalog.minimal_log import MinimalLog
from user_configuration.settings_wrapper import get_user_configuration
ml = MinimalLog()


class QbitConfig:
    def __init__(self):
        self.config = get_user_configuration()
        # parsers
        self.metadata_parser = self.get_parser_for_(metadata=True)
        self.search_settings_and_status = self.get_parser_for_(search=True)
        self.user_config_parser = self.get_parser_for_(settings=True)
        # parser keys
        self.metadata_keys = self.get_keyring_for_(metadata=True)
        self.search_detail_keys = self.get_keyring_for_(search=True)
        self.settings = self.get_keyring_for_(settings=True)

    def get_all_sections_from_parser_(self, metadata=False, search=False, settings=False) -> list:
        try:
            sections = list()
            if metadata:
                sections = self.metadata_parser.sections()
            if search:
                sections = self.search_settings_and_status.sections()
            if settings:
                sections = self.user_config_parser.sections()
            assert len(sections) > 0, 'no sections found'
            return sections
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_keyring_for_(self, metadata=False, search=False, settings=False):
        """
        :param metadata: flag for metadata parser
        :param search: flag for search detail parser
        :param settings: flag for user config parser
        :return: a keyring containing constants for the associated parser
        """
        try:
            if metadata:
                metadata_detail_keyring = self.config.hardcoded.keys.metadata_parser_keyring
                return metadata_detail_keyring
            if search:
                search_parser_keyring = self.config.hardcoded.keys.search_parser_keyring
                return search_parser_keyring
            if settings:
                user_config_keyring = self.config.hardcoded.keys.user_config_parser_keyring
                return user_config_keyring
            raise Exception('no keyring has been chosen')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)
            
    def get_parser_as_sortable_(self, metadata=False, search=False, settings=False) -> dict:
        try:
            parser = None
            if metadata:
                parser = self.metadata_parser
            if search:
                parser = self.search_settings_and_status
            if settings:
                parser = self.user_config_parser
            assert parser is not None, 'no parser chosen!'
            parser_dict = dict()
            for section in parser.sections():
                parser_dict[section] = dict()
                for section_key in parser[section]:
                    parser_dict[section][section_key] = parser[section][section_key]
            return parser_dict
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_parser_at_section(self, section, metadata=False, search=True, settings=False) -> SectionProxy:
        try:
            assert isinstance(section, str), 'section is not a string'
            if metadata:
                assert section in self.metadata_parser, 'section not found in parser'
                parser_at_section = self.metadata_parser[section]
                return parser_at_section
            if search:
                assert section in self.search_settings_and_status, 'section not found in parser'
                parser_at_section = self.search_settings_and_status[section]
                return parser_at_section
            if settings:
                assert section in self.user_config_parser, 'section not found in parser'
                parser_at_section = self.user_config_parser[section]
                return parser_at_section
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_parser_for_(self, metadata=False, search=False, settings=False) -> ConfigParser:
        try:
            if metadata:
                parser = self.config.parser.parsers.metadata_parser
                return parser
            if search:
                parser = self.config.parser.parsers.search_settings_and_status
                return parser
            if settings:
                parser = self.config.parser.parsers.user_settings_parser
                return parser
            raise Exception('no parser has been chosen')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def read_parser_value_with_(self, key, section='DEFAULT',
                                metadata=False, search=False, settings=False) -> str:
        try:
            parser = None
            if metadata:
                assert section in self.metadata_parser, 'metadata section not found'
                parser = self.metadata_parser[section]
                assert key in parser, 'metadata key not found'
            if search:
                assert section in self.search_settings_and_status, 'search detail section not found'
                parser = self.search_settings_and_status[section]
                assert key in parser, 'search detail key not found'
            if settings:
                assert section in self.user_config_parser, 'user config section not found'
                parser = self.user_config_parser[section]
                assert key in parser, 'user config key not found'
            value = parser[key]
            return value
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def reset_search_ids(self):
        try:
            parser = self.search_settings_and_status
            keys = self.search_detail_keys
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
            parser = self.search_settings_and_status
            search = self.search_detail_keys
            sdp_as_dict = self.get_parser_as_sortable_(search=True)
            sdp_as_dict_sorted = sorted(sdp_as_dict.items(), key=lambda k: k[1][sort_key])
            number_of_sections = len(sdp_as_dict_sorted)
            for search_rank in range(number_of_sections):
                header = sdp_as_dict_sorted[search_rank][0]
                parser[header][search.RANK] = str(search_rank)
                ml.log_event(f'search rank \'{search_rank}\' assigned to header \'{header}\'')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def write_config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            parsers_dict = self.config.parser.parsers.parsers_keyed_by_file_path
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
                    ml.log_event(f'parser update for {parser}')
                    ml.log_event(f'successfully written parser to disk at \'{parser_path}\'')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def write_parser_value_with_key_(self, parser_key, value='', section='DEFAULT',
                                     metadata=False, search=False, settings=False) -> bool:
        try:
            if metadata:
                assert section in self.metadata_parser, 'metadata section not found'
                parser = self.metadata_parser[section]
                parser[parser_key] = str(value)
                return True
            if search:
                assert section in self.search_settings_and_status, 'search detail section not found'
                parser = self.search_settings_and_status[section]
                parser[parser_key] = str(value)
                return True
            if settings:
                assert section in self.user_config_parser, 'user config section not found'
                parser = self.user_config_parser
                parser[parser_key] = str(value)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)
