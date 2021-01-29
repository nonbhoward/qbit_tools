from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, remove, walk
from pathlib2 import Path
ml = MinimalLog(__name__)
# project directory names, cannot be changed
CONFIG_PATH_DIR_NAME = 'user_configuration'
DATA_PATH_DIR_NAME = 'data_src'
# project file names, cannot be changed
METADATA_FILE_NAME = 'metadata.cfg'
SEARCH_DETAILS_FILE_NAME = 'search_details.cfg'
USER_CONFIG_FILE_NAME = 'user_configuration.cfg'
# keys for Configuration().paths, can be changed
DATA_PATH = 'data_path'
PROJECT_PATH = 'project_path'
USER_CONFIG_PATH = 'user_config_path'
# keys for Configuration().files, can be changed
PROJECT_FILES = 'project_files'
USER_CONFIG_FILES = 'user_config_files'
# keys for Configuration().parsers, can be changed
METADATA = 'metadata'
SEARCH = 'search'
USER_CONFIG = 'user_config'
# key for the DEFAULT section of all config parsers, cannot be changed
DEFAULT = 'DEFAULT'
# keys for reading & writing boolean values for all config parsers, cannot be changed
NO = 'no'
YES = 'yes'
# keys for reading & writing values for the search config parser's end reason key, can be changed
REQUIRED_RESULTS_FOUND = 'required results found!'
TIMED_OUT = 'timed out!'
# keys for the state machine in memory, half can be changed
QUEUED = 'queued'  # this indicates that the search should be started soon
RUNNING = 'Running'  # this is a web api status return value, indicates search is running
STOPPED = 'Stopped'  # this is a web api status return value, indicates search is or has stopped
CONCLUDED = 'concluded'  # this indicates that the search will not start again
# keys for the search details state machine on disk, can be changed
SEARCH_QUEUED = 'search_queued'
SEARCH_RUNNING = 'search_running'
SEARCH_STOPPED = 'search_stopped'
SEARCH_CONCLUDED = 'search_concluded'
# keys for reading & writing metadata info
META_DEMAND = 'nbPeers'
META_NAME = 'fileName'
META_SUPPLY = 'nbSeeders'
META_URL = 'fileurl'
# keys for reading & writing user configuration
ADD_WAIT = 'seconds_to_wait_after_each_torrent_add_attempt'
PRIORITY = 'metadata_priority'
MAIN_LOOP_WAIT = 'seconds_to_wait_after_each_main_loop'
OTHER_WAIT = 'seconds_to_wait_for_other_reason'
SEARCH_CHECK_WAIT = 'seconds_to_wait_after_each_search_status_check'
UNI_CHAR_COUNT = 'unicode_total_character_count'
UNI_SHIFT = 'unicode_shift_offset_for_scrambling_results_cfg_file'
# keys for reading & writing search details
AVG_SEEDS = 'average_seed_count'
EXPECTED_RESULT_COUNT = 'expected_search_result_count'
FILENAME_REGEX = 'regex_filter_for_filename'
MAX_SEARCH_ATTEMPTS = 'maximum_search_attempts'
MIN_SEEDS = 'minimum_seeds'
RESULTS_ADDED = 'results_added'
RESULTS_REQUIRED = 'results_required'
SEARCH_ATTEMPT_COUNT = 'search_attempt_count'
SEARCH_ID = 'search_id'
SEARCH_TERM = 'search_term'
# keys for controlling pause_type
ADD = 'add'
MAIN_LOOP = 'loops'
SEARCH = SEARCH  # key with two uses, 1. controlling pause type, 2. keying parser
STARTING = 'starting'
# keys to label/organize
EMPTY = ''
RESET = 'reset'
SEARCHES = 'searches'


class Configuration:
    def __init__(self, clean_up=False):
        # set paths
        self.paths = {
            PROJECT_PATH: _get_project_path(),
            DATA_PATH: _get_data_path(),
            USER_CONFIG_PATH: _get_user_config_path()
        }
        # set expected config files
        self.files = {
            USER_CONFIG_FILES: _get_expected_config_files(),
            PROJECT_FILES: _get_all_files_in_project_path()
        }
        # set parsers
        self.parsers = {
            METADATA: _get_parser(self.files[USER_CONFIG_FILES][METADATA_FILE_NAME]),
            SEARCH: _get_parser(self.files[USER_CONFIG_FILES][SEARCH_DETAILS_FILE_NAME]),
            USER_CONFIG: _get_parser(self.files[USER_CONFIG_FILES][USER_CONFIG_FILE_NAME])
        }
        if clean_up:
            self.cleanup_project_path()

    def cleanup_project_path(self):
        try:
            self._cleanup_path(Path(DATA_PATH_DIR_NAME))
            self._cleanup_path(Path(CONFIG_PATH_DIR_NAME))
            pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _cleanup_path(self, path_to_clean: Path):
        try:
            files_in_path = _get_all_files_in_path(path_to_clean)
            for file in files_in_path:
                expected_config_file_names = self.files[USER_CONFIG_FILES]
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


def _get_user_config_path() -> Path:
    """
    :return: data path as path object
    """
    try:
        ml.log_event('get data path', event_completed=True)
        return Path(_get_project_path(), CONFIG_PATH_DIR_NAME)
    except OSError as o_err:
        ml.log_event(o_err)


def _get_data_path() -> Path:
    """
    :return: data path as path object
    """
    try:
        ml.log_event('get data path', event_completed=True)
        return Path(_get_project_path(), DATA_PATH_DIR_NAME)
    except OSError as o_err:
        ml.log_event(o_err)


def _get_expected_config_files() -> dict:
    """
    :return: built path from hardcoded filename
    """
    ml.log_event('get config files')
    try:
        # get project root path
        project_path = _get_project_path()
        # get sub paths
        data_path = Path(project_path, DATA_PATH_DIR_NAME)
        user_config_path = Path(project_path, CONFIG_PATH_DIR_NAME)
        # get paths to config files
        config_files = {
            METADATA_FILE_NAME: Path(data_path, METADATA_FILE_NAME),
            SEARCH_DETAILS_FILE_NAME: Path(data_path, SEARCH_DETAILS_FILE_NAME),
            USER_CONFIG_FILE_NAME: Path(user_config_path, USER_CONFIG_FILE_NAME)
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
