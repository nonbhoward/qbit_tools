from configparser import RawConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, walk
from pathlib import Path
ml = MinimalLog(__name__)


##### ##### ##### ##### ##### ##### ##### ##### TIER 3 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class ConfigParserPathNames:  # Configuration.HardCoded.DirectoryNames.ConfigParserDirectoryNames
    # project's config directory names, cannot be changed without changing project structure
    def __init__(self):
        try:
            self.user_config_path_name = 'user_configuration'
            self.metadata_path_name = 'data_meta'
            self.search_data_path_name = 'data_search'
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class ConfigParserFileNames:  # Configuration.HardCoded.FileNames.ConfigParserFileNames
    # project's configuration file names, cannot be changed without changing project structure
    def __init__(self):
        try:
            self.metadata_added = 'metadata_added.cfg'
            self.metadata_failed = 'metadata_failed.cfg'
            self.search = 'search.cfg'
            self.user_settings = 'EDIT_SETTINGS_HERE.cfg'
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class MetadataParserKeys:  # Configuration.HardCoded.KeyRing.MetaDataKeys
    def __init__(self):
        try:
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
            self.RESULTS = 'results'
            self.SIZE = 'fileSize'
            self.SITE = 'siteUrl'
            self.SUPPLY = 'nbSeeders'
            self.URL = 'fileUrl'
            # translations to api
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class SearchParserKeys:  # Configuration.HardCoded.KeyRing.SearchDetailKeys
    # keys for reading & writing search details
    def __init__(self):
        try:
            self.ADD_PAUSED = 'add_paused'
            self.AVG_SEED_COUNT = 'average_seed_count'
            self.DEFAULT = 'DEFAULT'
            self.EMPTY = ''
            self.ID = 'search_id'
            self.MAX_SEARCH_COUNT = 'maximum_search_attempt_count'
            self.MIN_SEED = 'minimum_seed_count'
            self.RANK = 'search_rank'
            self.REGEX_FILENAME = 'regex_filter_for_filename'  # TODO allow a list of tilers?
            self.RESET = 'reset'
            self.RESULTS_ADDED_COUNT = 'results_added_count'  # TODO can this trigger a conclude? untested
            self.RESULTS_COUNT = 'results_count'  # this relies on being in DEFAULTS or program errors?
            self.RESULTS_REQUIRED_COUNT = 'results_required_count'
            self.SEARCH_ATTEMPT_COUNT = 'search_attempt_count'
            self.SEARCH_STOPPED_REASON = 'search_stopped_reason'
            self.SIZE_MAX_BYTES = 'maximum_file_size_bytes'
            self.SIZE_MIN_BYTES = 'minimum_file_size_bytes'
            self.TERM = 'search_term'  # your search term
            self.TIME_LAST_READ = 'time_last_read'
            self.TIME_LAST_SEARCHED = 'time_last_searched'
            self.TIME_LAST_WRITTEN = 'time_last_written'
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
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class UserConfigParserKeys:  # Configuration.HardCoded.KeyRing.UserConfigKeys
    def __init__(self):
        try:
            # keys for reading & writing user configuration
            self.DEFAULT = 'DEFAULT'
            self.RANK_REQUIRED = 'search_rank_required_to_start'
            self.UNI_MEMBER_COUNT = 'unicode_total_character_count'
            self.UNI_SHIFT = 'unicode_shift_offset_for_scrambling_metadata_parser'
            self.USER_PRIORITY = 'metadata_value_sort_priority'
            self.WAIT_FOR_MAIN_LOOP = 'seconds_to_wait_after_each_main_loop'
            self.WAIT_FOR_SEARCH_RESULT_ADD = 'seconds_to_wait_after_each_torrent_add_attempt'
            self.WAIT_FOR_SEARCH_STATUS_CHECK = 'seconds_to_wait_after_each_search_status_check'
            self.WAIT_FOR_USER = 'seconds_to_wait_to_allow_user_to_read_log'
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


