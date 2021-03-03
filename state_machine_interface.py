from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from time import sleep
from user_configuration.settings_io import QbitConfig as qconf
from re import findall
ml = MinimalLog(__name__)
m_key, s_key, u_key = qconf.get_keyrings()
ma_parser, mf_parser, s_parser, u_parser = qconf.get_parsers()


def add_is_successful_for_(result, api, section) -> bool:
    try:
        count_before_add_attempt = api.count_all_local_results()
        ml.log_event(f'local machine has {count_before_add_attempt} stored results before add attempt..')
        # TODO why does client fail to add so often? outside project scope?
        api.qbit_client.torrents_add(urls=result[m_key.URL], is_paused=get_add_mode_for_(section))
        pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
        results_added_count = api.count_all_local_results() - count_before_add_attempt
        success = False
        if results_added_count:
            success = True
            increment_result_added_count_for_(section)
        store_metadata_of_(result, success)
        return success
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def add_results_from_(results, active_kv, api):
    # TODO this could be broken up?
    try:
        active_section = active_kv[0]
        s_parser_at_active = s_parser[active_section]
        results_required_count = int(s_parser_at_active[s_key.RESULTS_REQUIRED_COUNT])
        unicode_offset = u_parser[u_key.DEFAULT][u_key.UNI_SHIFT]
        results = filter_(results, active_section, size=True)
        if not enough_found_in_(results, active_section):
            reduce_search_expectations_for_(active_section)
            results_required_count = len(results)
        ml.log_event(f'add most popular \'{results_required_count}\' count results')
        for result in results:
            results_added_count = int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT])
            if results_added_count > results_required_count:
                ml.log_event(f'the search for \'{active_section}\' can be concluded', announce=True)
                s_parser_at_active[s_key.CONCLUDED] = s_key.YES
                return  # enough results have been added for this header, stop
            if previously_found_(result):
                continue
            if add_is_successful_for_(result, api, active_section):
                create_metadata_section_for_(result, active_section, unicode_offset)
                if enough_results_added_for_(active_section):
                    ml.log_event(f'enough results added for \'{active_section}\'')
                    return  # desired result count added, stop adding
                continue  # result added, go to next
            ml.log_event(f'client failed to add \'{result[m_key.NAME]}\'', level=ml.WARNING)
            continue  # FIXME delete this, no longer does anything
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def all_searches_concluded() -> bool:
    """
    1. iterate over every section in the search parser
    2. fetch the value of CONCLUDED from each
    3. if all True, then all searches are concluded
    :return: bool, all searches concluded
    """
    try:
        concluded = list()
        for section in s_parser.sections():
            if s_parser[section].getboolean(s_key.CONCLUDED):
                concluded.append(True)
        if concluded and all(concluded):
            return True
        ml.log_event(f'all searches are not concluded, program continuing')
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def apply_filters_to_(result, filters):
    try:
        # TODO decide to abstract to this func or delete
        pass
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def create_metadata_section_for_(result, section, offset):
    try:
        ml.log_event(f'save metadata result to parser \'{result[m_key.NAME]}\'')
        metadata_section = hash_metadata(result[m_key.NAME], offset=offset)
        if ma_parser.has_section(metadata_section):  # FIXME two files, same name?
            ml.log_event(f'metadata parser already has section \'{metadata_section}\'', level=ml.WARNING)
            return
        ml.log_event(f'qbit client has added result \'{result[m_key.NAME]}\' for header \'{section}\'', announce=True)
        ma_parser.add_section(metadata_section)
        for attribute, detail in result.items():
            h_attr, d_attr = get_hashed_(attribute, detail, offset)
            write_parser_value_with_key_(parser_key=h_attr, value=d_attr,
                                         section=metadata_section, metadata=True)
            pause_on_event(u_key.WAIT_FOR_USER)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def empty_(test_string) -> bool:
    try:
        if test_string == '':
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def enough_results_added_for_(section) -> bool:
    try:
        results_added_count = int(s_parser[section][s_key.RESULTS_ADDED_COUNT])
        results_required_count = int(s_parser[section][s_key.RESULTS_REQUIRED_COUNT])
        if results_added_count > results_required_count - 1:
            return True
        return False
    except Exception as e_err:
        print(e_err.args[0])


