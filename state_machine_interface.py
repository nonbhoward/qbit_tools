from minimalog.minimal_log import MinimalLog
from user_configuration.settings_io import QbitConfig
from re import findall
ml = MinimalLog(__name__)
conf = QbitConfig()
m_key, s_key, u_key = conf.get_keyrings()
m_parser, s_parser, u_parser = conf.get_parsers()


def all_searches_concluded(self) -> bool:
    # TODO would be nice to exit if all jobs exceed set limits, not currently in-use
    try:
        pass  # TODO write this function
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def enough_results_in_(filtered_results, expected_result_count):
    try:
        filtered_results_count = len(filtered_results)
        if filtered_results_count < expected_result_count:
            ml.log_event(f'not enough results were found! \'{filtered_results_count}\' '
                         f'results, consider adjusting search parameters', level=ml.WARNING)
            return False
        ml.log_event(f'search yielded adequate results, \'{filtered_results_count}\' results found')
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


def get_all_sections_from_parser_(metadata=False, search=False, settings=False):
    try:
        return conf.get_all_sections_from_parser_(search=True)
        pass
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def get_most_popular_results(self, regex_filtered_results: list) -> list:
    try:
        pass  # TODO delete this function?
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def filter_results_using_(filename_regex, results) -> list:
    try:
        return list()
        pass  # TODO delete this function?
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def hash_metadata(x, undo=False, offset=0):
    # TODO how to get u_keys here?
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        ml.log_event(f'hashed from {x} to {_hash}')
        return _hash
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def read_parser_value_with_(key, section, search):
    # TODO this interface is lazy, above is a bool, and what is below? this is needlessly confusing
    # FIXME address this after refactor
    try:
        conf.read_parser_value_with_(key, section, search)
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def reduce_search_expectations_for_(section: str, c_key, er_key):
    try:
        ml.log_event(f'reducing search expectations for \'{section}\'')
        er_val = int(s_parser[section][er_key])
        if not er_val:
            ml.log_event(f'concluding search for \'{section}\'', level=ml.WARNING)
            s_parser[section][c_key] = s_key.YES
        er_val -= 1
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def regex_matches(filename_regex, filename) -> bool:
    try:
        regex_match = findall(filename_regex, filename)
        if regex_match:
            ml.log_event(f'pattern \'{filename_regex}\' matched against '
                         f'filename \'{filename}\'')
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def result_has_enough_seeds(self, result) -> bool:
    try:
        pass  # TODO refactor into this function
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def search_has_yielded_required_results(self) -> bool:
    # TODO recator into this function
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


def set_search_rank_using_(key):
    try:
        conf.set_search_rank_using_(key)
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def set_time_last_searched_for_active_header(self):
    try:
        pass  # TODO refactor into this function
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def write_config_to_disk():
    try:
        conf.write_config_to_disk()
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def write_parser_value_with_key_(parser_key, value, section, search):
    # FIXME same issue as read, lazy interface
    try:
        conf.write_parser_value_with_key_(parser_key, value, section, search)
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)
