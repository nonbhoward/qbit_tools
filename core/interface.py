from configparser import RawConfigParser
from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from qbit_api_interface.qbit_api_wrapper import QbitApiCaller as QApi
from string import ascii_uppercase as upper, digits
from user_configuration.settings_io import QbitConfig as QConf
digits_or_sign = f'-{digits}'
m_key, s_key, u_key = QConf.get_keyrings()
ma_parser, mf_parser, s_parser, u_parser = QConf.get_parsers()
ml = MinimalLog(__name__)
q_api = QApi()
default = 'DEFAULT'
empty = ''

u_parser_at_default = u_parser[u_key.DEFAULT]
unicode_offset = u_parser_at_default[u_key.UNI_SHIFT]


### ### ### ### ### ### ### ### ### ### ### ### GLOBAL ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                                        GLOBAL BELOW                                           #
### ### ### ### ### ### ### ### ### ### ### ### GLOBAL ### ### ### ### ### ### ### ### ### ### ### ###


def all_searches_concluded() -> bool:
    concluded_bools = [True if get_bool_from_(section, s_key.CONCLUDED) else False
                       for section in get_all_sections_from_search_parser()]
    return True if concluded_bools and all(concluded_bools) else False


def check_for_empty_string_to_replace_with_no_data_in_(string: str) -> str:
    return 'NO DATA' if empty_(string) else string


def empty_(string: str) -> bool:
    event = f'testing for empty string'
    try:
        return True if string == empty else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def exit_program() -> None:
    write_parsers_to_disk()
    event = f'exiting program'
    try:
        ml.log(event, announcement=True)
        exit()
    except RuntimeError as r_err:
        ml.log(r_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def filter_provided_for_(parser_val) -> bool:
    if isinstance(parser_val, list):
        if len(parser_val) > 1:
            return True
        try:  # FIXME p3, this works fine but could probably be improved with some thought
            parser_val = int(parser_val[0])
        except ValueError:
            return True
    return False if zero_or_neg_one_(parser_val) else True


def get_search_rank_required_to_start() -> int:
    return get_int_from_user_preference_for_(u_key.RANK_REQUIRED)


def get_tuple_of_hashed_values_for_(attribute: str, detail: str) -> tuple:
    return hash_metadata(attribute), hash_metadata(detail)


def hash_metadata(x: str, undo=False, verbose=False) -> str:
    offset = get_int_from_user_preference_for_(u_key.UNI_SHIFT)
    event = f'hashing metadata with offset \'{offset}\' for \'{x}\''
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        if verbose:
            ml.log(f'hashing..\n\t\'{x}\'\n\t\'{_hash}\'')
        return _hash
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def keyword_in_(string: str, keywords: list, require_all_kw=False) -> bool:
    event = f'checking if keywords in string'
    try:
        kw_found_indices = [kw in lower_(string) for kw in keywords]
        return all(kw_found_indices) if require_all_kw else any(kw_found_indices)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def lower_(string: str) -> str:
    event = f'converting string to lower'
    try:
        return ''.join([char.lower() if char in upper else char for char in string])
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def mega(bytes_: int) -> int:
    event = f'converting \'{bytes_}\' bytes to megabytes'
    try:
        return int(bytes_ / 1000000)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def none_value_(value) -> bool:
    event = f'checking if value \'{value}\' is None'
    try:
        return True if value is None else False
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def pause_on_event(pause_type: str, quiet=False) -> None:
    delay = get_int_from_user_preference_for_(pause_type)
    if not quiet:
        ml.log(f'waiting \'{delay}\' seconds due to user config key \'{str(pause_type)}\'')
    q_api.pause_for_(delay)  # FIXME p3, refactor this, it is silly


def print_search_ids_from_(active_search_ids: dict) -> None:
    event = f'printing search ids from active search ids'
    ml.log('active search headers are..')
    try:  # fixme p3, this was hit too frequently, ..and now it isn't hit enough..
        for active_search_header_name in active_search_ids.keys():
            ml.log(f'\tsearch header : \'{active_search_header_name}\'')
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_search_ranks() -> None:
    try:  # fixme top bug is the soft-lock this function could resolve
        scp_as_dict = get_search_parser_as_sortable()
        scp_as_sorted_list_of_tuples = sorted(scp_as_dict.items(), key=lambda k: k[1][s_key.TIME_LAST_SEARCHED])
        number_of_sections = len(scp_as_sorted_list_of_tuples)
        for ranked_search_index in range(number_of_sections):
            section = scp_as_sorted_list_of_tuples[ranked_search_index][0]
            _scp_if_set_str_for_(section, s_key.RANK, str(ranked_search_index))
            ml.log(f'search rank \'{ranked_search_index}\','
                   f' last searched at {_scp_if_get_str_at_key_(section, s_key.TIME_LAST_SEARCHED)}'
                   f' assigned to \'{section}\'')
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def validate_metadata_and_type_for_(metadata_attribute_key_string: str, metadata_detail_value: str) -> tuple:
    expected_value_types = [int, str]
    event = f'validating metadata detail value/type for ' \
            f'\'{metadata_detail_value}\' at \'{metadata_attribute_key_string}\''
    try:
        metadata_detail_value_type = type(metadata_detail_value)
        if metadata_detail_value_type not in expected_value_types:
            ex_event = f'unexpected metadata detail value type \'{metadata_detail_value_type}\''
            ml.log(ex_event, level=ml.ERROR)
            raise TypeError(ex_event)
        if metadata_detail_value_type is int:
            event = f'converting int to string'
            try:
                metadata_detail_value = str(metadata_detail_value)
            except Exception as e_err:
                ml.log(e_err.args[0], level=ml.ERROR)
                ml.log(f'error {event}')
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')
    metadata_detail_value = check_for_empty_string_to_replace_with_no_data_in_(metadata_detail_value)
    return metadata_attribute_key_string, metadata_detail_value


def value_provided_for_(value: str) -> bool:
    event = f'checking if value provided for argument'
    try:
        return False if value == '0' else True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def zero_or_neg_one_(parser_value: int) -> bool:
    event = f'checking if parser value is zero or negative one'
    try:
        return True if parser_value == -1 or parser_value == 0 else False
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


### ### ### ### ### ### ### ### ### ### ### ### GLOBAL ### ### ### ### ### ### ### ### ### ### ### ###
#                                            GLOBAL ABOVE                                            #
### ### ### ### ### ### ### ### ### ### ### ### GLOBAL ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ## RESULTS HANDLERS ## ### ### ### ### ### ### ### ### ### ###
# NEXT                                  RESULTS HANDLERS BELOW                                       #
### ### ### ### ### ### ### ### ### ### ## RESULTS HANDLERS ## ### ### ### ### ### ### ### ### ### ###


def add_successful_for_(result: dict, section: str) -> bool:
    count_before_add_attempt = get_local_results_count()
    name = get_result_metadata_at_key_(result, m_key.NAME)
    ml.log(f'\'{count_before_add_attempt}\' existing.. attempting to add \'{name}\'')
    url = get_result_metadata_at_key_(result, m_key.URL)
    add_result_from_(url, get_add_mode_for_(section))
    pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD, quiet=True)
    results_added_count = get_local_results_count() - count_before_add_attempt
    successfully_added = True if results_added_count else False
    if successfully_added:
        increment_result_added_count_for_(section)
    return successfully_added


