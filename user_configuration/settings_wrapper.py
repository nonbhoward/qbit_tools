from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, walk
from pathlib import Path
ml = MinimalLog(__name__)


##### ##### ##### ##### ##### ##### ##### ##### TIER 3 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class ConfigParserPathNames:  # Configuration.HardCoded.DirectoryNames.ConfigParserDirectoryNames
    # project's config directory names, cannot be changed without changing project structure
    def __init__(self):
        self.user_config_path_name = 'user_configuration'
        self.data_path_name = 'data_src'


class ConfigParserFileNames:  # Configuration.HardCoded.FileNames.ConfigParserFileNames
    # project's configuration file names, cannot be changed without changing project structure
    def __init__(self):
        self.metadata = 'metadata_history.cfg'
        self.search = 'search.cfg'
        self.user_settings = 'EDIT_SETTINGS_HERE.cfg'


class MetadataParserKeys:  # Configuration.HardCoded.KeyRing.MetaDataKeys
    def __init__(self):
        # default section name
        self.DEFAULT = 'DEFAULT'
        # keys for reading the SearchResultsDictionary containing the metadata in results['results']
        self.RESULT = 'results'  # don't delete this (again).. it is used in one spot..
        self.STATUS = 'status'
        self.TOTAL = 'total'
        # keys for reading & writing core metadata info
        self.DEMAND = 'nbLeechers'
        self.LINK = 'descrLink'
        self.NAME = 'fileName'
        self.SIZE = 'fileSize'
        self.SITE = 'siteUrl'
        self.SUPPLY = 'nbSeeders'
        self.URL = 'fileUrl'
        # translations to api


class SearchParserKeys:  # Configuration.HardCoded.KeyRing.SearchDetailKeys
    # keys for reading & writing search details
    def __init__(self):
        # meta elements
        time_last_read = 'time_last_read'
        time_last_searched = 'time_last_searched'
        time_last_written = 'time_last_written'
        self.DATETIME_ELEMENT_LIST = [time_last_read, time_last_searched, time_last_written]
        # FYI, ***FOR KEY REFERENCES ONLY*** trying to keep properties singular for predictability,
        # key strings can be plural or singular since they are never directly referenced
        self.AVG_SEED_COUNT = 'average_seed_count'
        self.DEFAULT = 'DEFAULT'
        self.EMPTY = ''
        self.EXPECTED_SEARCH_RESULT_COUNT = 'expected_search_result_count'
        self.ID = 'search_id'
        self.MAX_FILE_SIZE = 'max_file_size'  # TODO add
        self.MAX_SEARCH_ATTEMPT_COUNT = 'maximum_search_attempt_count'
        self.MIN_SEED = 'minimum_seed_count'
        self.RANK = 'search_rank'
        self.REGEX_FILTER_FOR_FILENAME = 'regex_filter_for_filename'  # TODO allow a list of tilers?
        self.RESET = 'reset'
        self.RESULTS_ADDED_COUNT = 'results_added_count'  # TODO can this trigger a conclude? untested
        self.RESULTS_COUNT = 'results_count'  # this relies on being in DEFAULTS or program errors?
        self.RESULTS_REQUIRED_COUNT = 'results_required_count'
        self.SEARCH_ATTEMPT_COUNT = 'search_attempt_count'
        self.SEARCH_STOPPED_REASON = 'search_stopped_reason'
        self.TERM = 'search_term'  # your search term
        self.TIME_LAST_READ = time_last_read
        self.TIME_LAST_SEARCHED = time_last_searched
        self.TIME_LAST_WRITTEN = time_last_written
        # search state keys, 'concluded' and 'queued' are arbitrary names and can be changed
        self.CONCLUDED = 'concluded'  # the search will not start again
        self.QUEUED = 'queued'  # the search is waiting to start
        # search state keys, **CANNOT BE CHANGED** as they are compared to the api return values
        self.RUNNING = 'Running'  # this is a web api status return value, search is running, needs time to finish
        self.STOPPED = 'Stopped'  # this is a web api status return value, search is stopped, will be processed
        # boolean state keys
        self.NO = 'no'  # ConfigParser equivalent of False
        self.YES = 'yes'  # ConfigParser equivalent of True
        # search stopped reasons
        self.REQUIRED_RESULT_COUNT_FOUND = 'required results found!'
        self.TIMED_OUT = 'search timed out!'


