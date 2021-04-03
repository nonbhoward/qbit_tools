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


def all_searches_concluded() -> bool:
    concluded_bools = [True if get_bool_from_(section, s_key.CONCLUDED) else False
                       for section in get_all_sections_from_search_parser()]
    if concluded_bools and all(concluded_bools):
        ml.log(f'all searches concluded', level=ml.WARNING)
        return True
    ml.log(f'all searches not concluded')
    return False


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
    ml.log(f'exiting program')
    write_parsers_to_disk()
    exit()


def filter_provided_for_(parser_val) -> bool:
    return False if zero_or_neg_one_(parser_val) else True


def get_hashed_(attribute: str, detail: str) -> tuple:
    return hash_metadata(attribute), hash_metadata(detail)


def get_search_rank_required_to_start() -> int:
    return get_int_from_user_preference_for_(u_key.RANK_REQUIRED)


def hash_metadata(x: str, undo=False) -> str:
    offset = get_int_from_user_preference_for_(u_key.UNI_SHIFT)
    event = f'hashing metadata with offset \'{offset}\' for \'{x}\''
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
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


def pause_on_event(pause_type: str) -> None:
    delay = get_int_from_user_preference_for_(pause_type)
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
        scp_as_sorted_list_of_tuples = sorted(scp_as_dict.items(), key=lambda k: k[1][s_key.time_last_searched])
        number_of_sections = len(scp_as_sorted_list_of_tuples)
        for ranked_search_index in range(number_of_sections):
            section = scp_as_sorted_list_of_tuples[ranked_search_index][0]
            _scp_if_set_str_for_(section, s_key.rank, str(ranked_search_index))
            ml.log(f'search rank \'{ranked_search_index}\' assigned to \'{section}\'')
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def validate_metadata_and_type_for_(metadata_attribute: str, metadata_detail: str) -> tuple:
    expected_value_types = [int, str]
    parser_key, parser_value = metadata_attribute, metadata_detail
    event = f'validating metadata and type for \'{parser_value}\' at \'{parser_key}\''
    try:
        parser_value_type = type(parser_value)
        if parser_value_type not in expected_value_types:
            ex_event = f'unexpected parser value type \'{parser_value_type}\''
            ml.log(ex_event, level=ml.ERROR)
            raise TypeError(ex_event)
        if parser_value_type is int:
            event = f'converting int to string'
            try:
                parser_value = str(parser_value)
            except Exception as e_err:
                ml.log(e_err.args[0], level=ml.ERROR)
                ml.log(f'error {event}')
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')
    parser_value = check_for_empty_string_to_replace_with_no_data_in_(parser_value)
    return parser_key, parser_value


def value_provided_for_(value: str) -> bool:
    event = f'checking if value provided for \'{value}\''
    try:  # TODO could this be combined with the filter checker?
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


### ### ### ### ### ### ### ### ### ### ## results handlers ## ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                       results handlers below                                       #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ## results handlers ## ### ### ### ### ### ### ### ### ### ###


def add_successful_for_(result: dict, section: str) -> bool:
    count_before_add_attempt = get_local_results_count()
    ml.log(f'local machine has {count_before_add_attempt} stored results before add attempt..')
    url = get_result_metadata_at_key_(result, m_key.URL)
    add_result_from_(url, get_add_mode_for_(section))
    pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
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
        return dict({get_hashed_(validate_metadata_and_type_for_(attr, dtl)[0],
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
                   f'found, consider adjusting search parameters', level=ml.WARNING)
            return False
        ml.log(f'search yielded adequate results, \'{results_found_count}\' results found')
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def previously_found_(result: dict, verbose_log=True) -> bool:
    result_name = build_metadata_guid_from_(result)
    event = f'checking if previously found result \'{result}\''
    try:
        added_or_failed = [*ma_parser.sections(), *mf_parser.sections()]
        if result_name in added_or_failed:
            if verbose_log:  # FIXME p4, pull this out to some surface object init
                ml.log(f'old result found, skipping \'{result_name}\'', level=ml.WARNING)
            return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')
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


### ### ### ### ### ### ### ### ### ### ## results handlers ## ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                       results handlers above                                       #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ## results handlers ## ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ## section handlers ## ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                       section handlers below                                       #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ## section handlers ## ### ### ### ### ### ### ### ### ### ###


def enough_results_added_for_(section: str) -> bool:
    event = f'comparing results added to results required'
    try:
        return True if get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT) >= \
                       get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT) else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_concluded_state_for_(section: str) -> bool:
    return get_search_state_for_(section)[3]  # FIXME p3, not used


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


