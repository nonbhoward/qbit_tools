from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, remove, walk
from pathlib2 import Path
CONFIG_FILE_NAMES = 'config_file_names'
DIRECTORY_NAMES = 'directory_names'


class HardcodedDirectoryNames:
    def __init__(self):
        # project's sub directory names, strings cannot be changed without changing project structure
        self.CONFIG_PATH_DIR_NAME = 'user_configuration'
        self.DATA_PATH_DIR_NAME = 'data_src'


class HardcodedConfigFileNames:
    def __init__(self):
        # project's configuration file names, cannot be changed without changing project structure
        self.METADATA_FILE_NAME = 'metadata.cfg'
        self.SEARCH_DETAILS_FILE_NAME = 'search_details.cfg'
        self.USER_CONFIG_FILE_NAME = 'user_configuration.cfg'


class DirectoryPathKeys:
    def __init__(self):
        # keys for sub paths in the project path
        self.DATA_PATH = 'data_path'
        self.PROJECT_PATH = 'project_path'
        self.USER_CONFIG_PATH = 'user_config_path'


class ProjectFilePathKeys:
    def __init__(self):
        # keys for project file group
        self.PROJECT_FILE_PATH = 'project_file_path'


class ConfigFilePathKeys:
    def __init__(self):
        # keys for config file group
        self.METADATA_FILE_PATH = 'metadata_file_path'
        self.USER_CONFIG_FILE_PATH = 'user_config_file_path'


class ParserKeys:
    def __init__(self):
        # keys for Configuration().parsers, can be changed
        self.METADATA = 'metadata'
        self.SEARCH = 'search'  # key with two uses, 1. controlling pause type, 2. keying parser
        self.USER_CONFIG = 'user_config'
        # key for the DEFAULT section of all config parsers, cannot be changed
        self. DEFAULT = 'DEFAULT'
        # keys for reading & writing boolean values for all config parsers, cannot be changed
        self.NO = 'no'
        self.YES = 'yes'


class SearchKeys:
    def __init__(self):
        # keys for reading & writing values for the search config parser's end reason key, can be changed
        self.REQUIRED_RESULTS_FOUND = 'required results found!'
        self.TIMED_OUT = 'search timed out!'


class APIStateKeys:
    def __init__(self):
        # keys for the state machine, some from API responses, in memory, half can be changed
        self.CONCLUDED = 'concluded'  # this indicates that the search will not start again
        self.QUEUED = 'queued'  # this indicates that the search should be started soon
        self.RUNNING = 'Running'  # this is a web api status return value, indicates search is running
        self.STOPPED = 'Stopped'  # this is a web api status return value, indicates search is or has stopped


class SearchStateKeys:
    def __init__(self):
        # keys for the search details state machine on disk, can be changed
        self.SEARCH_CONCLUDED = 'search_concluded'
        self.SEARCH_QUEUED = 'search_queued'
        self.SEARCH_RUNNING = 'search_running'
        self.SEARCH_STOPPED = 'search_stopped'


class MetaDataKeys:
    def __init__(self):
        # keys for reading & writing metadata info
        # TODO get all of these keys from next debug run
        self.META_DEMAND = 'nbPeers'
        self.META_NAME = 'fileName'
        self.META_RESULTS = 'results'
        self.META_SUPPLY = 'nbSeeders'
        self.META_URL = 'fileurl'


class UserConfigKeys:
    def __init__(self):
        # keys for reading & writing user configuration
        self.ADD_WAIT = 'seconds_to_wait_after_each_torrent_add_attempt'
        self.PRIORITY = 'metadata_priority'
        self.MAIN_LOOP_WAIT = 'seconds_to_wait_after_each_main_loop'
        self.OTHER_WAIT = 'seconds_to_wait_for_other_reason'
        self.SEARCH_CHECK_WAIT = 'seconds_to_wait_after_each_search_status_check'
        self.UNI_CHAR_COUNT = 'unicode_total_character_count'
        self.UNI_SHIFT = 'unicode_shift_offset_for_scrambling_results_cfg_file'


class SearchDetailKeys:
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


class PauseKeys:
    def __init__(self):
        # keys for controlling pause_type
        self.ADD = 'add'
        self.MAIN_LOOP = 'loops'
        self.SEARCH = 'search'  # key with two uses, 1. controlling pause type, 2. keying parser
        self.STARTING = 'starting'


class MiscKeys:
    def __init__(self):
        # keys to label/organize
        self.EMPTY = ''
        self.RESET = 'reset'
        self.SEARCHES = 'searches'


class HardCoded:  # meta class
    def __init__(self):
        self.property = {
            CONFIG_FILE_NAMES: HardcodedConfigFileNames(),
            DIRECTORY_NAMES: HardcodedDirectoryNames()
        }