def build_metadata_guid_from_(result: dict) -> str:
    name, url = \
        get_result_metadata_at_key_(result, m_key.NAME), get_result_metadata_at_key_(result, m_key.URL)
    if empty_(url):
        raise ValueError(f'empty url!')
    return f'{hash_metadata(name)} @ {hash_metadata(url)}'


def convert_to_hashed_metadata_from_(result: dict) -> dict:
    event = f'building hashed metadata from result'
    try:
        result[hash_metadata(m_key.GUID)] = hash_metadata(build_metadata_guid_from_(result))
        return dict({get_tuple_of_hashed_values_for_(validate_metadata_and_type_for_(attr, dtl)[0],
                                                     validate_metadata_and_type_for_(attr, dtl)[1])
                     for attr, dtl in result.items()})
    except Exception as e_err:
        ml.log(f'error {event}')
        ml.log(e_err.args[0])


def enough_results_found_in_(results_filtered: list, section: str) -> bool:
    results_found_count = 0 if none_value_(results_filtered) else len(results_filtered)
    event = f'checking if filtered_results is valid and has a length'
    try:
        assert results_filtered is not None, ml.log(f'filtered results should not be None', ml.ERROR)
        if results_found_count < get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT):
            ml.log(f'not enough results were found! \'{results_found_count}\' results '
                   f'found, consider adjusting search and filter parameters', level=ml.WARNING)
            return False
        ml.log(f'search yielded adequate results, \'{results_found_count}\' results found')
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def previously_found_(result: dict, verbose=False) -> bool:
    result_name = build_metadata_guid_from_(result)
    results_added_or_failed = [*ma_parser.sections(), *mf_parser.sections()]
    event = f'checking if previously found result \'{result}\''
    try:
        if result_name in results_added_or_failed:
            if verbose:  # FIXME p4, pull this out to some surface object init
                ml.log(f'old result found, skipping \'{result_name}\'', level=ml.WARNING)
            return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')
    if verbose:
        ml.log(f'new result found \'{result_name}\'')
    return False


def reduce_search_expectations_if_not_enough_results_found_in_(results_filtered: list, section: str) -> None:
    if not enough_results_found_in_(results_filtered, section):
        _scp_if_reduce_search_expectations_for_(section)


def sort_(results: list) -> list:
    event = f'sorting results'
    try:  # TODO dynamic sort values
        return sorted(results, key=lambda k: k[m_key.SUPPLY], reverse=True)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def write_new_metadata_section_from_(result: dict, added=False) -> None:
    create_metadata_section_for_(ma_parser if added else mf_parser,
                                 convert_to_hashed_metadata_from_(result))


### ### ### ### ### ### ### ### ### ### ## RESULTS HANDLERS ## ### ### ### ### ### ### ### ### ### ###
#                                       RESULTS HANDLERS ABOVE                                       #
### ### ### ### ### ### ### ### ### ### ## RESULTS HANDLERS ## ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ## SECTION HANDLERS ## ### ### ### ### ### ### ### ### ### ###
# NEXT                                  SECTION HANDLERS BELOW                                       #
### ### ### ### ### ### ### ### ### ### ## SECTION HANDLERS ## ### ### ### ### ### ### ### ### ### ###


def enough_results_added_for_(section: str) -> bool:
    event = f'comparing results added to results required'
    try:
        return True if get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT) >= \
                       get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT) else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_keywords_to_add_from_(section: str) -> list:
    kw_to_add_csv = get_str_from_search_parser_at_(section, s_key.KEYWORDS_ADD)
    event = f'building keywords to add from \'{section}\' into iterable'
    try:
        return [kw.strip() for kw in kw_to_add_csv.split(sep=',')]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_keywords_to_skip_from_(section: str) -> list:
    kw_to_skip_csv = get_str_from_search_parser_at_(section, s_key.KEYWORDS_SKIP)
    event = f'building keywords to skip from \'{section}\' into iterable'
    try:
        return [kw.strip() for kw in kw_to_skip_csv.split(sep=',')]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_state_concluded_for_(section: str) -> bool:
    return get_search_state_from_state_machine_for_(section)
    return get_search_state_from_parser_for_(section)[3]  # FIXME p3, not used


def get_state_queued_for_(section: str) -> bool:
    return get_search_state_from_parser_for_(section)[0]  # FIXME p3, not used


def get_state_running_for_(section: str) -> bool:
    return get_search_state_from_parser_for_(section)[1]  # FIXME p3, not used


def get_state_stopped_for_(section: str) -> bool:
    return get_search_state_from_parser_for_(section)[2]  # FIXME p3, not used


def print_search_state_for_(section: str) -> None:
    search_queued, search_running, search_stopped, search_concluded = get_search_state_from_parser_for_(section)
    ml.log(f'search state for \'{section}\': '
           f'\n\tqueued: {search_queued}'
           f'\n\trunning: {search_running}'
           f'\n\tstopped: {search_stopped}'
           f'\n\tconcluded: {search_concluded}', announcement=True)


def ready_to_start_at_(section: str) -> bool:
    queued = get_search_state_from_parser_for_(section)[0]
    event = f'checking if search is queued and rank is allowed'
    try:
        search_rank_allowed = get_search_rank_for_(section) <= get_search_rank_required_to_start()
        if not queued:
            return False
        if not search_rank_allowed:
            ml.log(f'search at \'{section}\' is disallowed due to search rank', level=ml.WARNING)
            return False
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_search_states_for_(section: str, search_states) -> None:
    _scp_if_set_search_states_for_(section, search_states)
    event = f'extracting search states from tuple'
    try:
        ml.log(f'search state for \'{section}\': '
               f'\n\tqueued: {search_states[0]}'
               f'\n\trunning: {search_states[1]}'
               f'\n\tstopped: {search_states[2]}'
               f'\n\tconcluded: {search_states[3]}', announcement=True)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


