from configparser import ConfigParser  # for type-checking
from datetime import datetime
from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)


def all_searches_concluded(self) -> bool:
    # TODO would be nice to exit if all jobs exceed set limits, not currently in-use
    try:

        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def enough_results_in_(filtered_results, expected_result_count):
    try:
        filtered_results_count = len(filtered_results)
        if filtered_results_count < expected_result_count:
            return False
        return True
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def fetch_metadata_from_(m_parser) -> dict:
    ml.log_event('fetching results from disk', event_completed=False)
    try:
        result_data = dict()
        for section in m_parser.sections():
            result_data[hash_metadata(section, True)] = dict()
            for key, detail in m_parser[section].items():
                result_data[hash_metadata(section, True)][key] = hash_metadata(detail, True)
        ml.log_event('fetching results from disk', event_completed=True)
        return result_data
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def get_most_popular_results(self, regex_filtered_results: list) -> list:
    try:
        pass
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def get_regex_filtered_results_and_count(self) -> tuple:
    try:
        # FIXME this function is getting called on headers that don't have active search ids
        results = self._qbit_get_search_results()

        metadata_parser_keys = self.get_keyring_for_metadata_parser()
        filtered_results = list()
        filtered_result_count = 0
        if results is None:
            ml.log_event('no search results for \'{}\''.format(self.active_section), level=ml.WARNING)
            return None, 0
        ml.log_event('get filename regex pattern for active header \'{}\''.format(self.active_section))
        for result in results[metadata_parser_keys.RESULT]:
            filename = result[metadata_parser_keys.NAME]
            filename_regex = self.search_parser_get_filename_regex()
            if self.regex_matches(filename_regex, filename):
                filtered_results.append(result)
                filtered_result_count += 1
        ml.log_event('\'{}\' filtered results have been found'.format(filtered_result_count))
        return filtered_results, filtered_result_count
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def hash_metadata(self, x, undo=False):
    # TODO how to get u_keys here?
    try:
        _undo = -1 if undo else 1
        _ucp_keys = self.get_keyring_for_user_config_parser()
        _hash = ''.join([chr(ord(e) + int(
            self.config.parser.parsers.user_config_parser[_ucp_keys.DEFAULT][_ucp_keys.UNI_SHIFT])) * _undo
                         for e in str(x) if x])

        ml.log_event('hashed from {} to {}'.format(x, _hash))
        return _hash
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def metadata_parser_write_to_metadata_config_file(self, result):
    try:
        metadata_parser_keys, user_config_parser_keys = \
            self.get_keyring_for_metadata_parser(), self.get_keyring_for_user_config_parser()
        ml.log_event(f'save metadata result to file: {result[metadata_parser_keys.NAME]}')
        metadata_section = self.hash_metadata(result[metadata_parser_keys.NAME])
        if not self.config.parser.parsers.metadata_parser.has_section(metadata_section):
            ml.log_event(f'qbit client has added result \'{result[metadata_parser_keys.NAME]}\' for header'
                         f' \'{self.active_section}\'', announce=True)
            self.config.parser.parsers.metadata_parser.add_section(metadata_section)
            header = metadata_section
            for attribute, detail in result.items():
                # TODO there are some redundant log commands 'above' and 'below' this entry
                # TODO i think this entry is causing the redundant log commands with _hash() calls
                h_attr, d_attr = self.hash_metadata(attribute), self.hash_metadata(detail)
                ml.log_event(f'detail added to metadata parser with attribute key \'{h_attr}\'')
                self.config.parser.parsers.metadata_parser[header][h_attr] = d_attr
                self.pause_on_event(user_config_parser_keys.WAIT_FOR_USER)
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def regex_matches(self, filename_regex, filename) -> bool:
    try:
        search_detail_parser_at_active_header = self.get_search_detail_parser_at_active_header()
        search_detail_parser_keys = self.get_keyring_for_search_detail_parser()
        user_config_parser_keys = self.get_keyring_for_user_config_parser()
        primary_search_term = search_detail_parser_at_active_header[search_detail_parser_keys.TOPIC]
        regex_match = findall(filename_regex, filename)
        if regex_match:
            # FIXME i don't like how this line is but if i split it up it looks worse somehow so.. what to do
            ml.log_event(f'@\'{self.active_section}\' w/ search term \'{primary_search_term}\' matched regex'
                         f' pattern \'{filename_regex}\' to results filename.. \n\n{filename}\n')
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_USER)
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def result_has_enough_seeds(self, result) -> bool:
    try:
        metadata_parser_keys, search_parser_keys = \
            self.config.hardcoded.keys.metadata_parser_keyring, self.config.hardcoded.keys.search_parser_keyring
        search_detail_parser_at_active_header = self.get_search_detail_parser_at_active_header()
        # minimum_seeds = int(self.search_parser[self.active_header][search_key.minimum_seeds])  # TODO delete
        minimum_seeds = int(search_detail_parser_at_active_header[search_parser_keys.MIN_SEED])
        # result_seeds = result[results_key.supply]
        result_seeds = result[metadata_parser_keys.SUPPLY]
        if result_seeds > minimum_seeds:
            ml.log_event('result {} has {} seeds, attempting to add'.format(result['fileName'], result_seeds))
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def search_has_yielded_required_results(self) -> bool:
    # TODO move this to state machine?
    ml.log_event('check if search can be concluded', event_completed=False)
    try:
        search_parser_keys = self.get_keyring_for_search_detail_parser()
        search_detail_parser_at_active_header = self.get_search_detail_parser_at_active_header()

        attempted_searches = \
            int(search_detail_parser_at_active_header[search_parser_keys.SEARCH_ATTEMPT_COUNT])

        max_search_attempt_count = \
            int(search_detail_parser_at_active_header[search_parser_keys.MAX_SEARCH_ATTEMPT_COUNT])

        results_added = \
            int(search_detail_parser_at_active_header[search_parser_keys.RESULTS_ADDED_COUNT])

        results_required = \
            int(search_detail_parser_at_active_header[search_parser_keys.RESULTS_REQUIRED_COUNT])

        if results_added > results_required:
            ml.log_event(f'search \'{self.active_section}\' can be concluded, '
                         'requested result count has been added', event_completed=True)
            self.search_set_end_reason(search_parser_keys.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
            return True
        elif attempted_searches > max_search_attempt_count:
            ml.log_event(f'search \'{self.active_section}\' can be concluded, too many search attempts '
                         f'w/o meeting requested result count', event_completed=True)
            self.search_set_end_reason(search_parser_keys.TIMED_OUT)  # too many search attempts, conclude
            return True
        ml.log_event(f'search \'{self.active_section}\' will be allowed to continue', event_completed=True)
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def set_time_last_searched_for_active_header(self):
    try:
        search_parser_at_active_header = self.get_search_detail_parser_at_active_header()
        search_parser_detail_keys = self.get_keyring_for_search_detail_parser()
        search_parser_at_active_header[search_parser_detail_keys.TIME_LAST_SEARCHED] = str(datetime.now())
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