def get_queued_state_for_(section: str) -> bool:
    return get_search_state_for_(section)[0]  # FIXME p3, not used


def get_running_state_for_(section: str) -> bool:
    return get_search_state_for_(section)[1]  # FIXME not used


def get_stopped_state_for_(section: str) -> bool:
    return get_search_state_for_(section)[2]  # FIXME not used


def print_search_state_for_(section: str) -> None:
    search_queued, search_running, search_stopped, search_concluded = get_search_state_for_(section)
    ml.log(f'search state for \'{section}\': '
           f'\n\tqueued: {search_queued}'
           f'\n\trunning: {search_running}'
           f'\n\tstopped: {search_stopped}'
           f'\n\tconcluded: {search_concluded}', announcement=True)


def ready_to_start_at_(section: str) -> bool:
    queued = get_search_state_for_(section)[0]
    event = f'checking if search is queued and rank is allowed'
    try:
        search_rank_allowed = get_search_rank_for_(section) <= get_search_rank_required_to_start()
        return True if queued and search_rank_allowed else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_search_states_for_(section: str, *search_states) -> None:
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


### ### ### ### ### ### ### ### ### ### ## section handlers ## ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                       section handlers above                                       #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ## section handlers ## ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### state machine handlers ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    state machine handlers below                                    #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### state machine handlers ### ### ### ### ### ### ### ### ### ###


def active_section_is_in_memory_of_(state_machine) -> bool:
    return True if get_active_section_from_(state_machine) in \
                   get_active_sections_from_(state_machine) else False


def add_filtered_results_stored_in_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    for result in get_results_filtered_from_(state_machine):
        result_name = get_result_metadata_at_key_(result, m_key.NAME)
        if search_is_concluded_in_(state_machine):
            return  # FIXME p2, is this state reachable? should it be?
        if add_successful_for_(result, section):  # FIXME p0, sometimes this adds two values
            write_new_metadata_section_from_(result, added=True)
            if enough_results_added_for_(section):
                ml.log(f'enough results added for \'{section}\'')
                return  # desired result count added, stop adding
            continue  # result added, go to next
        ml.log(f'client failed to add \'{result_name}\'', level=ml.WARNING)


def conclude_search_for_active_section_in_(state_machine) -> None:
    set_bool_for_(get_active_section_from_(state_machine), s_key.CONCLUDED, True)


def filter_results_in_(state_machine, found=True, sort=True) -> list:
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
    for result_unfiltered in get_results_unfiltered_from_(state_machine):
        result_name = get_result_metadata_at_key_(result_unfiltered, m_key.NAME)
        if found and previously_found_(result_unfiltered):
            continue  # filter this result
        if filter_provided_for_(seeds_min):
            result_seeds = int(get_result_metadata_at_key_(result_unfiltered, m_key.SUPPLY))  # FIXME p2, fetch int natively
            enough_seeds = True if result_seeds > seeds_min else False
            if not enough_seeds:
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
                ml.log(f'size requirement \'{megabytes_min}\'mib to \'{megabytes_max}\'mib not met by '
                       f'result with size \'{megabytes_result}\'mib, result: \'{result_name}\'',
                       level=ml.WARNING)
                write_new_metadata_section_from_(result_unfiltered)  # remember this result
                continue  # filter this result
        if filter_provided_for_(keywords_to_add):
            # fixme p0, entry point for continued implementation of add/skip keyword paradigm
            ml.log(f'filtering results using add keywords \'{keywords_to_add}\'')
            filename = get_result_metadata_at_key_(result_unfiltered, m_key.NAME)
            if keyword_in_(filename, keywords_to_skip) or not keyword_in_(filename, keywords_to_add):
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
    return get_search_state_for_(get_active_section_from_(state_machine))


def get_search_term_for_active_section_in_(state_machine) -> str:
    return get_search_term_for_(get_active_section_from_(state_machine))


def increment_search_state_at_active_section_for_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'incrementing search state for \'{section}\''
    try:
        try:  # fixme p1, worked out bugs, comment left as reminder, delete me soon
            search_state = get_search_state_for_active_section_in_(state_machine)
            queued, running, stopped, concluded = search_state
            if queued:
                queued, running = False, True
                ml.log(f'{event} from queued to running, please wait for search to complete')
            elif running:
                running, stopped = False, True
                ml.log(f'{event} from running to stopped, will be processed on next loop')
                increment_search_attempt_count_for_(section)
            elif stopped:
                stopped = False
                concluded = True if search_is_concluded_in_(state_machine) else False
                queued = True if not concluded else False
            elif concluded:
                ml.log(f'search for \'{section}\' concluded, cannot increment')
            search_states = queued, running, stopped, concluded
            set_search_states_for_(section, search_states)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log('error ' + event)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def ready_to_start_at_active_section_in_(state_machine) -> bool:
    return ready_to_start_at_(get_active_section_from_(state_machine)) \
        if not search_queue_is_full_in_(state_machine) else False


