from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from time import sleep
from user_configuration.settings_io import QbitConfig
from re import findall
ml = MinimalLog(__name__)
conf = QbitConfig()
m_key, s_key, u_key = conf.get_keyrings()
m_parser, s_parser, u_parser = conf.get_parsers()


def add_results_from_(results, active_kv, api):
    # TODO this should be broken up
    try:
        active_section = active_kv[0]
        s_parser_at_active = s_parser[active_section]
        expected_results_count = int(s_parser_at_active[s_key.EXPECTED_SEARCH_RESULT_COUNT])
        search_priority = u_parser[u_key.DEFAULT][u_key.USER_PRIORITY]
        unicode_offset = u_parser[u_key.DEFAULT][u_key.UNI_SHIFT]
        results_count = len(results)
        # TODO results_key.supply could be sort by any key
        ml.log_event(f'add results by {search_priority}')
        ml.log_event(f'get most popular \'{expected_results_count}\' count results')
        if not enough_results_in_(results, expected_results_count):
            c_key, er_key = s_key.CONCLUDED, s_key.EXPECTED_SEARCH_RESULT_COUNT
            reduce_search_expectations_for_(active_section, c_key, er_key)
            expected_results_count = results_count
        # TODO remove hardcoded nbSeeders
        sorted_results = sorted(results, key=lambda k: k['nbSeeders'], reverse=True)
        searches_concluded = dict()
        active_is_concluded = s_parser_at_active.getboolean(s_key.CONCLUDED)
        if active_is_concluded:
            write_parser_value_with_key_(parser_key=s_key.CONCLUDED, value='yes',
                                         section=active_section, search=True)
        for section in s_parser.sections():
            searches_concluded[section] = s_parser_at_active.getboolean(s_key.CONCLUDED)
        if all(searches_concluded.values()):
            ml.log_event('all search tasks concluded, exiting program')
            exit()
        ml.log_event(f'results sorted by popularity for {active_section}')
        minimum_seeds = int(s_parser_at_active[s_key.MIN_SEED])
        for result in sorted_results:
            results_added_count = int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT])
            if results_added_count > expected_results_count:
                # TODO this would be a successful conclusion
                return  # enough results have been added for this header, stop
            result_seeds = result[m_key.SUPPLY]
            enough_seeds = True if result_seeds > minimum_seeds else False
            if enough_seeds:
                count_before = api.count_all_local_results()
                ml.log_event(f'local machine has {count_before} stored results before add attempt..')
                api.qbit_client.torrents_add(urls=result[m_key.URL], is_paused=True)
                pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
                results_added = api.count_all_local_results() - count_before
                # TODO why does client fail to add so often? outside project scope?
                if results_added > 0:  # successful add
                    results_added_count += 1
                    s_parser_at_active[s_key.RESULTS_ADDED_COUNT] = str(results_added_count)
                    ml.log_event(f'save metadata result to file: {result[m_key.NAME]}')
                    metadata_section = hash_metadata(result[m_key.NAME], offset=unicode_offset)
                    if m_parser.has_section(metadata_section):
                        ml.log_event(f'metadata parser already has section \'{metadata_section}\'',
                                     level=ml.WARNING)
                        # FIXME this could be a bug if two files had the same name.. do i care? at this time, no
                        continue
                    ml.log_event(f'qbit client has added result \'{result[m_key.NAME]}\' for '
                                 f'header \'{active_section}\'', announce=True)
                    m_parser.add_section(metadata_section)
                    for attribute, detail in result.items():
                        h_attr, d_attr = \
                            hash_metadata(attribute, offset=unicode_offset), \
                            hash_metadata(detail, offset=unicode_offset)
                        write_parser_value_with_key_(parser_key=h_attr, value=d_attr,
                                                     section=metadata_section, metadata=True)
                        pause_on_event(u_key.WAIT_FOR_USER)
                    if results_added_count > expected_results_count:
                        return
                    s_parser_at_active[s_key.RESULTS_ADDED_COUNT] = \
                        str(int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT]))
            ml.log_event(f'client failed to add \'{result[m_key.NAME]}\'', level=ml.WARNING)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def all_searches_concluded() -> bool:
    # TODO would be nice to exit if all jobs exceed set limits, not currently in-use
    try:
        pass  # TODO write this function
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def empty_(test_string) -> bool:
    try:
        if test_string == '':
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


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
        ml.log_event(e_err.args[0], level=ml.ERROR)