### ### ### ### ### ### ### ### ### ### ## SECTION HANDLERS ## ### ### ### ### ### ### ### ### ### ###
#                                       SECTION HANDLERS ABOVE                                       #
### ### ### ### ### ### ### ### ### ### ## SECTION HANDLERS ## ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### STATE HANDLERS ### ### ### ### ### ### ### ### ### ### ###
# NEXT                               STATE MACHINE HANDLERS BELOW                                    #
### ### ### ### ### ### ### ### ### ### ### STATE HANDLERS ### ### ### ### ### ### ### ### ### ### ###


def active_section_is_in_memory_of_(state_machine) -> bool:
    active_section = get_active_section_from_(state_machine)
    active_sections = get_active_sections_from_(state_machine)
    return True if active_section in active_sections else False


def add_filtered_results_stored_in_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    results_filtered = get_results_filtered_from_(state_machine)
    for result in results_filtered:
        result_name = get_result_metadata_at_key_(result, m_key.NAME)
        if search_is_concluded_at_active_section_in_(state_machine):
            return  # FIXME p2, is this state reachable? should it be?
        if add_successful_for_(result, section):  # FIXME p0, sometimes this adds two values
            write_new_metadata_section_from_(result, added=True)
            if enough_results_added_for_(section):
                ml.log(f'enough results added for \'{section}\'')
                return  # desired result count added, stop adding
            continue  # result added, go to next
        ml.log(f'client failed to add \'{result_name}\'', level=ml.WARNING)


def conclude_search_for_active_section_in_(state_machine) -> None:
    set_bool_for_(get_active_section_from_(state_machine), s_key.QUEUED, False)
    set_bool_for_(get_active_section_from_(state_machine), s_key.RUNNING, False)
    set_bool_for_(get_active_section_from_(state_machine), s_key.STOPPED, False)
    set_bool_for_(get_active_section_from_(state_machine), s_key.CONCLUDED, True)
    delete_section_from_active_searches_in_(state_machine)


def delete_section_from_active_searches_in_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    active_sections = get_active_sections_from_(state_machine)
    event = f'deleting active section \'{state_machine.active_section}\' from state machine'
    try:
        if section in active_sections:
            del state_machine.active_sections[state_machine.active_section]
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def filter_results_in_(state_machine, found=True, sort=True, verbose=False) -> list:
    results_filtered_and_sorted = list()
    section = get_active_section_from_(state_machine)
    seeds_min = get_int_from_search_parser_at_(section, s_key.MIN_SEED)
    bytes_min = get_int_from_search_parser_at_(section, s_key.SIZE_MIN_BYTES)
    bytes_max = get_int_from_search_parser_at_(section, s_key.SIZE_MAX_BYTES)
    megabytes_min = mega(bytes_min)
    megabytes_max = mega(bytes_max) if bytes_max != -1 else bytes_max
    keywords_to_add = get_keywords_to_add_from_(section)
    keywords_to_skip = get_keywords_to_skip_from_(section)
    results_filtered = list()
    for idx, result_unfiltered in enumerate(get_results_unfiltered_from_(state_machine)):
        result_name = get_result_metadata_at_key_(result_unfiltered, m_key.NAME)
        if found and previously_found_(result_unfiltered):
            continue  # filter this result
        if filter_provided_for_(seeds_min):
            result_seeds = int(get_result_metadata_at_key_(result_unfiltered, m_key.SUPPLY))  # FIXME p2, fetch int natively
            enough_seeds = True if result_seeds > seeds_min else False
            if not enough_seeds:
                if verbose:
                    ml.log(f'required seeds \'{seeds_min}\' not met by result with '
                           f'\'{result_seeds}\' seeds, result : \'{result_name}\'',
                           level=ml.WARNING)
                write_new_metadata_section_from_(result_unfiltered)  # remember this result
                continue  # filter this result
        if filter_provided_for_(megabytes_min) or filter_provided_for_(megabytes_max):
            bytes_result = int(get_result_metadata_at_key_(result_unfiltered, m_key.SIZE))
            megabytes_result = mega(bytes_result)
            if filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                file_size_in_range = True if bytes_max > bytes_result > bytes_min else False
            elif not filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                file_size_in_range = True if bytes_max > bytes_result else False
            else:
                file_size_in_range = True if bytes_result > bytes_min else False
            if not file_size_in_range:
                if verbose:
                    ml.log(f'size requirement \'{megabytes_min}\'mib to \'{megabytes_max}\'mib not met by '
                           f'result with size \'{megabytes_result}\'mib, result: \'{result_name}\'',
                           level=ml.WARNING)
                write_new_metadata_section_from_(result_unfiltered)  # remember this result
                continue  # filter this result
        if filter_provided_for_(keywords_to_add):
            if idx == 0:  # FIXME p2, this does nothing, rework
                ml.log(f'filtering results for \'{section}\' using add keywords \'{keywords_to_add}\'')
            filename = get_result_metadata_at_key_(result_unfiltered, m_key.NAME)
            if keyword_in_(filename, keywords_to_skip) or not keyword_in_(filename, keywords_to_add):
                if True:  # FIXME p1, replace True with verbose flag, forces log
                    ml.log(f'keyword requirements have not been met by '
                           f'\'{result_name}\'', level=ml.WARNING)
                write_new_metadata_section_from_(result_unfiltered)  # remember this result
                continue  # filter this result
        ml.log(f'result \'{result_name}\' meets all requirements')
        results_filtered.append(result_unfiltered)
    if sort:
        ml.log(f'sorting results for \'{section}\'')
        results_filtered_and_sorted = sort_(results_filtered)
    reduce_search_expectations_if_not_enough_results_found_in_(results_filtered_and_sorted, section)
    return results_filtered_and_sorted


def get_search_state_for_active_section_in_(state_machine) -> tuple:
    section = get_active_section_from_(state_machine)
    search_states = get_search_state_from_parser_for_(section)
    ml.log(f'search state for \'{section}\': '
           f'\n\tqueued: {search_states[0]}'
           f'\n\trunning: {search_states[1]}'
           f'\n\tstopped: {search_states[2]}'
           f'\n\tconcluded: {search_states[3]}', announcement=True)
    return search_states