# TODO would it be better to subclass/extend and avoid keys all-together?
class KeyNamesForKeyRing:
    def __init__(self):
        self.PROJECT_FILES = 'project_files'
        self.CONFIG_FILES = 'config_files'
        self.METADATA = 'metadata'
        self.MISC = 'misc'
        self.PARSER = 'parser'
        self.PATH = 'path'
        self.PAUSE = 'pause'
        self.SEARCH = 'search'
        self.SEARCH_STATE = 'search_state'
        self.STATE = 'state'
        self.SEARCH_DETAIL = 'search_detail'
        self.USER_CONFIG = 'user_config'


class KeyRing:  # meta class
    def __init__(self):
        self.names = KeyNamesForKeyRing()
        self.ring = {
            self.names.PROJECT_FILES: ProjectFilePathKeys(),
            self.names.CONFIG_FILES: ConfigFilePathKeys(),
            self.names.METADATA: MetaDataKeys(),
            self.names.MISC: MiscKeys(),
            self.names.PARSER: ParserKeys(),
            self.names.PATH: DirectoryPathKeys(),
            self.names.PAUSE: PauseKeys(),
            self.names.SEARCH: SearchKeys(),
            self.names.SEARCH_STATE: SearchStateKeys(),
            self.names.STATE: APIStateKeys(),
            self.names.SEARCH_DETAIL: SearchDetailKeys(),
            self.names.USER_CONFIG: UserConfigKeys(),
        }


class Configuration:
    def __init__(self, clean_up=False):
        self.key = KeyRing()
        key_names = self.key.names
        self.hardcoded = HardCoded()
        # set paths
        path_key = self.key.ring[key_names.PATH]
        self.project_path = {
            path_key.PROJECT_PATH: _get_project_path(),
        }
        self.config_paths = {
            path_key.DATA_PATH: _get_data_path(self),
            path_key.USER_CONFIG_PATH: _get_user_config_path(self)
        }
        # set expected config files
        project_files_key = self.key.ring[key_names.PROJECT_FILES]
        config_files_key = self.key.ring[key_names.CONFIG_FILES]
        self.project_file_path = {
            project_files_key.PROJECT_FILE_PATH: _get_all_files_in_project_path(self),
        }
        self.config_file_paths = {
            config_files_key.METADATA_FILE_PATH: _get_expected_metadata_file_as_paths_dict(self),
            config_files_key.USER_CONFIG_FILE_PATH: _get_expected_config_files_as_paths_dict(self)
        }
        # set parsers
        key_names = self.key.names
        parser_key = self.key.ring[key_names.PARSER]
        parser_file_paths = _get_parser_file_paths_as_dict(self)
        hardcoded = self.hardcoded
        metadata_config_file_name = hardcoded.property[key_names.CONFIG_FILES].METADATA_FILE_NAME
        metadata_config_file_path = parser_file_paths[metadata_config_file_name]
        self.parsers = {
            parser_key.METADATA: _get_parser(hardcoded.property[key_names.CONFIG_FILES].METADATA_FILE_NAME),
            parser_key.SEARCH: _get_parser(hardcoded.property[key_names.CONFIG_FILES].SEARCH_DETAILS_FILE_NAME),
            parser_key.USER_CONFIG: _get_parser(hardcoded.property[key_names.CONFIG_FILES].USER_CONFIG_FILE_NAME)
        }
        if clean_up:
            self.cleanup_project_path()

    def cleanup_project_path(self):
        try:
            hardcoded = self.hardcoded
            data_path_name = hardcoded.property[DIRECTORY_NAMES].DATA_PATH_DIR_NAME
            config_path_name = hardcoded.property[DIRECTORY_NAMES].CONFIG_PATH_DIR_NAME
            self._cleanup_path(Path(data_path_name))
            self._cleanup_path(Path(config_path_name))
            pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _cleanup_path(self, path_to_clean: Path):
        try:
            configuration = self
            files_in_path = _get_all_files_in_path(path_to_clean)
            for file in files_in_path:
                expected_config_file_names = _get_expected_config_files_as_paths_dict()
                if file not in expected_config_file_names:
                    remove(file)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


def _config_file_has_sections(config_parser) -> bool:
    ml.log_event('check if config for {} has sections'.format(config_parser), False)
    try:
        config_file_section_count = len(config_parser.sections())
        if config_file_section_count > 0:
            ml.log_event('check if config for {} has sections'.format(config_parser), True)
            return True
        ml.log_event('config file has no sections!'.format(config_parser), ml.WARNING, announce=True)
        return False
    except RuntimeError as r_err:
        ml.log_event('{}: configuration file has no sections'.format(r_err))


