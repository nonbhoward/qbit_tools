from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd
# TODO what to import to delete a file again..
from os.path import devnull
from os import walk
from os.path import exists
from pathlib2 import Path
ml = MinimalLog(__name__)
# TODO besides imports the first program call is here, could be done better?
DATA_PATH_DIR_NAME = 'data_src'
METADATA_OF_ADDED_TORRENTS_FILE_NAME = 'metadata_of_added_torrents.cfg'
SEARCH_JOB_DETAILS_FILE_NAME = 'search_job_details.cfg'
USER_CONFIG_FILE_NAME = 'user_configuration.cfg'

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

# Keys for reading & writing values for the settings config parser
RESULT = 'result'
SEARCH = 'search'
SETTINGS = 'user_settings'

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


class UserSettings:
    def __init__(self):
        # second class call in file
        # folder in project where program expects to find configuration files to set behavior, examples provided
        self.configuration = Configuration()
        self.parser_file_names =

        # set key to 0 in user_configuration.cfg to disable scrambling
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


class Configuration:
    def __init__(self, clean_up = False):
        # first class call in file
        # this is the program entry from user imports
        self.data_directory_path = _get_data_path()
        self.user_config_files = _get_config_files()
        self.all_files_in_data_path = _get_all_files_in_data_path()
        if clean_up:
            self.cleanup_data_path()
        # files in data path
        self.user_preferences_filename = 'user_configuration.cfg'

    def cleanup_data_path(self):
        try:
            files = self.all_files_in_data_path
            for file in files:
                expected_files = self.user_config_files
                if file not in expected_files:

        except Exception as e_err:
            ml.log_event(e_err)


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


def _config_get_parser(parser_type) -> ConfigParser:
    """
    :return: ConfigParser containing parsed details
    """
    ml.log_event('get parser type {}'.format(parser_type), event_completed=False)
    try:
        if exists(_get_config_files(parser_type)):
            cp = ConfigParser()
            cp.read(filenames=_get_config_files(parser_type))
            if _config_file_has_sections(cp):
                ml.log_event('get parser type {}'.format(parser_type), event_completed=True)
                return cp
            ml.log_event('warning, configuration file has no sections', level=ml.WARNING)
            return cp
        else:
            raise FileNotFoundError('requested {} configuration does not exist'.format(parser_type))
    except FileNotFoundError as f_err:
        ml.log_event(f_err)

def _get_all_files_in_data_path():
    try:
        data_path, all_files = user_settings.configuration.data_directory_path, list()
        for root, dirs, files in walk(data_path):
            for file in files:
                all_files.append(Path(root, file))
        return all_files
    except Exception as e_err:
        ml.log_event(e_err)


def _get_config_files() -> tuple:
    """
    :return: built path from hardcoded filename
    """
    ml.log_event('get config files')
    try:
        data_path = user_settings.configuration.data_directory_path
        metadata_of_added_torrents_path = Path(data_path, METADATA_OF_ADDED_TORRENTS_FILE_NAME)
        search_job_details_path = Path(data_path, SEARCH_JOB_DETAILS_FILE_NAME)
        user_configuration_path = Path(data_path, USER_CONFIG_FILE_NAME)
        return metadata_of_added_torrents_path, search_job_details_path, user_configuration_path
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


if __name__ == '__main__':
    pass  # i don't see why i would run this directly besides testing
else:
    user_settings = UserSettings()