def get_search_term_for_active_section_in_(state_machine) -> str:
    return get_search_term_for_(get_active_section_from_(state_machine))


def increment_search_attempt_count_in_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    increment_search_attempt_count_for_(section)


def increment_search_state_at_active_section_for_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'incrementing search state for \'{section}\''
    try:  # fixme p1, worked out bugs, comment left as reminder, delete me soon
        search_state = get_search_state_for_active_section_in_(state_machine)
        queued, running, stopped, concluded = search_state
        if queued:
            queued, running = False, True
            ml.log(f'{event} from queued to running')
        elif running:
            running, stopped = False, True
            ml.log(f'{event} from running to stopped')
            increment_search_attempt_count_for_(section)
        elif stopped:
            stopped = False
            # concluded = True if search_is_concluded_in_(state_machine) else False
            concluded = True if search_is_concluded_at_active_section_in_(state_machine) else False
            queued = True if not concluded else False
        elif concluded:
            ml.log(f'search for \'{section}\' concluded, cannot increment')
        search_states = queued, running, stopped, concluded
        set_search_states_for_(section, search_states)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def ready_to_start_at_active_section_in_(state_machine) -> bool:
    ready_to_start = ready_to_start_at_(state_machine.active_section)
    queue_full = search_queue_is_full_in_(state_machine)
    return ready_to_start if not queue_full else False


def reset_search_state_at_active_section_for_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'resetting search state at \'{section}\''
    ml.log(event, level=ml.WARNING)
    try:
        queued, running, stopped, concluded = True, False, False, False
        search_states = queued, running, stopped, concluded
        set_search_states_for_(section, search_states)
        delete_section_from_active_searches_in_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def save_results_to_(state_machine, save_results_filtered=True) -> None:
    save_search_results_unfiltered_to_(state_machine)
    if save_results_filtered:
        save_search_results_filtered_to_(state_machine)


def search_is_concluded_at_active_section_in_(state_machine) -> bool:
    return get_bool_from_search_parser_at_(state_machine.active_section, s_key.CONCLUDED)


def search_is_running_at_active_section_in_(state_machine) -> bool:
    status = _stm_if_get_search_properties_from_(state_machine)[2]
    if none_value_(status):
        return False
    return True if s_key.RUNNING in status else False


def search_is_stopped_at_active_section_in_(state_machine) -> bool:
    status = _stm_if_get_search_properties_from_(state_machine)[2]
    if none_value_(status):
        return False
    return True if s_key.STOPPED in status else False


def search_queue_is_full_in_(state_machine) -> bool:
    active_search_dict = get_active_search_dict_from_(state_machine)
    section = get_active_section_from_(state_machine)
    event = f'checking if search queue full'
    try:
        active_searches_running = len(active_search_dict)
        if active_searches_running < q_api.concurrent_searches_allowed:
            ml.log(f'search queue is not full, '
                   f'\'{q_api.concurrent_searches_allowed - active_searches_running}\' '
                   f'spaces available')
            if active_searches_running:
                print_search_ids_from_(active_search_dict)
            return False
        ml.log(f'search queue is full, cannot add \'{section}\'', level=ml.WARNING)
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_started_for_(state_machine) -> bool:
    return True if get_active_section_from_(state_machine) in \
                   get_active_sections_from_(state_machine) else False


def set_time_last_searched_for_active_section_in_(state_machine) -> None:
    set_time_last_searched_for_(get_active_section_from_(state_machine))


def start_search_with_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    search_term = get_search_term_for_active_section_in_(state_machine)
    search_properties = create_search_job_for_(search_term, 'all', 'all')
    add_search_properties_to_(state_machine, search_properties)
    search_id = ''
    event = f'starting search for active section'
    try:
        search_id = get_search_id_from_active_section_in_(state_machine)
        write_search_id_to_search_parser_at_(section, search_id)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')
    if search_is_stored_in_(state_machine):
        ml.log(f'search \'{search_term}\' successfully started for \'{section}\' with id \'{search_id}\'')
        set_time_last_searched_for_active_section_in_(state_machine)
        increment_search_state_at_active_section_for_(state_machine)
        return
    ml.log(f'stale search, bad search status and/or bad search id, re-queueing \'{section}\'', level=ml.WARNING)
    reset_search_state_at_active_section_for_(state_machine)


### ### ### ### ### ### ### ### ### ### ### STATE HANDLERS ### ### ### ### ### ### ### ### ### ### ###
#                                    STATE MACHINE HANDLERS ABOVE                                    #
### ### ### ### ### ### ### ### ### ### ### STATE HANDLERS ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ## WRAPPERS ## ### ### ### ### ### ### ### ### ### ### ###
# NEXT                                      WRAPPERS BELOW                                           #
### ### ### ### ### ### ### ### ### ### ### ## WRAPPERS ## ### ### ### ### ### ### ### ### ### ### ###


def add_result_from_(url: str, is_paused: bool) -> None:
    _api_if_add_result_from_(url, is_paused)


def add_search_properties_to_(state_machine, search_properties: tuple) -> None:
    _stm_if_add_search_properties_to_(state_machine, search_properties)


def create_metadata_section_for_(mp: RawConfigParser, hashed_result: dict) -> None:
    _mdp_if_create_section_for_(mp, hashed_result)


def create_search_job_for_(pattern: str, plugins: str, category: str) -> tuple:
    return _api_if_create_search_job_for_(pattern, plugins, category)


def get_active_search_dict_from_(state_machine) -> dict:
    return _stm_if_get_active_search_dict_from_(state_machine)


def get_active_section_from_(state_machine) -> str:
    return _stm_if_get_active_section_from_(state_machine)


def get_active_sections_from_(state_machine) -> list:
    return _stm_if_get_active_sections_from_(state_machine)


def get_add_mode_for_(section: str) -> bool:
    return _scp_if_get_add_mode_for_(section)


def get_all_sections_from_metadata_parsers() -> tuple:
    return _mdp_if_get_all_sections_from_metadata_parsers()


def get_all_sections_from_user_config_parser() -> list:
    return _ucp_if_get_all_sections_from_user_config_parser()


def get_all_sections_from_search_parser() -> list:
    return _scp_if_get_all_sections_from_search_parser()


def get_bool_from_(section: str, key: str) -> bool:
    return _scp_if_get_bool_from_(section, key)


