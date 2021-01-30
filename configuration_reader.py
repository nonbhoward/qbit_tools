# TODO this should maybe be it's own repo/project, lots of potential for re-use
from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, remove, walk
from pathlib2 import Path
ml = MinimalLog()


##### ##### ##### ##### ##### ##### ##### ##### TIER 3 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class Config:  # Configuration.HardCoded.FileNames.Config
    def __init__(self):
        # project's configuration file names, cannot be changed without changing project structure
        self.metadata = 'metadata.cfg'
        self.search_details = 'search_details.cfg'
        self.user_config = 'user_configuration.cfg'


class APIStateKeys:  # Configuration.Parser.KeyRing.MetaDataKeys.APIStateKeys
    def __init__(self):
        # keys for the state machine, some from API responses, in memory, half can be changed
        self.CONCLUDED = 'concluded'  # this indicates that the search will not start again
        self.QUEUED = 'queued'  # this indicates that the search should be started soon
        self.RUNNING = 'Running'  # this is a web api status return value, indicates search is running
        self.STOPPED = 'Stopped'  # this is a web api status return value, indicates search is or has stopped


class MiscKeys:  # Configuration.Parser.KeyRing.MetaDataKeys.MiscKeys
    def __init__(self):
        # keys to label/organize
        self.EMPTY = ''
        self.RESET = 'reset'
        self.SEARCHES = 'searches'


class ParserKeys:  # Configuration.Parser.KeyRing.MetaDataKeys.ParserKeys
    def __init__(self):
        # keys for Configuration().parsers, can be changed
        # key for the DEFAULT section of all config parsers, cannot be changed
        self. DEFAULT = 'DEFAULT'
        # keys for reading & writing boolean values for all config parsers, cannot be changed
        self.NO = 'no'
        self.YES = 'yes'


class PauseKeys:  # Configuration.Parser.KeyRing.MetaDataKeys.PauseKeys
    def __init__(self):
        # keys for controlling pause_type
        self.ADD = 'add'
        self.MAIN_LOOP = 'loops'
        self.SEARCH = 'search'  # key with two uses, 1. controlling pause type, 2. keying parser
        self.STARTING = 'starting'


class SearchKeys:  # Configuration.Parser.KeyRing.MetaDataKeys.SearchKeys
    def __init__(self):
        # keys for reading & writing values for the search config parser's end reason key, can be changed
        self.REQUIRED_RESULTS_FOUND = 'required results found!'
        self.TIMED_OUT = 'search timed out!'


class MetaDataKeys:  # Configuration.Parser.KeyRing.MetaDataKeys
    def __init__(self):
        # keys for reading & writing metadata info
        # TODO get all of these keys from next debug run
        self.META_DEMAND = 'nbPeers'
        self.META_NAME = 'fileName'
        self.META_RESULTS = 'results'
        self.META_SUPPLY = 'nbSeeders'
        self.META_URL = 'fileurl'


class SearchDetailKeys:  # Configuration.Parser.KeyRing.SearchDetailKeys
    def __init__(self):
        # keys for reading & writing search details
        self.AVG_SEEDS = 'average_seed_count'
        self.EXPECTED_RESULT_COUNT = 'expected_search_result_count'
        self.FILENAME_REGEX = 'regex_filter_for_filename'
        self.LAST_READ = 'last_read'
        self.LAST_WRITE = 'last_write'
        self.MAX_SEARCH_ATTEMPTS = 'maximum_search_attempts'
        self.MIN_SEEDS = 'minimum_seeds'
        self.RESULTS_ADDED = 'results_added'
        self.RESULTS_REQUIRED = 'results_required'
        self.SEARCH_ATTEMPT_COUNT = 'search_attempt_count'
        self.SEARCH_ID = 'search_id'
        self.SEARCH_TERM = 'search_term'


class SearchStateKeys:  # Configuration.Parser.KeyRing.SearchStateKeys
    def __init__(self):
        # keys for the search details state machine on disk, can be changed
        self.SEARCH_CONCLUDED = 'search_concluded'
        self.SEARCH_QUEUED = 'search_queued'
        self.SEARCH_RUNNING = 'search_running'
        self.SEARCH_STOPPED = 'search_stopped'