##### ##### ##### ##### ##### ##### ##### ##### TIER 2 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class DirectoryNames:  # Configuration.HardCoded.DirectoryNames
    def __init__(self):
        try:
            self.config_parser_path_names = ConfigParserPathNames()
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class Extensions:  # Configuration.HardCoded.Extensions
    def __init__(self):
        try:
            self.cfg = '.cfg'  # FIXME, reminder that delimiter in string could cause issues, test this
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class FileNames:  # Configuration.HardCoded.FileNames
    def __init__(self):
        try:
            self.config_parser = ConfigParserFileNames()
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class KeyRing:  # Configuration.HardCoded.KeyRing
    def __init__(self):
        try:
            self.metadata_parser_keyring = MetadataParserKeys()
            self.search_parser_keyring = SearchParserKeys()
            self.user_config_parser_keyring = UserConfigParserKeys()
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class ParserPaths:  # Configuration.Parser.ParserPaths
    def __init__(self, configuration):
        try:
            self.metadata_parser_path = self.get_parser_paths_from_(configuration)
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def get_parser_paths_from_(configuration):
        try:
            print('todo? : ParserPaths().get_parser_paths_from_()')
        except Exception as e_err:
            ml.log_event(f'error getting parser paths from \'{configuration}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class Parsers:  # Configuration.Parser.Parsers
    def __init__(self, configuration):
        try:
            # TODO not scalable in the long term, will have to think about how to restructure this
            parser_paths = configuration.paths._get_parser_paths_from_(configuration)
            self.parsers_keyed_by_file_path = self.get_parsers_from_(parser_paths)
            self.metadata_added_parser = self.parsers_keyed_by_file_path[parser_paths[0]]
            self.metadata_failed_parser = self.parsers_keyed_by_file_path[parser_paths[1]]
            self.search_parser = self.parsers_keyed_by_file_path[parser_paths[2]]
            self.user_settings_parser = self.parsers_keyed_by_file_path[parser_paths[3]]
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def get_parsers_from_(parser_paths) -> dict:
        try:
            parser_path = ''
            parsers = dict()
            for parser_path in parser_paths:
                rcp = RawConfigParser()
                rcp.read(parser_path)
                # TODO check to be sure this statement works as expected
                assert _parser_has_sections(rcp), ml.log_event('fatal exception {} has no sections'.format(rcp))
                parsers[parser_path] = rcp
            return parsers
        except Exception as e_err:
            ml.log_event(f'error getting parsers from \'{parser_path}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], ml.ERROR)


##### ##### ##### ##### ##### ##### ##### ##### TIER 1 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class HardCoded:  # Configuration.HardCoded
    def __init__(self):
        try:
            self.config_parser_filenames = ConfigParserFileNames
            self.filenames = FileNames()
            self.directory_names = DirectoryNames()
            self.extensions = Extensions()
            self.keys = KeyRing()
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class Parser:  # Configuration.Parser
    def __init__(self, configuration):
        try:
            self.parser_paths = ParserPaths(configuration)
            self.parsers = Parsers(configuration)
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


class Paths:  # Configuration.Paths
    def __init__(self, configuration):
        try:
            self.project = configuration._get_project_path()
            self.meta = self._get_meta_path_from(configuration)
            self.search = self._get_search_path_from(configuration)
            self.user_config = self._get_user_config_path_from_(configuration)
            self.metadata_added_parser, self.metadata_failed_parser, \
                self.search_parser, self.user_config_parser = \
                self._get_parser_paths_from_(configuration)
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def _get_meta_path_from(path, configuration) -> Path:
        """
        :return: meta path as path object
        """
        try:
            meta_directory_name = configuration.hardcoded.directory_names.config_parser_path_names.metadata_path_name
            ml.log_event(f'get metadata path for {meta_directory_name}')
            return Path(path.project, meta_directory_name)
        except Exception as e_err:
            ml.log_event(f'error getting meta path from \'{configuration}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def _get_search_path_from(path, configuration) -> Path:
        """
        :return: search path as path object
        """
        try:
            search_directory_name = configuration.hardcoded.directory_names.config_parser_path_names.search_data_path_name
            ml.log_event(f'get data path for {search_directory_name}..')
            return Path(path.project, search_directory_name)
        except OSError as o_err:
            ml.log_event(f'error getting search path from \'{configuration}\'', level=ml.ERROR)
            ml.log_event(o_err, level=ml.ERROR)

    def _get_parser_paths_from_(path, configuration) -> tuple:
        # TODO this is basically hardcoded, do this better but lower priority than bugs
        try:
            # result metadata parsers
            meta_added_parser_path = Path(path.meta, configuration.hardcoded.filenames.config_parser.metadata_added)
            meta_failed_parser_path = Path(path.meta, configuration.hardcoded.filenames.config_parser.metadata_failed)
            # search parser
            search_details_path = Path(path.search, configuration.hardcoded.filenames.config_parser.search)
            # user config parser
            user_config_path = Path(path.user_config, configuration.hardcoded.filenames.config_parser.user_settings)
            # build and return
            parser_paths = [meta_added_parser_path, meta_failed_parser_path, search_details_path, user_config_path]
            return * parser_paths,
        except Exception as e_err:
            ml.log_event(f'error getting parser paths from \'{configuration}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def _get_user_config_path_from_(path, configuration) -> Path:
        """
        :return: data path as path object
        """
        try:
            ml.log_event('get data path', event_completed=True)
            user_config_directory_name = \
                configuration.hardcoded.directory_names.config_parser_path_names.user_config_path_name
            return Path(path.project, user_config_directory_name)
        except OSError as o_err:
            ml.log_event(f'error getting user config path from \'{configuration}\'', level=ml.ERROR)
            ml.log_event(o_err, level=ml.ERROR)


class ProjectFiles:  # Configuration.ProjectFiles
    def __init__(self, configuration):
        try:
            # TODO could be nice to have a dict of files by extension instead of a list
            self.all_project_file_paths = self._get_all_files_in_project_path_using_(configuration)
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def _get_all_files_in_project_path_using_(configuration):
        try:
            project_path, all_files = configuration.paths.project, list()
            for root, dirs, files in walk(project_path):
                for file in files:
                    all_files.append(Path(root, file))
            return all_files
        except Exception as e_err:
            ml.log_event(f'error getting all files in project path using \'{configuration}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


##### ##### ##### ##### ##### ##### ##### ###### TIER 0 CLASS ###### ##### ##### ##### ##### ##### ##### ######
class ConfigurationManager:  # ROOT @ Configuration
    def __init__(self, parse_all_project_files=False):  # FYI, module entry point is here
        try:
            self.hardcoded = HardCoded()  # lots of hardcoded "keys" and project properties/variables
            self.paths = Paths(self)  # relevant paths used to build the project
            if parse_all_project_files:
                self.files = ProjectFiles(self)  # a list of the Path object for every project file
            self.parser = Parser(self)  # all parsers containing parsed .cfg file data
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def _get_project_path() -> Path:
        try:
            return Path(getcwd())
        except OSError as o_err:
            ml.log_event(f'error getting project path from \'{getcwd()}\'', level=ml.ERROR)
            ml.log_event(o_err.args[0], level=ml.ERROR)


def get_user_configuration(parse_all_project_files=False) -> ConfigurationManager:  # this is the only export required?
    try:
        configuration = ConfigurationManager(parse_all_project_files)
        return configuration
    except Exception as e_err:
        ml.log_event(f'error getting user configuration', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _parser_has_sections(raw_config_parser: RawConfigParser) -> bool:
    try:
        if _parser_has_defaults(raw_config_parser):
            return True
        section_count = len(raw_config_parser.sections())
        ml.log_event(f'configparser {raw_config_parser} has {section_count} sections')
        if section_count < 1:
            if _parser_able_to_read_write_(raw_config_parser):
                return True
            return False
        return True
    except Exception as e_err:
        ml.log_event(f'error checking if parser \'{raw_config_parser}\' has sections', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _parser_able_to_read_write_(raw_config_parser: RawConfigParser) -> bool:
    try:
        parser_modified_test_sections = _parser_modify_test_sections(raw_config_parser)
        if parser_modified_test_sections:
            ml.log_event(f'parser {raw_config_parser} is able tod modify sections, parser is valid')
            return True
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if parser able to read/write to \'{raw_config_parser}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _parser_has_defaults(raw_config_parser: RawConfigParser) -> bool:
    try:
        if raw_config_parser.defaults() is not None:
            return True
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if parser \'{raw_config_parser}\' has defaults', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _parser_modify_test_sections(raw_config_parser: RawConfigParser) -> bool:
    # TODO function completely untested, has never needed to run.. maybe just learn to use pytest?
    try:
        parser_test_section = 'configparser self test header, can be deleted'
        if raw_config_parser.has_section(parser_test_section):
            raw_config_parser.remove_section(parser_test_section)
            if not raw_config_parser.has_section(parser_test_section):
                return True
        raw_config_parser.add_section(parser_test_section)
        if raw_config_parser.has_section(parser_test_section):
            raw_config_parser.remove_section(parser_test_section)
            if not raw_config_parser.has_section(parser_test_section):
                return True
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if parser \'{raw_config_parser}\' sections can be modified', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    cf = ConfigurationManager(parse_all_project_files=True)
    pass
else:
    ml = MinimalLog(__name__)