class UserConfigParserKeys:  # Configuration.HardCoded.KeyRing.UserConfigKeys
    def __init__(self):
        # keys for reading & writing user configuration
        self.DEFAULT = 'DEFAULT'
        self.UNI_MEMBER_COUNT = 'unicode_total_character_count'
        self.UNI_SHIFT = 'unicode_shift_offset_for_scrambling_metadata_parser'
        self.USER_PRIORITY = 'metadata_value_sort_priority'
        self.WAIT_FOR_MAIN_LOOP = 'seconds_to_wait_after_each_main_loop'
        self.WAIT_FOR_SEARCH_RESULT_ADD = 'seconds_to_wait_after_each_torrent_add_attempt'
        self.WAIT_FOR_SEARCH_STATUS_CHECK = 'seconds_to_wait_after_each_search_status_check'
        self.WAIT_FOR_USER = 'seconds_to_wait_to_allow_user_to_read_log'


##### ##### ##### ##### ##### ##### ##### ##### TIER 2 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class DirectoryNames:  # Configuration.HardCoded.DirectoryNames
    def __init__(self):
        self.config_parser_path_names = ConfigParserPathNames()


class Extensions:  # Configuration.HardCoded.Extensions
    def __init__(self):
        self.cfg = '.cfg'  # FIXME, reminder that delimiter in string could cause issues, test this


class FileNames:  # Configuration.HardCoded.FileNames
    def __init__(self):
        self.config_parser = ConfigParserFileNames()


class KeyRing:  # Configuration.HardCoded.KeyRing
    def __init__(self):
        self.metadata_parser_keyring = MetadataParserKeys()
        self.search_parser_keyring = SearchParserKeys()
        self.user_config_parser_keyring = UserConfigParserKeys()


class ParserPaths:  # Configuration.Parser.ParserPaths
    def __init__(self, configuration):
        self.metadata_parser_path = self.get_parser_paths_from_(configuration)

    @staticmethod
    def get_parser_paths_from_(configuration):
        try:
            print('todo? : ParserPaths().get_parser_paths_from_()')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


class Parsers:  # Configuration.Parser.Parsers
    def __init__(self, configuration):
        # TODO not scalable in the long term, will have to think about how to restructure this
        parser_paths = configuration.paths._get_parser_paths_from_(configuration)
        self.parsers_keyed_by_file_path = self.get_parsers_from_(parser_paths)
        self.metadata_parser = self.parsers_keyed_by_file_path[parser_paths[0]]
        self.search_parser = self.parsers_keyed_by_file_path[parser_paths[1]]
        self.user_settings_parser = self.parsers_keyed_by_file_path[parser_paths[2]]

    @staticmethod
    def get_parsers_from_(parser_paths) -> dict:
        try:
            parsers = dict()
            for parser_path in parser_paths:
                cp = ConfigParser()
                cp.read(parser_path)
                # TODO check to be sure this statement works as expected
                assert _parser_has_sections(cp), ml.log_event('fatal exception {} has no sections'.format(cp))
                parsers[parser_path] = cp
            return parsers
        except Exception as e_err:
            ml.log_event(e_err, ml.ERROR)


##### ##### ##### ##### ##### ##### ##### ##### TIER 1 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class HardCoded:  # Configuration.HardCoded
    def __init__(self):
        self.config_parser_filenames = ConfigParserFileNames
        self.filenames = FileNames()
        self.directory_names = DirectoryNames()
        self.extensions = Extensions()
        self.keys = KeyRing()


class Parser:  # Configuration.Parser
    def __init__(self, configuration):
        self.parser_paths = ParserPaths(configuration)
        self.parsers = Parsers(configuration)


