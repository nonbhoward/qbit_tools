# TODO this should maybe be it's own repo/project, lots of potential for re-use
from configparser import ConfigParser
from minimalog.minimal_log import MinimalLog
from os import getcwd, remove, walk
from pathlib2 import Path
ml = MinimalLog()


##### ##### ##### ##### ##### ##### ##### ##### TIER 3 CLASSES ##### ##### ##### ##### ##### ##### ##### ######
class APIStateKeys:  # Configuration.HardCoded.KeyRing.APIStateKeys
    def __init__(self):
        # keys for the state machine, some from API responses, in memory, half can be changed
        self.CONCLUDED = 'concluded'  # this indicates that the search will not start again
        self.QUEUED = 'queued'  # this indicates that the search should be started soon
        self.RUNNING = 'Running'  # this is a web api status return value, indicates search is running
        self.STOPPED = 'Stopped'  # this is a web api status return value, indicates search is or has stopped


class MetaDataKeys:  # Configuration.HardCoded.KeyRing.MetaDataKeys
    def __init__(self):
        # keys for reading & writing metadata info
        # TODO get all of these keys from next debug run returning results
        self.DEMAND = 'nbPeers'
        self.NAME = 'fileName'
        self.RESULT = 'results'
        self.SUPPLY = 'nbSeeders'
        self.URL = 'fileUrl'


class MiscKeys:  # Configuration.HardCoded.KeyRing.MiscKeys
    def __init__(self):
        # keys to label/organize
        self.EMPTY = ''
        self.RESET = 'reset'


class Parsed:  # Configuration.HardCoded.FileNames.Parsed
    def __init__(self):
        # project's configuration file names, cannot be changed without changing project structure
        self.metadata = 'metadata.cfg'
        self.search_detail = 'search_details.cfg'
        self.user_config = 'user_configuration.cfg'


class ParserKeys:  # Configuration.HardCoded.KeyRing.ParserKeys
    def __init__(self):
        # keys for Configuration().parsers, can be changed
        # key for the DEFAULT section of all config parsers, cannot be changed
        self. DEFAULT = 'DEFAULT'
        # keys for reading & writing boolean values for all config parsers, cannot be changed
        self.NO = 'no'
        self.YES = 'yes'


class SearchDetailKeys:  # Configuration.HardCoded.KeyRing.SearchDetailKeys
    def __init__(self):
        # keys for reading & writing search details
        self.AVG_SEED_COUNT = 'average_seed_count'
        self.EXPECTED_RESULT_COUNT = 'expected_search_result_count'
        self.FILE_NAME_REGEX = 'regex_filter_for_file_name'
        self.LAST_READ = 'last_read'
        self.LAST_WRITE = 'last_write'
        self.MAX_SEARCH_ATTEMPT_COUNT = 'maximum_search_attempts'
        self.MIN_SEED_COUNT = 'minimum_seeds'
        # FYI, ***FOR KEY REFERENCES ONLY*** trying to keep properties singular for predictability,
        # key strings can be plural or singular since they are never directly referenced
        self.RESULT_ADDED_COUNT = 'results_added'
        self.RESULT_COUNT = 'results_count'
        self.RESULT_REQUIRED_COUNT = 'results_required'
        self.SEARCH_ATTEMPT_COUNT = 'search_attempt_count'
        self.SEARCH_ID = 'search_id'
        self.SEARCH_STOPPED_REASON = 'search_stopped_reason'
        self.SEARCH_TERM = 'search_term'


# class SearchStateKeys:  # Configuration.HardCoded.KeyRing.SearchStateKeys
#     def __init__(self):
#         # keys for the search details state machine on disk, can be changed
#         self.SEARCH_CONCLUDED = 'search_concluded'
#         self.SEARCH_QUEUED = 'search_queued'
#         self.SEARCH_RUNNING = 'search_running'
#         self.SEARCH_STOPPED = 'search_stopped'