def enough_found_in_(filtered_results, active_section):
    try:
        expected_results_count = int(s_parser[active_section][s_key.RESULTS_REQUIRED_COUNT])
        filtered_results_count = 0
        if filtered_results is not None:
            filtered_results_count = len(filtered_results)
        if filtered_results_count < expected_results_count:
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


def filter_(results: list, section: str, seeds=True, size=False, sort=True):
    try:
        search_priority = u_parser[u_key.DEFAULT][u_key.USER_PRIORITY]
        ml.log_event(f'add results by {search_priority}')
        minimum_seeds = int(s_parser[section][s_key.MIN_SEED])
        min_size_bytes = int(s_parser[section][s_key.SIZE_MIN_BYTES])
        min_size_megabytes = min_size_bytes / 1000000
        max_size_bytes = int(s_parser[section][s_key.SIZE_MAX_BYTES])
        max_size_megabytes = max_size_bytes / 1000000
        results_filtered = list()
        for result in results:
            if seeds:
                result_seeds = int(result[m_key.SUPPLY])
                enough_seeds = True if result_seeds > minimum_seeds else False
                if not enough_seeds:
                    ml.log_event(f'required seeds \'{minimum_seeds}\' not met by result with '
                                 f'\'{result_seeds}\' seeds, result : \'{result[m_key.NAME]}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    continue
            if size:
                result_size = int(result[m_key.SIZE])
                result_size_megabytes = result_size / 1000000
                file_size_in_range = True if max_size_bytes > result_size > min_size_bytes else False
                if not file_size_in_range:
                    ml.log_event(f'size requirement \'{min_size_megabytes}\'MiB to \'{max_size_megabytes}\'MiB not met by'
                                 f'result with size \'{result_size_megabytes}\'MiB, result: \'{result[m_key.NAME]}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    continue
            ml.log_event(f'result \'{result[m_key.NAME]}\' meets all requirements')
            results_filtered.append(result)
        if sort:
            ml.log_event(f'results sorted for {section} # TODO dynamic sort values')
            results = sort_(results_filtered)
        return results
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_add_mode_for_(section: str) -> bool:
    try:
        add_paused = s_parser[section].getboolean(s_key.ADD_PAUSED)
        if add_paused:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def get_all_sections_from_parser_(meta_add=False, meta_find=False, search=False, settings=False):
    try:
        if meta_add:
            return qconf.get_all_sections_from_parser_(meta_add=True)
        if meta_find:
            return qconf.get_all_sections_from_parser_(meta_find=True)
        if search:
            return qconf.get_all_sections_from_parser_(search=True)
        if settings:
            return qconf.get_all_sections_from_parser_(settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_hashed_(detail, attribute, offset):
    try:
        return hash_metadata(attribute, offset), hash_metadata(detail, offset)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_results_for_(active_kv: tuple, api) -> list:
    try:
        filename_regex = read_parser_value_with_(key=s_key.REGEX_FILTER_FOR_FILENAME,
                                                 section=active_kv[0],
                                                 search=True)
        results = api.get_search_results(search_id=active_kv[1],
                                         use_filename_regex_filter=True,
                                         filename_regex=filename_regex,
                                         metadata_filename_key=m_key.NAME)
        return results
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


def increment_result_added_count_for_(section):
    try:
        s_parser[section][s_key.RESULTS_ADDED_COUNT] = \
            str(int(s_parser[section][s_key.RESULTS_ADDED_COUNT]) + 1)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def pause_on_event(pause_type):
    try:
        parser_at_default = u_parser[u_key.DEFAULT]
        delay = int(parser_at_default[pause_type])
        ml.log_event(f'{dt.now()} waiting {delay} seconds for event \'{str(pause_type)}\'')
        sleep(delay)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def previously_found_(result):
    try:
        result_name = result[m_key.NAME]
        if result_name in mf_parser.sections():
            ml.log_event(f'result \'{result_name}\' failed before, skipping..', level=ml.WARNING)
            return True
        ml.log_event(f'result \'{result_name}\' is new! attempting to add')
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def read_parser_value_with_(key, section, search=False, metadata=False, settings=False):
    # TODO this interface is lazy, above is a bool, and what is below? this is needlessly confusing
    # FIXME address this after refactor
    try:
        if metadata:
            return qconf.read_parser_value_with_(key, section, metadata=True)
        if search:
            return qconf.read_parser_value_with_(key, section, search=True)
        if settings:
            return qconf.read_parser_value_with_(key, section, settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def ready_to_start_(queued, state_machine):
    try:
        search_rank = int(s_parser[state_machine.active_section][s_key.RANK])
        search_rank_required_to_start = int(u_parser[u_key.DEFAULT][u_key.RANK_REQUIRED])
        queue_has_room = not state_machine.search_queue_full()
        search_rank_allowed = search_rank <= search_rank_required_to_start
        if queued and queue_has_room and search_rank_allowed:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def reduce_search_expectations_for_(section: str):
    try:
        c_key, re_key = s_key.CONCLUDED, s_key.RESULTS_REQUIRED_COUNT
        ml.log_event(f'reducing search expectations for \'{section}\'')
        er_val = int(s_parser[section][re_key])
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
            pause_on_event(u_key.WAIT_FOR_USER)
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


def search_has_yielded_required_results(section) -> bool:
    # TODO refactor into this function
    try:
        s_parser_at_active = s_parser[section]
        attempted_searches = int(s_parser_at_active[s_key.SEARCH_ATTEMPT_COUNT])
        max_search_attempt_count = int(s_parser_at_active[s_key.MAX_SEARCH_COUNT])
        results_added = int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT])
        results_required = int(s_parser_at_active[s_key.RESULTS_REQUIRED_COUNT])
        if results_added >= results_required:
            ml.log_event(f'search \'{section}\' can be concluded, '
                         'requested result count has been added')
            search_set_end_reason(section, s_key.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
            return True
        elif attempted_searches >= max_search_attempt_count:
            ml.log_event(f'search \'{section}\' can be concluded, too many '
                         f'search attempts w/o meeting requested result count')
            search_set_end_reason(section, s_key.TIMED_OUT)  # too many search attempts, conclude
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_search_rank_using_(key):
    try:
        qconf.set_search_rank_using_(sort_key=key)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def search_set_end_reason(section, reason_key):
    try:
        s_parser[section][s_key.SEARCH_STOPPED_REASON] = reason_key
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_time_last_searched_for_active_header(self):
    try:
        pass  # TODO refactor into this function
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sort_(results):
    try:
        # TODO remove hardcoded nbSeeders
        results_sorted = sorted(results, key=lambda k: k['nbSeeders'], reverse=True)
        return results_sorted
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def store_metadata_of_(result, success):
    try:
        m_parser = ma_parser if success else mf_parser
        m_parser.add_section(hash_metadata(result[m_key.NAME]))
        ml.log_event(f'add is successful for \'{result[m_key.NAME]}\'')
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def write_config_to_disk():
    try:
        qconf.write_config_to_disk()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def write_parser_value_with_key_(parser_key, value, section, meta_add=False,
                                 meta_find=False, search=False, settings=False):
    # FIXME same issue as read, clunky interface, rework
    try:
        if meta_add:
            qconf.write_parser_value_with_key_(parser_key, value, section, meta_add=True)
        if meta_find:
            qconf.write_parser_value_with_key_(parser_key, value, section, meta_find=True)
        if search:
            qconf.write_parser_value_with_key_(parser_key, value, section, search=True)
        if settings:
            qconf.write_parser_value_with_key_(parser_key, value, section, settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
