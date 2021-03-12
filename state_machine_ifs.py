from configparser import RawConfigParser, SectionProxy
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_interface.api_comm import QbitApiCaller as QApi
from string import digits
from user_configuration.settings_io import QbitConfig as QConf
digits_or_sign = digits + '-'
ml = MinimalLog(__name__)
q_api = QApi()
m_key, s_key, u_key = QConf.get_keyrings()
ma_parser, mf_parser, s_parser, u_parser = QConf.get_parsers()


def add_results_from_(results: list, active_kv: tuple):
    try:
        section = active_kv[0]
        results = filter_(results, section)
        evaluate_filtered_results_for_(section, results)
        results_required_count = sp_if_get_int_from_(section, s_key.RESULTS_REQUIRED_COUNT)
        ml.log_event(f'add most popular \'{results_required_count}\' count results')
        for result in results:
            results_added_count = sp_if_get_int_from_(section, s_key.RESULTS_ADDED_COUNT)
            if results_added_count > results_required_count:  # FIXME p2, shouldn't this use the conclusion check func?
                ml.log_event(f'the search for \'{section}\' can be concluded', announce=True)
                sp_if_set_bool_for_(section, s_key.CONCLUDED, True)
                return  # enough results have been added for this header, stop
            if add_successful_for_(result, section):  # FIXME p0, sometimes this adds two values
                add_to_metadata_parsers_as_(result, added=True)
                if enough_results_added_for_(section):
                    ml.log_event(f'enough results added for \'{section}\'')
                    return  # desired result count added, stop adding
                cfg_if_write_to_disk()  # FIXME p0, debug line, consider removing
                continue  # result added, go to next
            result_name = cfg_if_get_result_metadata_at_key_(result, m_key.NAME)
            ml.log_event(f'client failed to add \'{result_name}\'', level=ml.WARNING)
            cfg_if_write_to_disk()  # FIXME p0, debug line, consider removing
    except Exception as e_err:
        ml.log_event(f'error adding results from \'{active_kv}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def add_successful_for_(result: dict, section: str) -> bool:
    try:
        count_before_add_attempt = api_if_get_local_results_count()
        ml.log_event(f'local machine has {count_before_add_attempt} stored results before add attempt..')
        # TODO why does client fail to add so often? outside project scope?
        url = cfg_if_get_result_metadata_at_key_(result, m_key.URL)
        api_if_add_result_from_(url, get_add_mode_for_(section))
        pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
        results_added_count = api_if_get_local_results_count() - count_before_add_attempt
        successfully_added = True if results_added_count else False
        if successfully_added:
            increment_result_added_count_for_(section)
        return successfully_added
    except Exception as e_err:
        ml.log_event(f'error checking if add successful for \'{result}\' at \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def add_to_metadata_parsers_as_(result: dict, added=False) -> None:  # FIXME metadata debug entry
    try:
        mp_if_create_section_for_(ma_parser if added else mf_parser, result)
    except Exception as e_err:
        ml.log_event(f'error adding \'{result}\' to metadata parsers', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def all_searches_concluded() -> bool:
    try:
        concluded_bools = list()
        for section in search_parser().sections():
            concluded_bool = True if sp_if_get_bool_from_(section, s_key.CONCLUDED) else False
            concluded_bools.append(concluded_bool)
        if concluded_bools and all(concluded_bools):
            ml.log_event(f'all searches concluded', level=ml.WARNING)
            return True
        ml.log_event(f'all searches are not concluded, program continuing')
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if all searches concluded', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def build_metadata_section_from_(result: dict) -> str:
    try:
        name, url = \
            cfg_if_get_result_metadata_at_key_(result, m_key.NAME), \
            cfg_if_get_result_metadata_at_key_(result, m_key.URL)
        if url == '':
            raise ValueError(f'empty url!')
        r_name, delim, r_url = hash_metadata(name), ' @ ', hash_metadata(url)
        hashed_name = r_name + delim + r_url
        return hashed_name
    except Exception as e_err:
        ml.log_event(f'error building metadata section from \'{result}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def check_for_no_data_in_(value: str) -> str:
    """
    1. if value is empty string, return NO DATA for parser write
    :param value: test value to be checked for empty string
    :return: 'NO DATA' if empty string
    """
    try:
        return 'NO DATA' if value == '' else value
    except Exception as e_err:
        ml.log_event(f'error checking data in value \'{value}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def empty_(test_string: str) -> bool:
    try:
        if test_string == '':
            return True
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if empty \'{test_string}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def enough_results_added_for_(section: str) -> bool:
    try:
        results_added_count = int(s_parser[section][s_key.RESULTS_ADDED_COUNT])
        results_required_count = int(s_parser[section][s_key.RESULTS_REQUIRED_COUNT])
        if results_added_count >= results_required_count:  # TODO check that indexing is perfect
            return True
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if enough results added for \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def enough_results_found_in_(section: str, filtered_results: list) -> bool:
    try:
        expected_results_count = int(s_parser[section][s_key.RESULTS_REQUIRED_COUNT])
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
        ml.log_event(f'error checking if enough results found in \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def evaluate_filtered_results_for_(section: str, filtered_results: list) -> None:
    try:
        if not enough_results_found_in_(section, filtered_results):
            reduce_search_expectations_for_(section)
    except Exception as e_err:
        ml.log_event(f'error evaluating search result quality for \'{section}')
        ml.log_event(e_err.args[0], level=ml.ERROR)


def exit_program():
    try:
        ml.log_event(f'writing all parsers to disk')
        cfg_if_write_to_disk()
        ml.log_event(f'exiting program')
        exit()
    except Exception as e_err:
        ml.log_event(f'error exiting program', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def fetch_metadata_from_(parser) -> dict:
    try:
        ml.log_event('fetching results from disk', event_completed=False)
        result_data = dict()
        for section in parser.sections():
            result_data[hash_metadata(section, True)] = dict()
            for key, detail in parser[section].items():
                result_data[hash_metadata(section, True)][key] = hash_metadata(detail, True)
        ml.log_event('fetching results from disk', event_completed=True)
        return result_data
    except Exception as e_err:
        ml.log_event(f'error fetching metadata from parser \'{parser}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def filter_(results: list, section: str, found=True, sort=True):
    """
    1. get search priority
    :param results: results returned from the api
    :param section: the active section of the search parser
    :param found: bool, True = don't parse previously failed results
    :param sort: bool, True = sort by key determined elsewhere
    :return:
    """
    try:
        sps_at_active = search_parser(section)
        seeds_min = int(read_parser_value_with_(s_key.MIN_SEED, section))
        bytes_min = int(read_parser_value_with_(s_key.SIZE_MIN_BYTES, section))
        bytes_max = int(read_parser_value_with_(s_key.SIZE_MAX_BYTES, section))
        megabytes_min = mega(bytes_min)
        megabytes_max = mega(bytes_max) if bytes_max != -1 else bytes_max
        filename_regex = read_parser_value_with_(s_key.REGEX_FILENAME, section)
        results_filtered = list()
        for result in results:
            result_name = cfg_if_get_result_metadata_at_key_(result, m_key.NAME)
            if found and previously_found_(result):
                continue
            if filter_provided_for_(seeds_min):
                result_seeds = cfg_if_get_result_metadata_at_key_(result, m_key.SUPPLY)  # FIXME int
                enough_seeds = True if result_seeds > seeds_min else False
                if not enough_seeds:
                    ml.log_event(f'required seeds \'{seeds_min}\' not met by result with '
                                 f'\'{result_seeds}\' seeds, result : \'{result_name}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    add_to_metadata_parsers_as_(result)
                    continue
            if filter_provided_for_(megabytes_min) or filter_provided_for_(megabytes_max):
                bytes_result = cfg_if_get_result_metadata_at_key_(result, m_key.SIZE)  # FIXME int
                megabytes_result = mega(bytes_result)
                if filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                    file_size_in_range = True if bytes_max > bytes_result > bytes_min else False
                elif not filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                    file_size_in_range = True if bytes_max > bytes_result else False
                else:
                    file_size_in_range = True if bytes_result > bytes_min else False
                if not file_size_in_range:
                    ml.log_event(f'size requirement \'{megabytes_min}\'MiB to \'{megabytes_max}\'MiB not met by '
                                 f'result with size \'{megabytes_result}\'MiB, result: \'{result_name}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    add_to_metadata_parsers_as_(result)
                    continue
            if filter_provided_for_(filename_regex):
                ml.log_event(f'filtering results using filename regex \'{filename_regex}\'')
                filename = cfg_if_get_result_metadata_at_key_(result, m_key.NAME)
                if not q_api.regex_matches(filename_regex, filename):
                    ml.log_event(f'regex \'{filename_regex}\' does not match for \'{filename}\'', level=ml.WARNING)
                    add_to_metadata_parsers_as_(result)
                    continue
            ml.log_event(f'result \'{result_name}\' meets all requirements')
            results_filtered.append(result)
        if sort:
            ml.log_event(f'results sorted for {section} # TODO dynamic sort values')
            results = sort_(results_filtered)
        return results
    except Exception as e_err:
        ml.log_event(f'error encountered filtering results at result \'{result}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def filter_provided_for_(parser_val: int) -> bool:
    try:
        return False if parser_val == -1 or parser_val == 0 else True
    except Exception as e_err:
        ml.log_event(f'error checking if filter provided for \'{parser_val}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_add_mode_for_(section: str) -> bool:
    try:
        return s_parser[section].getboolean(s_key.ADD_PAUSED)
    except Exception as e_err:
        ml.log_event(f'error getting add mode for \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0])


def get_all_sections_from_parser_(meta_add=False, meta_find=False, search=False, settings=False):
    try:
        if meta_add:
            return QConf.get_all_sections_from_parser_(meta_add=True)
        if meta_find:
            return QConf.get_all_sections_from_parser_(meta_find=True)
        if search:
            return QConf.get_all_sections_from_parser_(search=True)
        if settings:
            return QConf.get_all_sections_from_parser_(settings=True)
    except Exception as e_err:
        ml.log_event(f'error getting all sections from parser', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_hashed_(attribute: str, detail: str, offset: int) -> str:
    try:
        return hash_metadata(attribute, offset), hash_metadata(detail, offset)
    except Exception as e_err:
        ml.log_event(f'error getting hashed attribute detail for \'{attribute}\' \'{detail}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_id_from_(state_machine) -> str:
    try:  # FIXME label arg QbitStateMachine without recursion import?
        search_id = ''
        if state_machine.active_section in state_machine.active_search_ids:
            search_id = state_machine.active_search_ids[state_machine.active_section]
            ml.log_event(f'search id \'{search_id}\' successfully fetched')
        return search_id
    except Exception as e_err:
        ml.log_event(f'error getting search id from state machine', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_results_for_(active_kv: tuple) -> list:
    try:
        results = q_api.get_result_object_from_(search_id=active_kv[1])
        assert results is not None, 'bad results, fix it or handle it'
        results = results[m_key.RESULTS]  # TODO do this? or no?
        return results
    except Exception as e_err:
        ml.log_event(f'error getting search results for \'{active_kv}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def hash_metadata(x: str, undo=False, offset=0) -> str:
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        ml.log_event(f'hashed from.. \n\t\t\'{x}\' to.. \n\t\t\'{_hash}\'')
        return _hash
    except Exception as e_err:
        ml.log_event(f'error hashing metadata \'{x}\' with offset \'{offset}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def increment_result_added_count_for_(section: str) -> None:
    try:
        s_parser[section][s_key.RESULTS_ADDED_COUNT] = \
            str(int(s_parser[section][s_key.RESULTS_ADDED_COUNT]) + 1)
    except Exception as e_err:
        ml.log_event(f'error incrementing result added count for \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def mega(bytes_: int) -> int:
    try:
        megabytes_ = int(bytes_ / 1000000)
        return megabytes_
    except Exception as e_err:
        ml.log_event(f'error converting \'{bytes_}\' bytes to megabytes', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def meta_parser_add_section_to_(mp, hashed_section_name):
    try:
        if hashed_section_name in mp.sections():
            ml.log_event(f'section name already exists for \'{hashed_section_name}\'', level=ml.WARNING)
            return
        ml.log_event(f'adding section name for \'{hashed_section_name}\'')
        mp.add_section(hashed_section_name)
    except Exception as e_err:
        ml.log_event(f'error adding section to metadata parser \'{hashed_section_name}\'')
        ml.log_event(e_err.args[0], level=ml.ERROR)


def pause_on_event(pause_type: str):
    try:
        parser_at_default = u_parser[u_key.DEFAULT]
        delay = int(parser_at_default[pause_type])
        ml.log_event(f'waiting \'{delay}\' seconds for event \'{str(pause_type)}\'')
        q_api.pause_for_(delay)
    except Exception as e_err:
        ml.log_event(f'error pausing on event \'{pause_type}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def previously_found_(result: dict, verbose_log=True) -> bool:
    try:
        result_name = build_metadata_section_from_(result)
        added_or_found = [*ma_parser.sections(), *mf_parser.sections()]
        if result_name in added_or_found:
            if verbose_log:
                ml.log_event(f'old result found, skipping \'{result_name}\'', level=ml.WARNING)
            return True
        ml.log_event(f'new result found \'{result_name}\'')
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if previously found \'{result}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def print_search_ids_from_(active_search_ids: dict):
    try:  # FIXME p3, this is hit too frequently
        ml.log_event('active search headers are..')
        for active_search_header_name in active_search_ids.keys():
            ml.log_event(f'\tsearch header : \'{active_search_header_name}\'')
    except Exception as e_err:
        ml.log_event(f'error printing search ids from \'{active_search_ids}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def read_parser_value_with_(key: str, section: str,
                            meta_add=False, meta_find=False,
                            search=True, settings=False):
    # TODO this interface is lazy, above is a bool, and what is below? this is needlessly confusing
    # FIXME p2, address TODO
    try:
        if meta_add:
            return QConf.read_parser_value_with_(key, section, meta_add=meta_add)
        elif meta_find:
            return QConf.read_parser_value_with_(key, section, meta_find=meta_find)
        elif settings:
            return QConf.read_parser_value_with_(key, section, settings=settings)
        elif search:  # MUST be last since defaults true
            return QConf.read_parser_value_with_(key, section)
    except Exception as e_err:
        ml.log_event(f'error reading parser value with \'{key}\' at \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def ready_to_start_(queued: bool, state_machine) -> bool:
    try:  # FIXME labal arg QbitStateMachine without recursive import?
        search_rank = int(s_parser[state_machine.active_section][s_key.RANK])
        search_rank_required_to_start = int(u_parser[u_key.DEFAULT][u_key.RANK_REQUIRED])
        queue_has_room = not state_machine.search_queue_full()
        search_rank_allowed = search_rank <= search_rank_required_to_start
        if queued and queue_has_room and search_rank_allowed:
            return True
        return False
    except Exception as e_err:
        ml.log_event(f'error checking if ready to start', level=ml.ERROR)
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
        cfg_if_write_parser_value_with_(section, re_key, er_val)  # FIXME fix args
    except Exception as e_err:
        ml.log_event(f'error reducing search expectations for \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def result_has_enough_seeds(result) -> bool:
    try:
        ml.log_event(f'TODO result_has_enough_seeds()')
        pass  # TODO refactor into this function?
        return True
    except Exception as e_err:
        ml.log_event(f'error checking if enough seeds at result \'{result}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def search_has_yielded_required_results(section: str) -> bool:
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
        ml.log_event(f'error checking if search yielded required results at \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def search_set_end_reason(section, reason_key):
    try:
        ml.log_event(f'ending search at \'{section}\' with reason \'{reason_key}\'')
        sp_if_set_str_for_(section, s_key.SEARCH_STOPPED_REASON, reason_key)
        if all_searches_concluded():
            exit_program()
    except Exception as e_err:
        ml.log_event(f'error setting search end reason \'{reason_key}\' for \'{section}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_search_rank_using_(sort_key: str):
    try:
        sdp_as_dict = cfg_if_get_search_parser_as_sortable()
        sdp_as_dict_sorted = sorted(sdp_as_dict.items(), key=lambda k: k[1][sort_key])
        number_of_sections = len(sdp_as_dict_sorted)
        for search_rank in range(number_of_sections):
            # TODO this is a bit lazy, could use some refining
            header = sdp_as_dict_sorted[search_rank][0]
            s_parser[header][s_key.RANK] = str(search_rank)
            ml.log_event(f'search rank \'{search_rank}\' assigned to header \'{header}\'')
    except Exception as e_err:
        ml.log_event(f'error setting search rank using key \'{sort_key}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_time_last_searched_for_active_header():
    try:
        pass  # TODO refactor into this function?
    except Exception as e_err:
        ml.log_event(f'error setting time last searched for header', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sort_(results: list) -> list:
    try:
        return sorted(results, key=lambda k: k['nbSeeders'], reverse=True)  # FIXME remove hardcode
    except Exception as e_err:
        ml.log_event(f'error sorting results', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def validate_metadata_type_for_(metadata_kv: tuple) -> tuple:
    parser_key, value = metadata_kv  # FIXME reminder, WAS a bug, be sure it doesn't happen again
    try:
        expected_types = [int, str]
        value_type = type(value)
        if value_type not in expected_types:
            ex = f'unexpected data type \'{value_type}\''
            ml.log_event(ex, level=ml.ERROR)
            raise TypeError(ex)
        if value_type is int:
            try:
                value = str(value)
            except Exception as e_err:
                ml.log_event(f'unable to convert int to string', level=ml.ERROR)
                ml.log_event(e_err.args[0], level=ml.ERROR)
        value = check_for_no_data_in_(value)
        return parser_key, value
    except Exception as e_err:
        ml.log_event(f'error validating metadata type for \'{metadata_kv}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


#### ### ### ### ### ### ### ### ### ### API INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                     API INTERFACE BELOW                                            #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### API INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
def api_if_add_result_from_(url: str, is_paused: bool):
    try:
        q_api.add_result_from_(url, is_paused)
    except Exception as e_err:
        ml.log_event(f'api error adding result from \'{url}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def api_if_get_local_results_count():
    try:
        return q_api.get_local_results_count()
    except Exception as e_err:
        ml.log_event(f'api error getting local results count', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def api_if_create_search_job_for_(pattern: str, plugins: str, category: str) -> tuple:
    try:
        job = q_api.qbit_client.search.start(pattern, plugins, category)
        assert job is not None, 'bad search job, fix it or handle it'
        count, sid, status = q_api.get_search_info_from_(job)
        ml.log_event(f'qbit client created search job for \'{pattern}\'')
        return count, sid, status
    except Exception as e_err:
        ml.log_event(f'api error creating search job for \'{pattern}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def api_if_get_connection_time_start():
    try:
        return q_api.get_connection_time_start()
    except Exception as e_err:
        ml.log_event(f'api error getting connection time start')
        ml.log_event(e_err.args[0], level=ml.ERROR)


def api_if_get_search_status_for_(search_id: str) -> str:
    try:
        return q_api.get_search_status_for_(search_id=search_id)
    except Exception as e_err:
        ml.log_event(f'api error getting search status for \'{search_id}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


#### ### ### ### ### ### ### ### ### ### API INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                     API INTERFACE ABOVE                                            #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### API INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#### ### ### ### ### ### ### ### ### ### CFG INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                     CFG INTERFACE BELOW                                            #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### CFG INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
def cfg_if_get_result_metadata_at_key_(result: dict, key: str) -> str:  # QConf
    try:
        return QConf.get_result_metadata_at_key_(result, key)
    except Exception as e_err:
        ml.log_event(f'cfg error getting result metadata at key \'{key}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def cfg_if_get_search_parser_as_sortable():
    try:
        return QConf.get_search_parser_as_sortable()
    except Exception as e_err:
        ml.log_event(f'cfg error getting search parser as sortable', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def cfg_if_write_parser_value_with_(section: str, parser_key: str, value,
                                    mp=None, search=True, settings=False):
    try:  # FIXME p2, keep value type handling in mind (datetime, int, else?)
        if mp:
            QConf.write_parser_section_with_key_(parser_key, value, section, mp)
        elif settings:
            QConf.write_parser_section_with_key_(parser_key, value, section, settings=settings)
        elif search:  # MUST be last since search defaults true
            QConf.write_parser_section_with_key_(parser_key, value, section)
    except Exception as e_err:
        ml.log_event(f'cfg error writing parser value at \'{section}\' for key \'{parser_key}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def cfg_if_write_to_disk():
    try:
        QConf.write_config_to_disk()
    except Exception as e_err:
        ml.log_event(f'cfg error writing to disk', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


#### ### ### ### ### ### ### ### ### ### CFG INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                     CFG INTERFACE ABOVE                                            #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### CFG INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
### ### ### ### ### ### ### ### # METADATA PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ####
#                                                                                                    #
#                              METADATA PARSER INTERFACE BELOW                                       #
#                                                                                                    #
### ### ### ### ### ### ### ### # METADATA PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ####
def metadata_parser(section: str, successful_add=False):
    try:
        mp = ma_parser if successful_add else mf_parser
        return mp[section] if section else mp
    except Exception as e_err:
        error = f'error getting metadata parser'
        event = error + f' at \'{section}\'' if section else error
        ml.log_event(event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def mp_if_create_section_for_(mp: RawConfigParser, result: dict) -> None:
    try:
        offset = int(u_parser[u_key.DEFAULT][u_key.UNI_SHIFT])
        result_name = cfg_if_get_result_metadata_at_key_(result, m_key.NAME)
        ml.log_event(f'save metadata result to parser \'{result_name}\'')
        m_section = hash_metadata(build_metadata_section_from_(result), offset=offset)
        if mp.has_section(m_section):
            ml.log_event(f'metadata parser already has section \'{m_section}\'', level=ml.WARNING)
            return
        mp.add_section(m_section)
        result_name = cfg_if_get_result_metadata_at_key_(result, m_key.NAME)
        ml.log_event(f'section has been added to metadata result \'{result_name}\' for header \'{m_section}\'', announce=True)
        for metadata_kv in result.items():
            attribute, detail = validate_metadata_type_for_(metadata_kv)
            h_attr, h_dtl = get_hashed_(attribute, detail, offset)
            # FIXME p3, this will break due to bad parser arg.. revisiting, resolved?
            cfg_if_write_parser_value_with_(m_section, h_attr, h_dtl, mp)
            pause_on_event(u_key.WAIT_FOR_USER)
        return
    except Exception as e_err:
        ml.log_event(f'error creating metadata section for \'{result}\'', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### # METADATA PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ####
#                                                                                                    #
#                              METADATA PARSER INTERFACE ABOVE                                       #
#                                                                                                    #
### ### ### ### ### ### ### ### # METADATA PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ####
### ### ### ### ### ### ### ### ## SEARCH PARSER INTERFACE ## ### ### ### ### ### ### ### ### ### ####
#                                                                                                    #
#                               SEARCH PARSER INTERFACE BELOW                                        #
#                                                                                                    #
### ### ### ### ### ### ### ### ## SEARCH PARSER INTERFACE ## ### ### ### ### ### ### ### ### ### ####
def search_parser(section=''):
    try:
        return s_parser[section] if not empty_(section) else s_parser
    except Exception as e_err:
        error = f'error getting search parser'
        event = error + f' at \'{section}\'' if section else error
        ml.log_event(event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sp_if_get_bool_from_(section: str, key: str) -> bool:
    try:
        event = f'getting bool value for search parser at \'{key}\''
        val_bool = search_parser(section).getboolean(key)
        ml.log_event(event)
        return val_bool
    except Exception as e_err:
        ml.log_event(f'error ' + event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sp_if_get_int_from_(section: str, key: str) -> int:
    try:
        event = f'getting int value for search parser at \'{key}\''
        integer = search_parser(section)[key]
        ml.log_event(event)
        for char in integer:  # FIXME this would allow values like -79 but also 7-9 which would error
            if char not in digits_or_sign:
                raise TypeError(f'unexpected character while ' + event)
        return int(integer)
    except Exception as e_err:
        ml.log_event(f'error ' + event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sp_if_get_str_from_(section: str, key: str) -> str:
    try:
        event = f'getting str value for search parser at \'{key}\''
        string = search_parser(section)[key]
        ml.log_event(event)
        return str(string)
    except Exception as e_err:
        ml.log_event(f'error ' + event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sp_if_set_bool_for_(section: str, key: str, boolean: bool):
    try:
        event = f'setting bool value for search parser at \'{key}\''
        ml.log_event(event)
        search_parser(section)[key] = boolean
    except Exception as e_err:
        ml.log_event(f'error ' + event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sp_if_set_int_for_(section: str, key: str, integer: int):
    try:
        event = f'setting int value for search parser at \'{key}\''
        ml.log_event(event)
        search_parser(section)[key] = str(integer)
    except Exception as e_err:
        ml.log_event(f'error ' + event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def sp_if_set_str_for_(section: str, key: str, string: str):
    try:
        event = f'setting str value for search parser at \'{key}\''
        ml.log_event(event)
        search_parser(section)[key] = string
    except Exception as e_err:
        ml.log_event(f'error ' + event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ## SEARCH PARSER INTERFACE ## ### ### ### ### ### ### ### ### ### ####
#                                                                                                    #
#                               SEARCH PARSER INTERFACE ABOVE                                        #
#                                                                                                    #
### ### ### ### ### ### ### ### ## SEARCH PARSER INTERFACE ## ### ### ### ### ### ### ### ### ### ####
### ### ### ### ### ### ### ### USER CONFIG PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                            USER CONFIG PARSER INTERFACE BELOW                                      #
#                                                                                                    #
### ### ### ### ### ### ### ### USER CONFIG PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ###
def uc_if_get_int_from_(ucf_at_active: SectionProxy, ucf_key: str) -> int:
    try:  # TODO input user config parser isn't "at active"
        val = ucf_at_active[ucf_key]
        ml.log_event(f'returning int \'{val}\' from search parser')
        for char in val:  # FIXME this would allow values like -79 but also 7-9 which would error
            if char not in digits_or_sign:
                raise TypeError(f'unexpected character in value for key \'{ucf_key}\'')
        return int(val)
    except Exception as e_err:
        ml.log_event(f'error getting value from search parser at active section', level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


def user_config_parser(section: str):
    try:
        if section != 'DEFAULT':
            ml.log_event(f'the section value \'{section}\' may be an issue', level=ml.WARNING)
        return u_parser[section] if section else u_parser
    except Exception as e_err:
        error = f'error getting user config parser'
        event = error + f' at \'{section}\'' if section else error
        ml.log_event(event, level=ml.ERROR)
        ml.log_event(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### USER CONFIG PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                            USER CONFIG PARSER INTERFACE ABOVE                                      #
#                                                                                                    #
### ### ### ### ### ### ### ### USER CONFIG PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ###
