from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd
from os import remove
from os import walk
from os.path import exists
from pathlib2 import Path
ml = MinimalLog(__name__)
# TODO besides imports the first program call is here, could be done better?
CONFIG_PATH_DIR_NAME = 'user_configuration'
DATA_PATH_DIR_NAME = 'data_src'
METADATA_FILE_NAME = 'metadata.cfg'
SEARCH_DETAILS_FILE_NAME = 'search_details.cfg'
USER_CONFIG_FILE_NAME = 'user_configuration.cfg'

# Keys for Configuration().paths
PROJECT_PATH = 'project_path'
DATA_PATH = 'data_path'
USER_CONFIG_PATH = 'user_config_path'
# Keys for Configuration().files
USER_CONFIG_FILES = 'user_config_files'
PROJECT_FILES = 'project_files'

# Key for the DEFAULT section of all config parsers
DEFAULT = 'DEFAULT'

# Keys for writing to the search.cfg search state-machine, the next action is chosen based on these
QUEUED = 'queued'  # this indicates that the search should be started soon
RUNNING = 'Running'  # this is a web api status return value, indicates search is running
STOPPED = 'Stopped'  # this is a web api status return value, indicates search is or has stopped
CONCLUDED = 'concluded'  # this indicates that the search will not start again

# Keys for reading & writing boolean values for all config parsers
NO = 'no'
YES = 'yes'

# Keys for reading & writing UserSettings().parser
METADATA = 'metadata'
SEARCH = 'search'
USER_CONFIG = 'user_config'

# Keys for reading & writing values for the search config parser's end reason key
REQUIRED_RESULTS_FOUND = 'required results found!'
TIMED_OUT = 'timed out!'

# Uncategorized keys
ADD = 'add'
EMPTY = ''
LOOPS = 'loops'
RESET = 'reset'
SEARCHES = 'searches'
STARTING = 'starting'


class Configuration:
    def __init__(self, clean_up=False):
        # this is the program entry from user imports?
        # get paths
        self.paths = {
            PROJECT_PATH: _get_project_path(),
            DATA_PATH: _get_data_path(),
            USER_CONFIG_PATH: _get_user_config_path()
        }
        # get expected config files
        self.files = {
            USER_CONFIG_FILES: _get_expected_config_files(),
            PROJECT_FILES: _get_all_files_in_project_path()
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
                expected_config_file_names = self.user_config_files
                if file not in expected_config_file_names:
                    remove(file)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


class ResultKeys:
    def __init__(self):
        # keys that steer program function
        # change this to change sort priority on newly found searches
        # TODO how could i programmatically change self.seeders from being hardcoded? should i care?
        # TODO is this the first instance where we touch the API? maybe can't be changed then?
        if user_settings.parser['seeds']:
            self.priority = self.seeders
        self.priority = self.seeders
        self.file_size = 'filesize'  # TODO check spelling on filesize vs api response attribute
        # keys that correspond to  the web api responses
        self.demand = 'nbPeers'
        self.name = 'fileName'
        self.seeders = 'nbSeeders'

        # another term for number of seeds
        self.supply = self.seeders

        # uncategorized keys
        self.results = 'results'


class SearchJobKeys:
    def __init__(self):
        self.attempts = 'search_attempts'
        self.attempts_max = 'search_attempts_max'
        self.concluded = 'search_concluded'
        self.end_reason = ''
        self.expected_search_result_count = 'expected_search_result_count'
        self.id = 'search_id'
        self.last_read = 'last_read'
        self.last_write = 'last_write'
        self.minimum_seeds = 'minimum_seeds'
        self.pattern = 'search_pattern'
        self.queued = 'search_queued'
        self.results_added = 'results_added'
        self.results_required = 'results_required'
        self.running = 'search_running'
        self.stopped = 'search_stopped'
        self.term = 'search_term'


class UserSettings:
    def __init__(self):
        # second class call in file
        # folder in project where program expects to find user_configuration files to set behavior, examples provided
        self.configuration = Configuration()
        mp = ConfigParser().read(self.configuration.files[USER_CONFIG_FILES][0])
        sp = ConfigParser().read(self.configuration.files[USER_CONFIG_FILES][1])
        up = ConfigParser().read(self.configuration.files[USER_CONFIG_FILES][2])
        self.parsers = {
            METADATA: _config_get_parser()[0],
            SEARCH: _config_get_parser()[1],
            USER_CONFIG: _config_get_parser()[2]
        }
        # set to 0 in user_configuration.cfg to disable scrambling
        self.unicode_shift_offset = 'unicode_shift_offset_for_scrambling_results_cfg_file'
        # the amount of characters in all of unicode
        # TODO wonder if i could fetch this from somewhere that hosts it remotely?
        # TODO then would i have to be sure the unicode on my machine was up to date..
        # TODO could cause issues, low priority but something to think about
        self.unicode_total_character_count = 'unicode_total_character_count'
        # some keys for program wait times to avoid spamming searches
        self.wait_between_main_loops = 'seconds_to_wait_before_restarting_main_loop'
        self.wait_between_result_adds = 'seconds_to_wait_between_each_torrent_add_attempt'
        self.wait_between_searches = 'seconds_to_wait_between_search_status_checks'
        # a key for a generic wait time with no specific reason
        self.wait_for_some_other_reason = 'seconds_to_wait_for_other_reason'
        if not _parser_is_ready()[0]:
            ml.log_event('parser is not ready', level=ml.ERROR)
            raise Exception


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
        project_path, all_files = user_settings.configuration.project_path, list()
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


def _get_expected_config_files() -> tuple:
    """
    :return: built path from hardcoded filename
    """
    ml.log_event('get config files')
    try:
        # get main paths
        project_path = _get_project_path()
        data_path = Path(project_path, DATA_PATH_DIR_NAME)
        user_config_path = Path(project_path, CONFIG_PATH_DIR_NAME)
        # build full paths
        metadata_file = Path(data_path, METADATA_FILE_NAME)
        search_details_file = Path(data_path, SEARCH_DETAILS_FILE_NAME)
        user_config_file = Path(user_config_path, USER_CONFIG_FILE_NAME)
        return metadata_file, search_details_file, user_config_file
    except OSError as o_err:
        ml.log_event(o_err)


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


def get_user_settings() -> UserSettings:
    try:
        return UserSettings()
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    pass  # i don't see why i would run this directly besides testing
else:
    user_settings = UserSettings()