def fetch_metadata_from_(parser) -> dict:
    ml.log_event('fetching results from disk', event_completed=False)
    try:
        result_data = dict()
        for section in parser.sections():
            result_data[hash_metadata(section, True)] = dict()
            for key, detail in parser[section].items():
                result_data[hash_metadata(section, True)][key] = hash_metadata(detail, True)
        ml.log_event('fetching results from disk', event_completed=True)
        return result_data
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_all_sections_from_parser_(metadata=False, search=False, settings=False):
    try:
        if metadata:
            return conf.get_all_sections_from_parser_(metadata=True)
        if search:
            return conf.get_all_sections_from_parser_(search=True)
        if settings:
            return conf.get_all_sections_from_parser_(settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_most_popular_results(self, regex_filtered_results: list) -> list:
    try:
        pass  # TODO delete this function?
        return list()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_results_for_(active_kv: tuple, api) -> list:
    try:
        section, search_id, key = active_kv[0], active_kv[1], s_key.REGEX_FILTER_FOR_FILENAME
        filename_regex = read_parser_value_with_(key=key, section=section, search=True)
        results = api.get_search_results(search_id=search_id, use_filename_regex_filter=True,
                                         filename_regex=filename_regex, metadata_filename_key=m_key.NAME)
        return results
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def filter_results_using_(filename_regex, results) -> list:
    try:
        return list()
        pass  # TODO delete this function?
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def hash_metadata(x, undo=False, offset=0):
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        ml.log_event(f'hashed from {x} to {_hash}')
        return _hash
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def pause_on_event(pause_type):
    try:
        timestamp = dt.now()
        parser_at_default = u_parser[u_key.DEFAULT]
        if pause_type == u_key.WAIT_FOR_MAIN_LOOP:
            delay = int(parser_at_default[u_key.WAIT_FOR_MAIN_LOOP])
            ml.log_event(f'{timestamp} waiting {delay} seconds for main loop repeat..')
            sleep(delay)
        elif pause_type == u_key.WAIT_FOR_SEARCH_STATUS_CHECK:
            delay = int(parser_at_default[u_key.WAIT_FOR_SEARCH_STATUS_CHECK])
            ml.log_event(f'{timestamp} waiting {delay} seconds for search state check..')
            sleep(delay)
        elif pause_type == u_key.WAIT_FOR_SEARCH_RESULT_ADD:
            delay = int(parser_at_default[u_key.WAIT_FOR_SEARCH_RESULT_ADD])
            ml.log_event(f'{timestamp} waiting {delay} seconds for add attempt..')
            sleep(delay)
        elif pause_type == u_key.WAIT_FOR_USER:
            delay = int(parser_at_default[u_key.WAIT_FOR_USER])
            ml.log_event(f'{timestamp} waiting {delay} seconds to let user follow log..')
            sleep(delay)
        else:
            raise Exception(f'unknown pause type \'{pause_type}\'')
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def read_parser_value_with_(key, section, search=False, metadata=False, settings=False):
    # TODO this interface is lazy, above is a bool, and what is below? this is needlessly confusing
    # FIXME address this after refactor
    try:
        if metadata:
            return conf.read_parser_value_with_(key, section, metadata=True)
        if search:
            return conf.read_parser_value_with_(key, section, search=True)
        if settings:
            return conf.read_parser_value_with_(key, section, settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def reduce_search_expectations_for_(section: str, c_key, er_key):
    try:
        ml.log_event(f'reducing search expectations for \'{section}\'')
        er_val = int(s_parser[section][er_key])
        if not er_val:
            ml.log_event(f'concluding search for \'{section}\'', level=ml.WARNING)
            s_parser[section][c_key] = s_key.YES
        er_val -= 1
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def regex_matches(filename_regex, filename) -> bool:
    try:
        regex_match = findall(filename_regex, filename)
        if regex_match:
            ml.log_event(f'pattern \'{filename_regex}\' matched against '
                         f'filename \'{filename}\'')
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def result_has_enough_seeds(self, result) -> bool:
    try:
        ml.log_event(f'TODO result_has_enough_seeds()')
        pass  # TODO refactor into this function
        return True
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def search_has_yielded_required_results(self) -> bool:
    # TODO refactor into this function
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
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_search_rank_using_(key):
    try:
        conf.set_search_rank_using_(key)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_time_last_searched_for_active_header(self):
    try:
        pass  # TODO refactor into this function
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def write_config_to_disk():
    try:
        conf.write_config_to_disk()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def write_parser_value_with_key_(parser_key, value, section, metadata=False, search=False, settings=False):
    # FIXME same issue as read, clunky interface, rework
    try:
        if metadata:
            conf.write_parser_value_with_key_(parser_key, value, section, metadata=True)
        if search:
            conf.write_parser_value_with_key_(parser_key, value, section, search=True)
        if settings:
            conf.write_parser_value_with_key_(parser_key, value, section, settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
