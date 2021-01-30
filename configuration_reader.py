from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, remove, walk
from pathlib2 import Path
ml = MinimalLog(__name__)


class Paths:
    def __init__(self):
        # project directory names, cannot be changed
        self.CONFIG_PATH_DIR_NAME = 'user_configuration'
        self.DATA_PATH_DIR_NAME = 'data_src'


class ConfigFiles:
    def __init__(self):
        # project file names, cannot be changed
        self.METADATA_FILE_NAME = 'metadata.cfg'
        self.SEARCH_DETAILS_FILE_NAME = 'search_details.cfg'
        self.USER_CONFIG_FILE_NAME = 'user_configuration.cfg'


class PathKeys:
    def __init__(self):
        # keys for Configuration().paths, can be changed
        self.DATA_PATH = 'data_path'
        self.PROJECT_PATH = 'project_path'
        self.USER_CONFIG_PATH = 'user_config_path'


class ConfigFileKeys:
    def __init__(self):
        # keys for Configuration().files, can be changed
        self.PROJECT_FILES = 'project_files'
        self.USER_CONFIG_FILES = 'user_config_files'


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
        self.TIMED_OUT = 'timed out!'


class APIStateKeys:
    def __init__(self):
        # keys for the state machine, some from API responses, in memory, half can be changed
        self.QUEUED = 'queued'  # this indicates that the search should be started soon
        self.RUNNING = 'Running'  # this is a web api status return value, indicates search is running
        self.STOPPED = 'Stopped'  # this is a web api status return value, indicates search is or has stopped
        self.CONCLUDED = 'concluded'  # this indicates that the search will not start again


class SearchStateKeys:
    def __init__(self):
        # keys for the search details state machine on disk, can be changed
        self.SEARCH_QUEUED = 'search_queued'
        self.SEARCH_RUNNING = 'search_running'
        self.SEARCH_STOPPED = 'search_stopped'
        self.SEARCH_CONCLUDED = 'search_concluded'


class MetaDataKeys:
    def __init__(self):
        # keys for reading & writing metadata info
        # TODO get all of these keys from nextx debug run
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
            'path': Paths(),
            'file': ConfigFiles()
        }


class KeyRing:  # meta class
    def __init__(self):
        self.ring = {
            'path': PathKeys(),
            'config_file': ConfigFileKeys(),
            'parser': ParserKeys(),
            'search': SearchKeys(),
            'state': APIStateKeys(),
            'search_state': SearchStateKeys(),
            'metadata': MetaDataKeys(),
            'user_config': UserConfigKeys(),
            'search_detail': SearchDetailKeys(),
            'pause': PauseKeys(),
            'misc': MiscKeys()
        }


class Configuration:
    def __init__(self, clean_up=False):
        self.key = KeyRing()
        self.hardcoded = HardCoded()
        # set paths
        path_key = self.key.ring['path']
        self.paths = {
            path_key.PROJECT_PATH: _get_project_path(),
            path_key.DATA_PATH: _get_data_path(self),
            path_key.USER_CONFIG_PATH: _get_user_config_path(self)
        }
        # set expected config files
        config_key = self.key.ring['config']
        self.files = {
            config_key.USER_CONFIG_FILES: _get_expected_config_files_as_paths(self),
            config_key.PROJECT_FILES: _get_all_files_in_project_path()
        }
        # set parsers
        parser_key = self.key.ring['parser']
        hardcoded = self.hardcoded
        self.parsers = {
            parser_key.METADATA: _get_parser(hardcoded.property['file'].METADATA_FILE_NAME),
            parser_key.SEARCH: _get_parser(hardcoded.property['file'].SEARCH_DETAILS_FILE_NAME),
            parser_key.USER_CONFIG: _get_parser(hardcoded.property['file'].USER_CONFIG_FILE_NAME)
        }
        if clean_up:
            self.cleanup_project_path()

    def cleanup_project_path(self):
        try:
            hardcoded = self.hardcoded
            data_path_name = hardcoded.property['path'].DATA_PATH_DIR_NAME
            config_path_name = hardcoded.property['path'].CONFIG_PATH_DIR_NAME
            self._cleanup_path(Path(data_path_name))
            self._cleanup_path(Path(config_path_name))
            pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _cleanup_path(self, path_to_clean: Path):
        try:
            key = self.key
            files_in_path = _get_all_files_in_path(path_to_clean)
            for file in files_in_path:
                expected_config_file_names = key.ring['config'].USER_CONFIG_FILES
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


def _get_all_files_in_project_path():
    try:
        project_path, all_files = user_settings.config.project_path, list()
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
        return Path(_get_project_path(), configuration.hardcoded.property['path'].CONFIG_PATH_DIR_NAME)
    except OSError as o_err:
        ml.log_event(o_err)


def _get_data_path(configuration: Configuration) -> Path:
    """
    :return: data path as path object
    """
    try:
        ml.log_event('get data path', event_completed=True)
        return Path(_get_project_path(), configuration.hardcoded.property['path'].DATA_PATH_DIR_NAME)
    except OSError as o_err:
        ml.log_event(o_err)


def _get_expected_config_files_as_paths(configuration: Configuration) -> dict:
    """
    :return: built path from hardcoded filename
    """
    ml.log_event('get config files')
    try:
        # get project root path
        project_path = _get_project_path()
        configuration.hardcoded.property['path'].
        # get sub paths
        data_path = Path(project_path, configuration.hardcoded.property['path'].DATA_PATH_DIR_NAME)
        user_config_path = Path(project_path, configuration.hardcoded.property['path'].CONFIG_PATH_DIR_NAME)
        # get paths to config files
        metadata_fn = configuration.hardcoded.property['file'].METADATA_FILE_NAME
        search_detail_fn = configuration.hardcoded.property['file'].SEARCH_DETAILS_FILE_NAME
        user_config_fn = configuration.hardcoded.property['file'].USER_CONFIG_FILE_NAME
        config_files = {
            metadata_fn: Path(data_path, metadata_fn),
            search_detail_fn: Path(data_path, search_detail_fn),
            user_config_fn: Path(user_config_path, user_config_fn)
        }
        return config_files
    except OSError as o_err:
        ml.log_event(o_err)


def _get_parser(config_file_path) -> ConfigParser:
    try:
        parser = ConfigParser()
        parser.read(config_file_path)
        return parser
    except Exception as e_err:
        ml.log_event(e_err, ml.ERROR)


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


user_settings = UserSettings()  # fyi this is here because relies on the above functions


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
    pass  # i don't see why i would run this directly besides testing
else:
    user_settings = UserSettings()