class Paths:  # Configuration.Paths
    def __init__(self, configuration):
        self.project = configuration._get_project_path()
        self.data = self._get_data_path_from_(configuration)
        self.user_config = self._get_user_config_path_from_(configuration)
        self.metadata_parser, self.search_parser, self.user_config_parser = self._get_parser_paths_from_(configuration)

    def _get_data_path_from_(path, configuration) -> Path:
        """
        :return: data path as path object
        """
        try:
            data_directory_name = configuration.hardcoded.directory_names.config_parser_path_names.data_path_name
            ml.log_event('get data path for {}..'.format(data_directory_name))
            return Path(path.project, data_directory_name)
        except OSError as o_err:
            ml.log_event(o_err, level=ml.ERROR)

    def _get_parser_paths_from_(path, configuration) -> tuple:
        # TODO this is basically hardcoded, do this better but lower priority than bugs
        try:
            # data paths
            metadata_parser_path = Path(path.data, configuration.hardcoded.filenames.config_parser.metadata)
            search_details_path = Path(path.data, configuration.hardcoded.filenames.config_parser.search)
            # user config paths
            user_config_path = Path(path.user_config, configuration.hardcoded.filenames.config_parser.user_settings)
            # build and return
            parser_paths = [metadata_parser_path, search_details_path, user_config_path]
            return * parser_paths,
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_user_config_path_from_(path, configuration) -> Path:
        """
        :return: data path as path object
        """
        try:
            ml.log_event('get data path', event_completed=True)
            # user_config_directory_name = configuration.hardcoded.directory_names.user_config_path_name
            user_config_directory_name = \
                configuration.hardcoded.directory_names.config_parser_path_names.user_config_path_name
            return Path(path.project, user_config_directory_name)
        except OSError as o_err:
            ml.log_event(o_err, level=ml.ERROR)


class ProjectFiles:  # Configuration.ProjectFiles
    def __init__(self, configuration):
        # TODO could be nice to have a dict of files by extension instead of a list
        self.all_project_file_paths = self._get_all_files_in_project_path_using_(configuration)

    @staticmethod
    def _get_all_files_in_project_path_using_(configuration):
        try:
            project_path, all_files = configuration.paths.project, list()
            for root, dirs, files in walk(project_path):
                for file in files:
                    all_files.append(Path(root, file))
            return all_files
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


##### ##### ##### ##### ##### ##### ##### ###### TIER 0 CLASS ###### ##### ##### ##### ##### ##### ##### ######
class ConfigurationManager:  # ROOT @ Configuration
    def __init__(self, parse_all_project_files=False):  # FYI, module entry point is here
        self.hardcoded = HardCoded()  # lots of hardcoded "keys" and project properties/variables
        self.paths = Paths(self)  # relevant paths used to build the project
        if parse_all_project_files:
            self.files = ProjectFiles(self)  # a list of the Path object for every project file
        self.parser = Parser(self)  # all parsers containing parsed .cfg file data

    @staticmethod
    def _get_project_path() -> Path:
        try:
            return Path(getcwd())
        except OSError as o_err:
            ml.log_event(o_err)


def get_user_configuration(parse_all_project_files: bool) -> ConfigurationManager:  # this is the only export required?
    try:
        configuration = ConfigurationManager(parse_all_project_files)
        return configuration
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _parser_has_sections(configparser: ConfigParser) -> bool:
    try:
        if _parser_has_defaults(configparser):
            return True
        section_count = len(configparser.sections())
        ml.log_event('configparser {} has {} sections'.format(configparser, section_count))
        if section_count < 1:
            if _parser_able_to_read_write_(configparser):
                return True
            return False
        return True
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _parser_able_to_read_write_(configparser: ConfigParser) -> bool:
    try:
        parser_modified_test_sections = _parser_modify_test_sections(configparser)
        if parser_modified_test_sections:
            ml.log_event('parser {} is able tod modify sections, parser is valid'.format(configparser))
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _parser_has_defaults(configparser: ConfigParser) -> bool:
    try:
        if configparser.defaults() is not None:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _parser_modify_test_sections(configparser: ConfigParser) -> bool:
    # TODO function completely untested, has never needed to run.. maybe just learn to use pytest?
    try:
        parser_test_section = 'configparser self test header, can be deleted'
        if configparser.has_section(parser_test_section):
            configparser.remove_section(parser_test_section)
            if not configparser.has_section(parser_test_section):
                return True
        configparser.add_section(parser_test_section)
        if configparser.has_section(parser_test_section):
            configparser.remove_section(parser_test_section)
            if not configparser.has_section(parser_test_section):
                return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    cf = ConfigurationManager(parse_all_project_files=True)
    pass
else:
    ml = MinimalLog(__name__)