class UserConfigKeys:  # Configuration.Parser.KeyRing.UserConfigKeys
    def __init__(self):
        # keys for reading & writing user configuration
        self.ADD_WAIT = 'seconds_to_wait_after_each_torrent_add_attempt'
        self.PRIORITY = 'metadata_priority'
        self.MAIN_LOOP_WAIT = 'seconds_to_wait_after_each_main_loop'
        self.OTHER_WAIT = 'seconds_to_wait_for_other_reason'
        self.SEARCH_CHECK_WAIT = 'seconds_to_wait_after_each_search_status_check'
        self.UNI_CHAR_COUNT = 'unicode_total_character_count'
        self.UNI_SHIFT = 'unicode_shift_offset_for_scrambling_results_cfg_file'


##### ##### ##### ##### ##### ##### ##### ##### TIER 2 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class DirectoryNames:  # Configuration.HardCoded.DirectoryNames
    def __init__(self):
        self.user_config_path = 'user_configuration'
        self.data_path = 'data_src'


class Extensions:  # Configuration.HardCoded.Extensions
    def __init__(self):
        self.config = '.cfg'


class FileNames:  # Configuration.HardCoded.FileNames
    def __init__(self):
        self.config = Config()


class KeyRing:  # Configuration.Parser.KeyRing
    def __init__(self):
        self.api_state_keys = APIStateKeys()
        self.metadata_keys = MetaDataKeys()
        self.misc_keys = MiscKeys()
        self.parser_keys = ParserKeys()
        self.pause_keys = PauseKeys()
        self.search_detail_keys = SearchDetailKeys()
        self.search_state_keys = SearchStateKeys()
        self.user_config_keys = UserConfigKeys()


class ParserNames:  # Configuration.Parser.ParserNames
    def __init__(self):
        # TODO unused for now, could be used to help organize Parsers()
        self.metadata = 'metadata'
        self.search = 'search'  # key with two uses, 1. controlling pause type, 2. keying parser TODO still true?
        self.user_config = 'user_config'


class Parsers:  # Configuration.Parser.Parsers
    def __init__(self, configuration):
        # TODO for now return as unsorted tuple, (sorted by found) which could be done better using ParserNames()
        self.metadata_parser, self.search_parser, self.user_config_parser = self._get_parsers_from_(configuration)

    @staticmethod
    def _get_parsers_from_(configuration) -> tuple:
        try:
            data_path = str(configuration.paths.data)
            user_config_path = str(configuration.paths.user_config)
            config_extension = configuration.hardcoded.extensions.config
            parser_paths = [data_path, user_config_path]
            parsers = list()
            for parser_path in parser_paths:
                for root, dirs, files in walk(parser_path):
                    for file in files:
                        if file.endswith(config_extension):
                            cp = ConfigParser()
                            cp.read(file)
                            parsers.append(cp)
            return * parsers,
        except Exception as e_err:
            ml.log_event(e_err, ml.ERROR)


##### ##### ##### ##### ##### ##### ##### ##### TIER 1 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class HardCoded:  # Configuration.HardCoded
    def __init__(self):
        self.file_names = FileNames()
        self.directory_names = DirectoryNames()
        self.extensions = Extensions()


class Parser:  # Configuration.Parser
    def __init__(self, configuration):
        self.parsers = Parsers(configuration)
        self.names = ParserNames()
        self.keys = KeyRing()


class Paths:  # Configuration.Paths
    def __init__(self, configuration):
        self.project = configuration._get_project_path()
        self.data = self._get_data_path_from_(configuration)
        self.user_config = self._get_user_config_path_from_(configuration)

    def _get_data_path_from_(path, configuration) -> Path:
        """
        :return: data path as path object
        """
        try:
            ml.log_event('get data path', event_completed=True)
            data_directory_name = configuration.hardcoded.directory_names.data_path
            return Path(path.project, data_directory_name)
        except OSError as o_err:
            ml.log_event(o_err, level=ml.ERROR)

    def _get_user_config_path_from_(path, configuration) -> Path:
        """
        :return: data path as path object
        """
        try:
            ml.log_event('get data path', event_completed=True)
            user_config_directory_name = configuration.hardcoded.directory_names.user_config_path
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
class Configuration:  # ROOT @ Configuration
    def __init__(self, parse_all_project_files=False):
        self.hardcoded = HardCoded()
        self.paths = Paths(self)
        if parse_all_project_files:
            self.files = ProjectFiles(self)
        self.parser = Parser(self)

    @staticmethod
    def _get_project_path() -> Path:
        try:
            return Path(getcwd())
        except OSError as o_err:
            ml.log_event(o_err)


def get_user_configuration() -> Configuration:  # this is the only export required?
    try:
        return Configuration()
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    cf = Configuration(parse_all_project_files=True)
    pass
else:
    ml = MinimalLog(__name__)
