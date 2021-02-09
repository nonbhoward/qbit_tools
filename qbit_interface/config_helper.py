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
        self.search_detail_parser = self.get_parser_for_(search_detail=True)
        self.user_config_parser = self.get_parser_for_(user_config=True)
        # parser keys
        self.metadata_keys = self.get_keyring_for_(metadata=True)
        self.search_detail_keys = self.get_keyring_for_(search_detail=True)
        self.user_config_keys = self.get_keyring_for_(user_config=True)

    def get_keyring_for_(self, metadata=False, search_detail=False, user_config=False):
        """
        :param metadata: flag for metadata parser
        :param search_detail: flag for search detail parser
        :param user_config: flag for user config parser
        :return: a keyring containing constants for the associated parser
        """
        try:
            if metadata:
                metadata_detail_keyring = self.config.hardcoded.keys.metadata_parser_keyring
                return metadata_detail_keyring
            if search_detail:
                search_parser_keyring = self.config.hardcoded.keys.search_parser_keyring
                return search_parser_keyring
            if user_config:
                user_config_keyring = self.config.hardcoded.keys.user_config_parser_keyring
                return user_config_keyring
            raise Exception('no keyring has been chosen')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)
            
    def get_parser_for_(self, metadata=False, search_detail=False, user_config=False) -> ConfigParser:
        try:
            if metadata:
                parser = self.config.parser.parsers.metadata_parser
                return parser
            if search_detail:
                parser = self.config.parser.parsers.search_detail_parser
                return parser
            if user_config:
                parser = self.config.parser.parsers.user_config_parser
                return parser
            raise Exception('no parser has been chosen')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_parser_as_sortable_(self, metadata=False, search_detail=False, user_config=False) -> dict:
        try:
            parser = None
            if metadata:
                parser = self.metadata_parser
            if search_detail:
                parser = self.search_detail_parser
            if user_config:
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

    def get_parser_at_section(self, section, metadata=False, search_detail=True, user_config=False) -> SectionProxy:
        try:
            assert isinstance(section, str), 'section is not a string'
            if metadata:
                assert section in self.metadata_parser, 'section not found in parser'
                parser_at_section = self.metadata_parser[section]
                return parser_at_section
            if search_detail:
                assert section in self.search_detail_parser, 'section not found in parser'
                parser_at_section = self.search_detail_parser[section]
                return parser_at_section
            if user_config:
                assert section in self.user_config_parser, 'section not found in parser'
                parser_at_section = self.user_config_parser[section]
                return parser_at_section
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def read_parser_value_with_(self, parser_key, section='DEFAULT', 
                                metadata=True, search_detail=False, user_config=False) -> str:
        try:
            if metadata:
                assert section in self.metadata_parser, 'metadata section not found'
                parser = self.metadata_parser[section]
                assert parser_key in parser, 'metadata key not found'
                value = parser[parser_key]
                return value
            if search_detail:
                assert section in self.search_detail_parser, 'search detail section not found'
                parser = self.search_detail_parser[section]
                assert parser_key in parser, 'search detail key not found'
                value = parser[parser_key]
                return value
            if user_config:
                assert section in self.user_config_parser, 'user config section not found'
                parser = self.user_config_parser
                assert parser_key in parser, 'user config key not found'
                value = parser[parser_key]
                return value
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def search_has_started_at_(self, section):
        """
        # TODO rework this or delete it
        """
        try:
            active_search_term = self.get_search_term_from_search_detail_parser_at_active_header()
            if active_search_term in self.active_search_ids.keys():
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_all_sections_from_parser_(self, metadata=False, search_detail=False, user_config=False) -> list:
        try:
            sections = list()
            if metadata:
                sections = self.metadata_parser.sections()
            if search_detail:
                sections = self.search_detail_parser.sections()
            if user_config:
                sections = self.user_config_parser.sections()
            assert len(sections) > 0, 'no sections found'
            return sections
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def write_config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            parsers_dict = self.config.parser.parsers.parsers_keyed_by_file_path
            search_detail_parser_keys = self.get_keyring_for_search_detail_parser()
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
                    ml.log_event('parser update for {}'.format(parser))
                    ml.log_event('successfully written parser to disk at \'{}\''.format(parser_path))
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def write_parser_value_with_(self, parser_key, value='', section='DEFAULT',
                                 metadata=True, search_detail=False, user_config=False) -> bool:
        try:
            if metadata:
                assert section in self.metadata_parser, 'metadata section not found'
                parser = self.metadata_parser[section]
                parser[parser_key] = str(value)
                return True
            if search_detail:
                assert section in self.search_detail_parser, 'search detail section not found'
                parser = self.search_detail_parser[section]
                parser[parser_key] = str(value)
                return True
            if user_config:
                assert section in self.user_config_parser, 'user config section not found'
                parser = self.user_config_parser
                parser[parser_key] = str(value)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)