def _get_all_files_in_project_path(configuration: Configuration):
    try:
        path_key = configuration.key.ring['path']
        project_path, all_files = configuration.project_path[path_key.PROJECT_PATH], list()
        for root, dirs, files in walk(project_path):
            for file in files:
                all_files.append(Path(root, file))
        return all_files
    except Exception as e_err:
        ml.log_event(e_err)


def _get_user_config_path(configuration: Configuration) -> Path:
    """
    :return: data path as path object
    """
    try:
        ml.log_event('get data path', event_completed=True)
        return Path(_get_project_path(), configuration.hardcoded.property[DIRECTORY_NAMES].CONFIG_PATH_DIR_NAME)
    except OSError as o_err:
        ml.log_event(o_err)


def _get_data_path(configuration: Configuration) -> Path:
    """
    :return: data path as path object
    """
    try:
        ml.log_event('get data path', event_completed=True)
        return Path(_get_project_path(), configuration.hardcoded.property[DIRECTORY_NAMES].DATA_PATH_DIR_NAME)
    except OSError as o_err:
        ml.log_event(o_err)


def _get_expected_config_files_as_paths_dict(configuration: Configuration) -> dict:
    ml.log_event('get config files')
    try:
        # get project root path
        path_key = configuration.key
        project_path = configuration.project_path[path_key.ring['path'].PROJECT_PATH]
        # get sub paths
        data_path = Path(project_path, configuration.hardcoded.property[DIRECTORY_NAMES].DATA_PATH_DIR_NAME)
        user_config_path = Path(project_path, configuration.hardcoded.property[DIRECTORY_NAMES].CONFIG_PATH_DIR_NAME)
        # get paths to config files
        search_detail_fn = configuration.hardcoded.property[CONFIG_FILE_NAMES].SEARCH_DETAILS_FILE_NAME
        user_config_fn = configuration.hardcoded.property[CONFIG_FILE_NAMES].USER_CONFIG_FILE_NAME
        config_files = {
            search_detail_fn: Path(data_path, search_detail_fn),
            user_config_fn: Path(user_config_path, user_config_fn)
        }
        return config_files
    except OSError as o_err:
        ml.log_event(o_err)


def _get_expected_metadata_file_as_paths_dict(configuration: Configuration) -> dict:
    ml.log_event('get config files')
    try:
        # get project root path
        path_key = configuration.key
        project_path = configuration.project_path[path_key.ring['path'].PROJECT_PATH]
        # get sub paths
        data_path = Path(project_path, configuration.hardcoded.property[DIRECTORY_NAMES].DATA_PATH_DIR_NAME)
        # get paths to metadata file
        metadata_fn = configuration.hardcoded.property[CONFIG_FILE_NAMES].METADATA_FILE_NAME
        metadata_file = {
            metadata_fn: Path(data_path, metadata_fn),
        }
        return metadata_file
    except OSError as o_err:
        ml.log_event(o_err)


def _get_parser(config_file_path) -> ConfigParser:
    try:
        parser = ConfigParser()
        parser.read(config_file_path)
        return parser
    except Exception as e_err:
        ml.log_event(e_err, ml.ERROR)


def _get_parser_file_paths_as_dict(configuration: Configuration) -> dict:
    try:
        key, key_names = configuration.key, configuration.key.names
        parser_file_paths_dict = dict()
        config_file_paths = configuration.config_file_paths
        for file_path_key, file_path_dict in config_file_paths.items():
            for file_name, file_path in file_path_dict.items():
                parser_file_paths_dict[file_name] = file_path
                # TODO NOW get the project files
        return parser_file_paths_dict
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _get_project_path() -> Path:
    try:
        return Path(getcwd())
    except OSError as o_err:
        ml.log_event(o_err)


def _parser_is_ready() -> tuple:
    ml.log_event('check if parser is ready', event_completed=False)
    try:
        parser = ConfigParser()
        ml.log_event('check if parser is ready', event_completed=True)
        if parser is not None:
            return True, parser
        return False, parser
    except OSError as o_err:
        ml.log_event(o_err, level=ml.ERROR)


# user_settings = UserSettings()  # fyi this is here because relies on the above functions


def _get_all_files_in_path(path_containing_files: Path) -> list:
    try:
        all_files = list()
        for root, dirs, files in walk(path_containing_files):
            for file in files:
                all_files.append(Path(root, file))
        return all_files
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def get_user_configuration() -> Configuration:
    try:
        return Configuration()
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    cf = Configuration(clean_up=True)
    pass
else:
    ml = MinimalLog(__name__)