def reset_search_state_at_active_section_for_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'resetting search state at \'{section}\''
    ml.log(event, level=ml.WARNING)
    try:
        queued, running, stopped, concluded = True, False, False, False
        search_states = queued, running, stopped, concluded
        set_search_states_for_(section, *search_states)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def save_results_to_(state_machine, save_results_filtered=True) -> None:
    save_search_results_unfiltered_to_(state_machine)
    if save_results_filtered:
        save_search_results_filtered_to_(state_machine)


def search_is_concluded_in_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    event = f'checking if search concluded for \'{section}\''
    try:  # FIXME p1, are there multiple functions declared for this job..?
        if get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT) >= \
                get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT):
            ml.log(f'the search for \'{section}\' can be concluded', announcement=True)
            set_bool_for_(section, s_key.CONCLUDED, True)
        return get_bool_from_(section, s_key.CONCLUDED)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_running_at_active_section_in_(state_machine) -> bool:
    return search_is_running_at_(get_active_section_from_(state_machine))


def search_is_stopped_at_active_section_in_(state_machine) -> bool:
    return search_is_stopped_at_(get_active_section_from_(state_machine))


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


### ### ### ### ### ### ### ### ### ### state machine handlers ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    state machine handlers above                                    #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### state machine handlers ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### wrp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                       wrapper interface below                                      #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### wrp if ### ### ### ### ### ### ### ### ### ### ### ###


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
    event = f'getting search parser as sortable'
    try:
        search_parser = get_search_parser()
        parser_as_sortable = dict()
        for search_parser_section in search_parser.sections():
            parser_as_sortable[search_parser_section] = dict()
            for section_key in search_parser[search_parser_section]:
                parser_as_sortable[search_parser_section][section_key] = \
                    search_parser[search_parser_section][section_key]
        return parser_as_sortable
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_properties_from_(state_machine) -> tuple:
    return _stm_if_get_search_properties_from_(state_machine)


def get_search_rank_for_(section: str) -> int:
    return _scp_if_get_int_at_key_(section, s_key.RANK)


def get_search_results_for_(state_machine) -> list:
    return _api_if_get_search_results_for_(state_machine)


def get_search_state_for_(section: str) -> tuple:
    return _scp_if_get_search_state_for_(section)


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


def search_is_running_at_(section: str) -> bool:
    return _stm_if_search_is_running_at_(section)


def search_is_stopped_at_(section: str) -> bool:
    return _stm_if_search_is_stopped_at_(section)


def search_is_stopped_in_(state_machine) -> bool:
    return _stm_if_search_is_stopped_in_(state_machine)


def search_is_stored_in_(state_machine) -> bool:
    return _stm_if_search_is_stored_in_(state_machine)


def set_active_section_to_(section: str, state_machine) -> None:
    _stm_if_set_active_section_to_(section, state_machine)


def set_bool_for_(section: str, key: str, boolean: bool) -> None:
    _scp_if_set_bool_for_(section, key, boolean)


def set_time_last_read_for_(section: str) -> None:
    _scp_if_set_time_last_read_for_(section)


def set_time_last_searched_for_(section: str) -> None:
    _scp_if_set_time_last_searched_for_(section)


def update_search_properties_for_(state_machine) -> None:
    _stm_if_update_search_properties_for_(state_machine)


def write_parsers_to_disk() -> None:
    _cfg_if_write_parsers_to_disk()


def write_search_id_to_search_parser_at_(section: str, search_id: str) -> None:
    _scp_if_set_str_for_(section, s_key.ID, search_id)


### ### ### ### ### ### ### ### ### ### ### ### wrp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                       wrapper interface above                                      #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### wrp if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                        api interface below                                         #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###