class SearchStoppedReasonKeys:  # Configuration.HardCoded.KeyRing.SearchStoppedReasonKeys
    def __init__(self):
        # keys for reading & writing values for the search config parser's end reason key, can be changed
        self.REQUIRED_RESULT_COUNT_FOUND = 'required results found!'
        self.TIMED_OUT = 'search timed out!'


class UserConfigKeys:  # Configuration.HardCoded.KeyRing.UserConfigKeys
    def __init__(self):
        # keys for reading & writing user configuration
        # program wait times
        self.ADD_RESULT = 'seconds_to_wait_after_each_torrent_add_attempt'
        self.MAIN_LOOP = 'seconds_to_wait_after_each_main_loop'
        self.MISCELLANEOUS = 'seconds_to_wait_for_miscellaneous_reason'
        self.SEARCH_STATUS_CHECK = 'seconds_to_wait_after_each_search_status_check'
        # other user settings
        # TODO how will 'seeds' on disk translate to 'nbSeeders' in practice?
        self.PRIORITY = 'metadata_priority'
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
        self.to_be_parsed = Parsed()


class KeyRing:  # Configuration.HardCoded.KeyRing
    def __init__(self):
        self.api_state_keyring = APIStateKeys()
        self.metadata_keyring = MetaDataKeys()
        self.misc_keyring = MiscKeys()
        self.parser_keyring = ParserKeys()
        self.search_detail_keyring = SearchDetailKeys()
        # self.search_state_keyring = SearchStateKeys()  # TODO delete
        self.search_stopped_reason_keyring = SearchStoppedReasonKeys()
        self.user_config_keyring = UserConfigKeys()


class ParserPaths:  # Configuration.Parser.ParserPaths
    def __init__(self, configuration):
        self.metadata_parser_path = self._get_parser_paths_from_(configuration)

    @staticmethod
    def _get_parser_paths_from_(configuration):
        try:
            print('todo')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


class Parsers:  # Configuration.Parser.Parsers
    def __init__(self, configuration):
        # TODO not scalable in the long term, will have to think about how to restructure this
        parser_paths = configuration.paths._get_parser_paths_from_(configuration)
        self.parsers_keyed_by_file_path = self._get_parsers_from_(parser_paths)
        self.metadata_parser = self.parsers_keyed_by_file_path[parser_paths[0]]
        self.search_details_parser = self.parsers_keyed_by_file_path[parser_paths[1]]
        self.user_config_parser = self.parsers_keyed_by_file_path[parser_paths[2]]

    @staticmethod
    def _get_parsers_from_(parser_paths) -> dict:
        """
        TODO how should this function handle situation where sections are not found?
        TODO most likely scenario is parser did not successfully read
        TODO for now it will not be added, which will cause Parsers to fatal exception
        """
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
        self.file_names = FileNames()
        self.directory_names = DirectoryNames()
        self.extensions = Extensions()
        self.keys = KeyRing()


class Parser:  # Configuration.Parser
    def __init__(self, configuration):
        self.paths = ParserPaths(configuration)
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
            data_directory_name = configuration.hardcoded.directory_names.data_path
            ml.log_event('get data path for {}..'.format(data_directory_name))
            return Path(path.project, data_directory_name)
        except OSError as o_err:
            ml.log_event(o_err, level=ml.ERROR)

    def _get_parser_paths_from_(path, configuration) -> tuple:
        # TODO this cannot scale
        try:
            # data paths
            metadata_parser_path = Path(path.data, configuration.hardcoded.file_names.to_be_parsed.metadata)
            search_details_path = Path(path.data, configuration.hardcoded.file_names.to_be_parsed.search_detail)
            # user config paths
            user_config_path = Path(path.user_config, configuration.hardcoded.file_names.to_be_parsed.user_config)
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
    def __init__(self, parse_all_project_files=False):  # FYI, module entry point is here
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
        configuration = Configuration(parse_all_project_files=True)
        return configuration
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _parser_has_sections(configparser) -> bool:
    try:
        section_count = len(configparser.sections())
        ml.log_event('configparser {} has {} sections'.format(configparser, section_count))
        if section_count > 0:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    cf = Configuration(parse_all_project_files=True)
    pass
else:
    ml = MinimalLog(__name__)