def get_connection_time_start() -> dt:
    return _api_if_get_connection_time_start()


def get_bool_from_search_parser_at_(section: str, key: str) -> bool:
    return _scp_if_get_bool_at_key_(section, key)  # FIXME p3, not used


def get_int_from_search_parser_at_(section: str, key: str) -> int:
    return _scp_if_get_int_at_key_(section, key)


def get_local_results_count() -> int:
    return _api_if_get_local_results_count()


def get_result_metadata_at_key_(result_unfiltered, key: str) -> str:
    return _mdp_if_get_result_metadata_at_key_(key, result_unfiltered)


def get_results_filtered_from_(state_machine) -> list:
    return _stm_if_get_results_filtered_from_(state_machine)


def get_results_unfiltered_from_(state_machine):
    return _stm_if_get_results_unfiltered_from_(state_machine)


def get_int_from_user_preference_for_(key: str):
    return _ucp_if_get_int_for_key_(key)


def get_search_parser() -> RawConfigParser:
    return _search_parser()


def get_str_from_search_parser_at_(section: str, key: str) -> str:
    return _scp_if_get_str_at_key_(section, key)


def get_search_id_from_active_section_in_(state_machine) -> str:
    return _stm_if_get_search_id_from_active_section_in_(state_machine)


def get_search_parser_as_sortable() -> dict:
    event = f'getting search parser as sortable to prepare for search ranking'
    try:
        search_parser = get_search_parser()
        parser_as_sortable = dict()
        for section in search_parser.sections():
            if search_parser[section].getboolean(s_key.CONCLUDED):
                continue
            parser_as_sortable[section] = dict()
            for key in search_parser[section]:
                parser_as_sortable[section][key] = search_parser[section][key]
        return parser_as_sortable
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_rank_for_(section: str) -> int:
    return _scp_if_get_int_at_key_(section, s_key.RANK)


def get_search_results_for_(state_machine) -> list:
    return _api_if_get_search_results_for_(state_machine)


def get_search_state_from_parser_for_(section: str) -> tuple:
    return _scp_if_get_search_state_for_(section)


def get_search_state_from_state_machine_for_(section: str) -> tuple:
    return _api_if_get_search_properties_at_(section)


def get_search_term_for_(section: str) -> str:
    return _scp_if_get_search_term_for_(section)


def increment_result_added_count_for_(section: str) -> None:
    _scp_if_increment_result_added_count_for_(section)


def increment_search_attempt_count_for_(section: str) -> None:
    _scp_if_increment_search_attempt_count_for_(section)


def save_search_results_filtered_to_(state_machine) -> None:
    _stm_if_save_filtered_search_results_to_(state_machine)


def save_search_results_unfiltered_to_(state_machine) -> None:
    _stm_if_save_unfiltered_search_results_to_(state_machine)


def search_at_active_section_has_completed_in_(state_machine) -> bool:
    return _scp_if_search_at_active_section_has_completed_in_(state_machine)


def search_is_stored_in_(state_machine) -> bool:
    return _stm_if_api_search_is_stored_in_(state_machine)


def set_active_section_to_(section: str, state_machine) -> None:
    _stm_if_set_active_section_to_(section, state_machine)


def set_bool_for_(section: str, key: str, boolean: bool) -> None:
    _scp_if_set_bool_for_(section, key, boolean)


def set_time_last_read_for_(section: str) -> None:
    _scp_if_set_time_last_read_for_(section)


def set_time_last_searched_for_(section: str) -> None:
    _scp_if_set_time_last_searched_for_(section)


def update_search_properties_from_api_for_(state_machine) -> None:
    if active_section_is_in_memory_of_(state_machine):
        _stm_if_update_search_properties_from_api_for_(state_machine)


def write_parsers_to_disk() -> None:
    _cfg_if_write_parsers_to_disk()


def write_search_id_to_search_parser_at_(section: str, search_id: str) -> None:
    _scp_if_set_str_for_(section, s_key.ID, search_id)


### ### ### ### ### ### ### ### ### ### ### ## WRAPPERS ## ### ### ### ### ### ### ### ### ### ### ###
# NEXT                                      WRAPPERS ABOVE                                           #
### ### ### ### ### ### ### ### ### ### ### ## WRAPPERS ## ### ### ### ### ### ### ### ### ### ### ###


### ### ### ### ### ### ### ### ### ### ### ## EXTERNAL ## ### ### ### ### ### ### ### ### ### ### ###
### ### ### ### ### ### ### ### ### ### ### # INTERFACES # ### ### ### ### ### ### ### ### ### ### ###
### ### ### ### ### ### ### ### ### ### ### # START HERE # ### ### ### ### ### ### ### ### ### ### ###


### ### ### ### ### ### ### ### ### ### ### ### API IF ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                                   API INTERFACE BELOW                                         #
### ### ### ### ### ### ### ### ### ### ### ### API IF ### ### ### ### ### ### ### ### ### ### ### ###


def _api_if_add_result_from_(url: str, is_paused: bool) -> None:
    q_api.add_result_from_(url, is_paused)


def _api_if_create_search_job_for_(pattern: str, plugins: str, category: str) -> tuple:
    return q_api.create_search_job(pattern, plugins, category)


def _api_if_get_connection_time_start() -> dt:
    return q_api.get_connection_time_start()


def _api_if_get_local_results_count() -> int:
    return q_api.get_count_of_local_results()


def _api_if_get_search_properties_at_(section: str) -> tuple:  # FIXME multiple calls
    search_id = _scp_if_get_search_id_for_(section)
    if empty_(search_id):
        ml.log(f'search id empty at \'{section}\'', level=ml.WARNING)
        return None, None, None
    return _api_if_get_search_properties_for_(search_id)


def _api_if_get_search_results_for_(state_machine) -> list:
    search_id = get_search_id_from_active_section_in_(state_machine)
    if empty_(search_id):
        ex_event = f'search id for active section \'{state_machine.active_section}\' is empty string'
        ml.log(ex_event, level=ml.WARNING)
        raise ValueError(ex_event)
    results = q_api.get_result_object_at_(search_id)
    if none_value_(results):
        ex_event = f'result object from api is None'
        ml.log(ex_event, level=ml.ERROR)
        raise ValueError(ex_event)
    return results[m_key.RESULTS]


def _api_if_get_search_properties_for_(search_id: str) -> tuple:
    return q_api.get_search_properties_for_(search_id=search_id)