def _api_if_add_result_from_(url: str, is_paused: bool) -> None:
    event = f'calling api to add result from url'
    try:  # api surface abstraction level = 0
        q_api.add_result_from_(url, is_paused)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _api_if_create_search_job_for_(pattern: str, plugins: str, category: str) -> tuple:
    event = f'calling api to create search job for pattern, plugins, and category'
    try:  # api surface abstraction level = 0
        job = q_api.qbit_client.search.start(pattern, plugins, category)
        assert job is not None, 'bad search job, fix it or handle it'
        count, sid, status = q_api.get_search_info_from_(job)
        ml.log(f'qbit client created search job for \'{pattern}\'')
        return count, sid, status
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _api_if_get_connection_time_start() -> dt:
    event = f'calling api to get connection time start'
    try:  # api surface abstraction level = 0
        return q_api.get_connection_time_start()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _api_if_get_local_results_count() -> int:
    event = f'calling api to get local results count'
    try:  # api surface abstraction level = 0
        return q_api.get_local_results_count()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _api_if_get_search_results_for_(state_machine) -> list:
    event = f'calling api to get search results for search id'
    search_id = get_search_id_from_active_section_in_(state_machine)
    results = q_api.get_result_object_at_(search_id)
    try:  # api surface abstraction level = 0
        if results is None:  # fyi this could cause permanent fatal errors depending on search id handling
            raise ValueError('unexpected empty results')
        return results[m_key.RESULTS]
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _api_if_get_search_properties_for_(search_id: str) -> tuple:
    event = f'calling api to get search properties for'
    try:  # api surface abstraction depth = 0
        return q_api.get_search_properties_for_(search_id=search_id)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                        api interface above                                         #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                         cfg interface below                                        #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###


def _cfg_if_set_parser_value_at_(section: str, parser_key: str, value,
                                 mp=None, search=True, settings=False):
    try:  # todo deprecate cfg interface methods
        if mp:
            QConf.write_parser_section_with_key_(parser_key, value, section, mp)
        elif settings:
            QConf.write_parser_section_with_key_(parser_key, value, section, settings=settings)
        elif search:  # must be last since search defaults True
            QConf.write_parser_section_with_key_(parser_key, value, section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _cfg_if_write_parsers_to_disk():
    try:  # todo deprecate cfg interface methods
        QConf.write_config_to_disk()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                         cfg interface above                                        #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### mdp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                   metadata parser interface below                                  #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### mdp if ### ### ### ### ### ### ### ### ### ### ### ###


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
    hashed_result_guid = hashed_result[hash_metadata(m_key.GUID)]  # FIXME p0, get this out of low lvl ifs
    event = f'creating metadata parser section'
    try:
        if mp.has_section(hashed_result_guid):
            ml.log(f'metadata parser already has section \'{hashed_result_guid}\'', level=ml.ERROR)
            return
        mp.add_section(hashed_result_guid)
        ml.log(f'section \'{hashed_result_guid}\' added to metadata', announcement=True)
        for h_attr, h_dtl in hashed_result.items():
            _cfg_if_set_parser_value_at_(hashed_result_guid, h_attr, h_dtl, mp)
        return
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_get_all_sections_from_metadata_parsers() -> tuple:
    try:
        return *_metadata_added_parser().sections(), *_metadata_failed_parser().sections()
    except Exception as e_err:
        ml.log(e_err.args[0])


def _mdp_if_get_metadata_from_(parser: RawConfigParser) -> dict:
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


def _mdp_if_previously_found_(result: dict, verbose_log=True) -> bool:
    event = f'checking if previously found result \'{result}\''
    try:
        result_name = build_metadata_guid_from_(result)
        added_or_found = [*ma_parser.sections(), *mf_parser.sections()]
        if result_name in added_or_found:
            if verbose_log:
                ml.log(f'old result found, skipping \'{result_name}\'', level=ml.WARNING)
            return True
        ml.log(f'new result found \'{result_name}\'')
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _mdp_if_write_metadata_from_(result: dict, added=False) -> None:
    try:
        pass
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ### ### ### ### mdp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                   metadata parser interface above                                  #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### mdp if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### scp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    search parser interface below                                   #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### scp if ### ### ### ### ### ### ### ### ### ### ### ###


def _search_parser(section=empty):
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


def _scp_if_get_bool_from_(section: str, key: str) -> bool:
    try:  # parser surface abstraction depth = 1
        return _search_parser(section).getboolean(key)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_get_bool_at_key_(section: str, key: str) -> bool:
    event = f'getting bool value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        boolean = _search_parser(section).getboolean(key)
        ml.log(event)
        return boolean
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_get_int_at_key_(section: str, key: str) -> int:
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


def _scp_if_get_str_at_key_(section: str, key: str) -> str:
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
        _search_parser(section)[key] = str(get_int_from_search_parser_at_(section, key) + 1)
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


def _scp_if_set_bool_for_(section: str, key: str, boolean: bool):
    try:  # parser surface abstraction depth = 1
        _search_parser(section)[key] = s_key.YES if boolean else s_key.NO
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _scp_if_set_end_reason_for_(section, reason_key):
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


def _scp_if_set_search_id_for_(section: str, search_id: str) -> None:
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


def _scp_if_set_str_for_(section: str, key: str, string: str):
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


### ### ### ### ### ### ### ### ### ### ### ### scp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    search parser interface above                                   #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### scp if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### stm if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    state machine interface below                                   #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### stm if ### ### ### ### ### ### ### ### ### ### ### ###


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


def _stm_if_get_active_search_dict_from_(state_machine) -> dict:
    event = f'getting active search dict from state machine'
    try:  # machine surface abstraction depth = 1
        return state_machine.active_sections
    except Exception as e_err:
        ml.log(f'error {event}')
        ml.log(e_err.args[0])


def _stm_if_get_active_section_from_(state_machine) -> str:
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


def _stm_if_get_active_section_search_id_from_(state_machine) -> str:
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


def _stm_if_get_search_id_from_(state_machine, section) -> str:
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


def _stm_if_get_search_properties_at_(section: str) -> tuple:
    search_id = _scp_if_get_search_id_for_(section)
    try:
        if empty_(search_id):
            return None, None, None
        return _api_if_get_search_properties_for_(search_id)
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_search_properties_from_(state_machine) -> tuple:
    # todo just noting this object has two surfaces, could be useful
    try:  # api/machine surface abstraction depth = 1/1
        search_id = _stm_if_get_active_section_search_id_from_(state_machine)
        search_properties = _api_if_get_search_properties_for_(search_id)
        return search_properties
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
        unfiltered_results = _api_if_get_search_results_for_(state_machine)
        _stm_if_update_search_properties_for_(state_machine)
        state_machine.active_sections[section]['unfiltered_results'] = unfiltered_results
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_search_is_running_at_(section) -> bool:
    try:  # machine surface abstraction depth = 1
        search_count, search_id, search_status = _stm_if_get_search_properties_at_(section)
        if none_value_(search_id):
            return False
        return True if s_key.RUNNING in search_status else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_search_is_stored_in_(state_machine) -> bool:
    # FIXME hierarchy status < search_id < section < state_machine could be reduced
    try:  # machine surface abstraction depth = 1
        search_count, search_id, search_status = _stm_if_get_search_properties_from_(state_machine)
        active_search_ids = _stm_if_get_active_search_dict_from_(state_machine)
        return True if search_id in active_search_ids else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_search_is_stopped_at_(section) -> bool:
    try:  # machine surface abstraction depth = 1
        search_count, search_id, search_status = _stm_if_get_search_properties_at_(section)
        if none_value_(search_id):
            return False
        return True if s_key.STOPPED in search_status else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_search_is_stopped_in_(state_machine) -> bool:
    try:  # FIXME hierarchy status < search_id < section < state_machine could be reduced
        key = s_key.STOPPED
        search_count, search_id, search_status = _stm_if_get_search_properties_from_(state_machine)
        active_sections = state_machine.active_sections
        return True if key in search_status and search_id in active_sections else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_set_active_section_to_(section: str, state_machine):
    try:
        state_machine.active_section = section
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_update_search_properties_for_(state_machine):
    section = _stm_if_get_active_section_from_(state_machine)
    search_properties = _stm_if_get_search_properties_from_(state_machine)
    try:
        state_machine.active_sections[section]['count'] = search_properties[0]
        state_machine.active_sections[section]['id'] = search_properties[1]
        state_machine.active_sections[section]['status'] = search_properties[2]
    except Exception as e_err:
        ml.log(e_err.args[0])


### ### ### ### ### ### ### ### ### ### ### ### stm if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    STATE MACHINE INTERFACE ABOVE                                   #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### stm if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### ucp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                 USER CONFIG PARSER INTERFACE BELOW                                 #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### ucp if ### ### ### ### ### ### ### ### ### ### ### ###


def _user_configuration(section=empty):
    event = f'getting user config parser at \'{section}\'' if not empty_(section) else f'getting user config parser'
    try:
        if section:
            if section != default:
                ml.log(f'the section value \'{section}\' may be an issue', level=ml.WARNING)
        ml.log(f'ignoring user section \'{section}\'.. setting to \'{default}\'')
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


def _ucp_if_get_str_for_key_(key: str) -> str:
    event = f'getting str from user configuration parser with key \'{key}\''
    try:
        val = _user_configuration(default)[key]
        return str(val)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


### ### ### ### ### ### ### ### ### ### ### ### ucp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                 USER CONFIG PARSER INTERFACE ABOVE                                 #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### ucp if ### ### ### ### ### ### ### ### ### ### ### ###