### ### ### ### ### ### ### ### ### ### ### ### API IF ### ### ### ### ### ### ### ### ### ### ### ###
#                                        API INTERFACE ABOVE                                         #
### ### ### ### ### ### ### ### ### ### ### ### API IF ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### CFG IF ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                                    CFG INTERFACE BELOW                                        #
### ### ### ### ### ### ### ### ### ### ### ### CFG IF ### ### ### ### ### ### ### ### ### ### ### ###


def _cfg_if_set_parser_value_at_(section: str, parser_key: str, value,
                                 mp=None, search=True, settings=False):  # FIXME multiple calls
    try:  # todo deprecate this func
        if mp:
            QConf.write_parser_section_with_key_(parser_key, value, section, mp)
        elif settings:
            QConf.write_parser_section_with_key_(parser_key, value, section, settings=settings)
        elif search:  # must be last since search defaults True
            QConf.write_parser_section_with_key_(parser_key, value, section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _cfg_if_write_parsers_to_disk():
    QConf.write_config_state_to_disk()


### ### ### ### ### ### ### ### ### ### ### ### CFG IF ### ### ### ### ### ### ### ### ### ### ### ###
#                                         CFG INTERFACE ABOVE                                        #
### ### ### ### ### ### ### ### ### ### ### ### CFG IF ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### MDP IF ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                              METADATA PARSER INTERFACE BELOW                                  #
### ### ### ### ### ### ### ### ### ### ### ### MDP IF ### ### ### ### ### ### ### ### ### ### ### ###


def _metadata_added_parser(section=empty) -> RawConfigParser:
    event = f'getting metadata added parser at \'{section}\'' if section else f'getting metadata added parser'
    try:
        if not empty_(section):
            assert section in ma_parser.sections(), KeyError(f'section \'{section}\' not in parser')
        return ma_parser[section] if not empty_(section) else ma_parser
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _metadata_failed_parser(section=empty) -> RawConfigParser:
    event = f'getting metadata failed parser at \'{section}\'' if section else f'getting metadata failed parser'
    try:
        if not empty_(section):
            assert section in mf_parser.sections(), KeyError(f'section \'{section}\' not in parser')
        return mf_parser[section] if not empty_(section) else mf_parser
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_create_section_for_(mp: RawConfigParser, hashed_result: dict) -> None:
    hashed_result_guid = hashed_result[hash_metadata(m_key.GUID)]  # FIXME p2, get this out of low lvl ifs
    event = f'creating metadata parser section'
    try:
        if mp.has_section(hashed_result_guid):
            ml.log(f'metadata parser already has section \'{hashed_result_guid}\'', level=ml.ERROR)
            return
        mp.add_section(hashed_result_guid)
        for hashed_attribute, hashed_detail in hashed_result.items():
            _cfg_if_set_parser_value_at_(hashed_result_guid, hashed_attribute, hashed_detail, mp)
        return
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_get_all_sections_from_metadata_parsers() -> tuple:
    try:
        return *_metadata_added_parser().sections(), *_metadata_failed_parser().sections()
    except Exception as e_err:
        ml.log(e_err.args[0])


def _mdp_if_get_metadata_from_(parser: RawConfigParser) -> dict:  # FIXME no calls
    event = f'getting metadata from parser'
    try:
        ml.log('fetching results from disk', event_completed=False)
        result_data = dict()
        for section in parser.sections():
            result_data[hash_metadata(section, True)] = dict()
            for key, detail in parser[section].items():
                result_data[hash_metadata(section, True)][key] = hash_metadata(detail, True)
        ml.log('fetching results from disk', event_completed=True)
        return result_data
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_get_result_metadata_at_key_(key: str, result: dict) -> str:  # QConf
    event = f'getting result metadata at key \'{key}\''
    try:  # fixme should this interface to QConf be re-thought?
        return QConf.get_result_metadata_at_key_(key, result)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_previously_found_(result: dict, verbose_log=True) -> bool:  # FIXME no calls
    event = f'checking if previously found result \'{result}\''
    try:
        result_name = build_metadata_guid_from_(result)
        added_or_found = [*ma_parser.sections(), *mf_parser.sections()]
        if result_name in added_or_found:
            if verbose_log:
                ml.log(f'old result found, skipping \'{result_name}\'', level=ml.WARNING)
            return True
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_write_metadata_from_(result: dict, added=False) -> None:  # FIXME no calls
    try:
        pass
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ### ### ### ### MDP IF ### ### ### ### ### ### ### ### ### ### ### ###
#                                   METADATA PARSER INTERFACE ABOVE                                  #
### ### ### ### ### ### ### ### ### ### ### ### MDP IF ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### SCP IF ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                               SEARCH PARSER INTERFACE BELOW                                   #
### ### ### ### ### ### ### ### ### ### ### ### SCP IF ### ### ### ### ### ### ### ### ### ### ### ###


def _search_parser(section=empty):  # FIXME excessive calls
    event = f'getting search parser for \'{section}\''
    try:  # parser surface abstraction depth = 0
        if not empty_(section):
            assert section in s_parser.sections(), KeyError(f'section \'{section}\' not in parser')
        return s_parser[section] if not empty_(section) else s_parser
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error' + event)


def _scp_if_get_add_mode_for_(section: str) -> bool:
    event = f'getting add mode for \'{section}\''
    try:  # parser surface abstraction depth = 0
        return _scp_if_get_bool_from_(section, s_key.ADD_PAUSED)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def _scp_if_get_all_sections_from_search_parser() -> list:
    try:  # parser surface abstraction depth = 0
        return _search_parser().sections()
    except Exception as e_err:
        ml.log(e_err.args[0])


def _scp_if_get_bool_from_(section: str, key: str) -> bool:  # FIXME multiple calls
    try:  # parser surface abstraction depth = 1
        return _search_parser(section).getboolean(key)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_get_bool_at_key_(section: str, key: str) -> bool:
    event = f'getting bool value for search parser section \'{section}\' at \'{key}\''
    try:  # parser surface abstraction depth = 1
        return _search_parser(section).getboolean(key)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_get_int_at_key_(section: str, key: str) -> int:  # FIXME multiple calls
    event = f'getting int value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        integer_as_str = _scp_if_get_str_at_key_(section, key)
        for char in integer_as_str:  # fixme this would allow values like -79 but also 7-9 which would error
            if char not in digits_or_sign:
                raise TypeError(f'unexpected character while ' + event)
        return int(integer_as_str)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_get_str_at_key_(section: str, key: str) -> str:  # FIXME multiple calls
    event = f'getting str value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        string = str(_search_parser(section)[key])
        return string
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_get_search_id_for_(section: str) -> str:
    try:
        search_id = _scp_if_get_str_at_key_(section, s_key.ID)
        return search_id
    except Exception as e_err:
        ml.log(e_err.args[0])


def _scp_if_get_search_state_for_(section) -> tuple:
    try:  # parser surface abstraction depth = 2
        _scp_if_set_str_for_(section, s_key.TIME_LAST_READ, str(dt.now()))  # fixme move to function
        search_queued = _scp_if_get_bool_from_(section, s_key.QUEUED)
        search_running = _scp_if_get_bool_from_(section, s_key.RUNNING)
        search_stopped = _scp_if_get_bool_from_(section, s_key.STOPPED)
        search_concluded = _scp_if_get_bool_from_(section, s_key.CONCLUDED)
        return search_queued, search_running, search_stopped, search_concluded
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_get_search_term_for_(section: str) -> str:
    try:
        search_term = _scp_if_get_str_at_key_(section, s_key.TERM)
        return search_term if value_provided_for_(search_term) else section
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_increment_result_added_count_for_(section: str) -> None:
    event = f'incrementing result added count for \'{section}\''
    key = s_key.RESULTS_ADDED_COUNT
    try:  # parser surface abstraction depth = 1
        results_added = str(get_int_from_search_parser_at_(section, key) + 1)
        _search_parser(section)[key] = results_added
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_increment_search_attempt_count_for_(section: str) -> None:
    try:  # fixme bring into compliance with standard interface functions
        search_attempt_count = _scp_if_get_int_at_key_(section, s_key.SEARCH_ATTEMPT_COUNT)
        ml.log(f'search try counter at \'{search_attempt_count}\', incrementing..')
        _scp_if_set_int_for_(section, s_key.SEARCH_ATTEMPT_COUNT, search_attempt_count + 1)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_reduce_search_expectations_for_(section: str) -> None:
    event = f'reducing search expectations for \'{section}\''
    try:
        c_key, re_key = s_key.CONCLUDED, s_key.RESULTS_REQUIRED_COUNT
        ml.log(f'reducing search expectations for \'{section}\'')
        er_val = int(s_parser[section][re_key])
        if not er_val:
            ml.log(f'concluding search for \'{section}\'', level=ml.WARNING)
            s_parser[section][c_key] = s_key.YES
        er_val -= 1
        _cfg_if_set_parser_value_at_(section, re_key, er_val)  # fixme fix args
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_search_at_active_section_has_completed_in_(state_machine) -> bool:
    section = _stm_if_get_active_section_from_(state_machine)
    event = f'checking if search has yielded required results for \'{section}\''
    try:
        search_attempt_count = _scp_if_get_int_at_key_(section, s_key.SEARCH_ATTEMPT_COUNT)
        search_attempt_count_max = _scp_if_get_int_at_key_(section, s_key.MAX_SEARCH_COUNT)
        results_added = _scp_if_get_int_at_key_(section, s_key.RESULTS_ADDED_COUNT)
        results_required = _scp_if_get_int_at_key_(section, s_key.RESULTS_REQUIRED_COUNT)
        if results_added >= results_required:
            _scp_if_set_end_reason_for_(section, s_key.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
            return True
        if search_attempt_count >= search_attempt_count_max:
            _scp_if_set_end_reason_for_(section, s_key.TIMED_OUT)  # too many search attempts, conclude
            return True
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_set_bool_for_(section: str, key: str, boolean: bool):  # FIXME multiple calls
    try:  # parser surface abstraction depth = 1
        _search_parser(section)[key] = s_key.YES if boolean else s_key.NO
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_set_end_reason_for_(section, reason_key):  # FIXME multiple calls
    event = f'setting end reason for \'{section}\' with reason \'{reason_key}\''
    try:  # parser surface abstraction depth = 2
        ml.log(f'search \'{section}\' can be concluded, \'{reason_key}\'')
        _scp_if_set_str_for_(section, s_key.SEARCH_STOPPED_REASON, reason_key)
        if all_searches_concluded():
            exit_program()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_set_int_for_(section: str, key: str, integer: int) -> None:
    event = f'setting int value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        _search_parser(section)[key] = str(integer)
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_set_search_id_for_(section: str, search_id: str) -> None:  # FIXME no calls
    try:  # parser surface abstraction depth = 2
        _scp_if_set_str_for_(section, s_key.ID, search_id)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_set_search_states_for_(section, search_states) -> None:
    try:
        queued, running, stopped, concluded = search_states
        _scp_if_set_bool_for_(section, s_key.QUEUED, queued)
        _scp_if_set_bool_for_(section, s_key.RUNNING, running)
        _scp_if_set_bool_for_(section, s_key.STOPPED, stopped)
        _scp_if_set_bool_for_(section, s_key.CONCLUDED, concluded)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_set_str_for_(section: str, key: str, string: str):  # FIXME multiple calls
    event = f'setting str value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 0
        _search_parser(section)[key] = string
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_set_time_last_read_for_(section: str) -> None:
    try:  # parser surface abstraction depth = 2
        _scp_if_set_str_for_(section, s_key.TIME_LAST_READ, str(dt.now()))
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_set_time_last_searched_for_(section: str) -> None:
    try:  # parser surface abstraction depth = 2
        _scp_if_set_str_for_(section, s_key.TIME_LAST_SEARCHED, str(dt.now()))
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ### ### ### ### SCP IF ### ### ### ### ### ### ### ### ### ### ### ###
#                                    SEARCH PARSER INTERFACE ABOVE                                   #
### ### ### ### ### ### ### ### ### ### ### ### SCP IF ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### STM IF ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                               STATE MACHINE INTERFACE BELOW                                   #
### ### ### ### ### ### ### ### ### ### ### ### STM IF ### ### ### ### ### ### ### ### ### ### ### ###


def _stm_if_add_search_properties_to_(state_machine, search_properties: tuple) -> None:
    section = _stm_if_get_active_section_from_(state_machine)
    event = f'adding search properties to state machine'
    try:  # machine surface abstraction depth = 0
        _stm_if_init_active_search_id_for_(state_machine, section)
        state_machine.active_sections[section]['count'] = search_properties[0]
        state_machine.active_sections[section]['id'] = search_properties[1]
        state_machine.active_sections[section]['status'] = search_properties[2]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def _stm_if_get_active_search_dict_from_(state_machine) -> dict:  # FIXME multiple calls
    event = f'getting active search dict from state machine'
    try:  # machine surface abstraction depth = 1
        return state_machine.active_sections
    except Exception as e_err:
        ml.log(f'error {event}')
        ml.log(e_err.args[0])


def _stm_if_get_active_section_from_(state_machine) -> str:  # FIXME multiple calls
    event = f'getting active section from state machine'
    try:  # machine surface abstraction depth = 0
        return state_machine.active_section
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def _stm_if_get_active_sections_from_(state_machine) -> list:
    # fixme this returns dict or list? it works as-is but.. need to be sure
    event = f'getting active section from state machine'
    try:  # machine surface abstraction depth = 0
        return state_machine.active_sections
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_active_section_search_id_from_(state_machine) -> str:  # FIXME no calls
    try:  # machine surface abstraction depth = 1
        section = _stm_if_get_active_section_from_(state_machine)
        return state_machine.active_sections[section]['id']
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_results_filtered_from_(state_machine):
    event = f'getting filtered results from state machine'
    section = _stm_if_get_active_section_from_(state_machine)
    try:  # FIXME p1, how to handle empty or None results?
        return state_machine.active_sections[section]['filtered_results']
        # if results_filtered is None:
        #     ml.log(f'invalid search results at \'{section}\'', level=ml.WARNING)
        #     reset_search_state_at_active_section_for_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def _stm_if_get_search_id_from_(state_machine, section) -> str:  # FIXME multiple calls
    try:  # machine surface abstraction depth = 0
        return state_machine.active_sections[section]['id']
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_search_id_from_active_section_in_(state_machine) -> str:
    try:
        section = state_machine.active_section
        return _stm_if_get_search_id_from_(state_machine, section)
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_search_properties_from_(state_machine) -> tuple:  # FIXME multiple calls
    # todo just noting this object has two surfaces, could be useful
    try:  # machine surface abstraction depth = 0
        if state_machine.active_section in state_machine.active_sections:
            active_section_dict = state_machine.active_sections[state_machine.active_section]
            count, sid, status = active_section_dict['count'], \
                                 active_section_dict['id'], \
                                 active_section_dict['status']
            return count, sid, status
        return None, None, None
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_get_results_unfiltered_from_(state_machine):
    section = _stm_if_get_active_section_from_(state_machine)
    event = f'getting results unfiltered from state machine'
    try:
        return state_machine.active_sections[section]['unfiltered_results']
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def _stm_if_init_active_search_id_for_(state_machine, section: str) -> None:
    try:  # machine surface abstraction depth = 0
        state_machine.active_sections[section] = dict()
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_save_filtered_search_results_to_(state_machine):
    # fixme p0, interface function relies on wrapper function, should be opposite
    section = _stm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        filtered_results = filter_results_in_(state_machine)
        # sm_if_update_search_properties_for_(state_machine)  # tODO delete me
        state_machine.active_sections[section]['filtered_results'] = filtered_results
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_save_unfiltered_search_results_to_(state_machine):
    section = _stm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        unfiltered_results = get_search_results_for_(state_machine)
        update_search_properties_from_api_for_(state_machine)
        state_machine.active_sections[section]['unfiltered_results'] = unfiltered_results
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_api_search_is_stored_in_(state_machine) -> bool:
    section = state_machine.active_section
    try:  # machine surface abstraction depth = 1
        search_count, search_id, search_status = _api_if_get_search_properties_at_(section)
        active_search_dict = _stm_if_get_active_search_dict_from_(state_machine)
        return True if search_id in active_search_dict[section]['id'] else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_set_active_section_to_(section: str, state_machine):
    try:
        state_machine.active_section = section
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_update_search_properties_from_api_for_(state_machine) -> None:
    section = _stm_if_get_active_section_from_(state_machine)
    count, sid, status = _api_if_get_search_properties_at_(section)
    try:
        if not none_value_(count):
            state_machine.active_sections[section]['count'] = count
            # state_machine.active_sections[section]['id'] = sid  # no need to update search id
            state_machine.active_sections[section]['status'] = status
    except Exception as e_err:
        ml.log(e_err.args[0])


### ### ### ### ### ### ### ### ### ### ### ### STM IF ### ### ### ### ### ### ### ### ### ### ### ###
#                                    STATE MACHINE INTERFACE ABOVE                                   #
### ### ### ### ### ### ### ### ### ### ### ### STM IF ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### UCP IF ### ### ### ### ### ### ### ### ### ### ### ###
# NEXT                            USER CONFIG PARSER INTERFACE BELOW                                 #
### ### ### ### ### ### ### ### ### ### ### ### UCP IF ### ### ### ### ### ### ### ### ### ### ### ###


def _user_configuration(section=empty):  # FIXME multiple calls
    event = f'getting user config parser at \'{section}\'' if not empty_(section) else f'getting user config parser'
    try:
        if section:
            if section != default:
                ml.log(f'the section value \'{section}\' may be an issue', level=ml.WARNING)
        # ml.log(f'ignoring user section \'{section}\'.. setting to \'{default}\'')  # FIXME p3, too spammy
        section = default  # FIXME p3, this is a dumb patch, fix it later
        return u_parser[section] if not empty_(section) else u_parser
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _ucp_if_get_all_sections_from_user_config_parser() -> list:
    event = f'getting all sections from user config parser'
    try:
        return _user_configuration().sections()
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def _ucp_if_get_int_for_key_(key: str) -> int:
    event = f'getting int from user configuration parser with key \'{key}\''
    try:  # fixme handle diff return types, str/int/etc
        val = _user_configuration(default)[key]
        for char in val:  # FIXME this would allow values like -79 but also 7-9 which would error
            if char not in digits_or_sign:
                raise TypeError(f'unexpected character in value for key \'{key}\'')
        return int(val)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _ucp_if_get_str_for_key_(key: str) -> str:  # FIXME no calls
    event = f'getting str from user configuration parser with key \'{key}\''
    try:
        val = _user_configuration(default)[key]
        return str(val)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


### ### ### ### ### ### ### ### ### ### ### ### UCP IF ### ### ### ### ### ### ### ### ### ### ### ###
#                                 USER CONFIG PARSER INTERFACE ABOVE                                 #
### ### ### ### ### ### ### ### ### ### ### ### UCP IF ### ### ### ### ### ### ### ### ### ### ### ###
