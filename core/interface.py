from configparser import RawConfigParser
from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from qbit_interface.api_comm import QbitApiCaller as QApi
from string import digits
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


def active_section_is_in_memory_of_(state_machine):
    event = f'checking if active section is in memory of state machine'
    section = get_active_section_from_(state_machine)
    active_sections = get_active_sections_from_(state_machine)
    try:
        return True if section in active_sections else False
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def add_results_stored_in_(state_machine):
    section = get_active_section_from_(state_machine)
    filtered_results = get_filtered_results_from_(state_machine)
    event = f'adding results from state machine'
    try:
        results_required_count = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
        ml.log_event(f'add most popular \'{results_required_count}\' count results')
        for result in filtered_results:
            results_added_count = get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT)
            if results_added_count > results_required_count:  # FIXME p2, shouldn't this use the conclusion check func?
                ml.log_event(f'the search for \'{section}\' can be concluded', announce=True)
                _sp_if_set_bool_for_(section, s_key.CONCLUDED, True)
                return  # enough results have been added for this header, stop
            if add_successful_for_(section, result):  # FIXME p0, sometimes this adds two values
                _mp_if_write_metadata_from_(result, added=True)
                if enough_results_added_for_(section):
                    ml.log_event(f'enough results added for \'{section}\'')
                    return  # desired result count added, stop adding
                write_parsers_to_disk()  # FIXME p0, debug line, consider removing
                continue  # result added, go to next
            result_name = _mp_if_get_result_metadata_at_key_(m_key.NAME, result)
            ml.log_event(f'client failed to add \'{result_name}\'', level=ml.WARNING)
            write_parsers_to_disk()  # FIXME p0, debug line, consider removing
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def add_search_properties_to_(state_machine, search_properties):
    event = f'adding search properties to state machine'
    try:
        _sm_if_add_search_properties_to_(state_machine, search_properties)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def add_successful_for_(section: str, result: dict) -> bool:
    event = f'checking if add successful for \'{section}\' with result \'{result}\''
    try:
        count_before_add_attempt = _api_if_get_local_results_count()
        ml.log_event(f'local machine has {count_before_add_attempt} stored results before add attempt..')
        # TODO why does client fail to add so often? outside project scope?
        url = _mp_if_get_result_metadata_at_key_(m_key.URL, result)
        _api_if_add_result_from_(url, _sp_if_get_add_mode_for_(section))
        pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
        results_added_count = _api_if_get_local_results_count() - count_before_add_attempt
        successfully_added = True if results_added_count else False
        if successfully_added:
            _sp_if_increment_result_added_count_for_(section)
        return successfully_added
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def all_searches_concluded() -> bool:
    event = f'checking if all searches concluded'
    try:
        concluded_bools = list()
        for section in get_all_sections_from_search_parser():
            concluded_bool = True if get_bool_from_(section, s_key.CONCLUDED) else False
            concluded_bools.append(concluded_bool)
        if concluded_bools and all(concluded_bools):
            ml.log_event(f'all searches concluded', level=ml.WARNING)
            return True
        ml.log_event(f'all searches are not concluded, program continuing')
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def build_metadata_section_from_(result: dict) -> str:
    event = f'building metadata section from \'{result}\''
    try:
        name, url = \
            _mp_if_get_result_metadata_at_key_(m_key.NAME, result), \
            _mp_if_get_result_metadata_at_key_(m_key.URL, result)
        if url == '':
            raise ValueError(f'empty url!')
        r_name, delimiter, r_url = hash_metadata(name), ' @ ', hash_metadata(url)
        hashed_name = r_name + delimiter + r_url
        return hashed_name
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def check_for_empty_string_to_replace_with_no_data_in_(value: str) -> str:
    event = f'checking for empty string to replace with \'NO DATA\' in value \'{value}\''
    try:
        return 'NO DATA' if empty_(value) else value
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def create_search_job_for_(pattern: str, plugins: str, category: str):
    event = f'creating search job for \'{pattern}\''
    try:
        return _api_if_create_search_job_for_(pattern, plugins, category)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def empty_(test_string: str) -> bool:
    event = f'checking if value \'{test_string}\' is empty string'
    try:
        return True if test_string == '' else False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def enough_results_added_for_(section: str) -> bool:
    event = f'checking if enough results added for \'{section}\''
    try:
        results_added = get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT)
        results_required = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
        if results_added >= results_required:  # TODO check that indexing is perfect
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def enough_results_found_in_(section: str, filtered_results: list) -> bool:
    event = f'checking if enough results found in \'{section}\''
    try:
        expected_results_count = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
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
        ml.log_event(f'error {event}')


def exit_program():
    event = f'exiting program'
    try:
        write_parsers_to_disk()
        ml.log_event(event)
        exit()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def filter_provided_for_(parser_val) -> bool:
    event = f'checking if filter provided'
    try:
        return False if parser_val == -1 or parser_val == 0 else True
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def filter_results_in_(state_machine, found=True, sort=True):
    # FIXME p1, this function needs a lot of work offloading to level 0 abstraction interfaces..
    results_filtered_and_sorted = list()
    section = _sm_if_get_active_section_from_(state_machine)
    results_unfiltered = _sm_if_get_unfiltered_results_from_(state_machine)
    event = f'filtering results for \'{section}\''
    try:
        seeds_min = get_int_from_search_parser_at_(section, s_key.MIN_SEED)
        bytes_min = get_int_from_search_parser_at_(section, s_key.SIZE_MIN_BYTES)
        bytes_max = get_int_from_search_parser_at_(section, s_key.SIZE_MAX_BYTES)
        megabytes_min = mega(bytes_min)
        megabytes_max = mega(bytes_max) if bytes_max != -1 else bytes_max
        filename_regex = _sp_if_get_str_at_key_(section, s_key.REGEX_FILENAME)  # FIXME check this return
        results_filtered = list()
        for result_unfiltered in results_unfiltered:
            result_name = _mp_if_get_result_metadata_at_key_(m_key.NAME, result_unfiltered)
            if found and _mp_if_previously_found_(result_unfiltered):
                continue
            if filter_provided_for_(seeds_min):
                result_seeds = int(_mp_if_get_result_metadata_at_key_(m_key.SUPPLY, result_unfiltered))  # FIXME int
                enough_seeds = True if result_seeds > seeds_min else False
                if not enough_seeds:
                    ml.log_event(f'required seeds \'{seeds_min}\' not met by result with '
                                 f'\'{result_seeds}\' seeds, result : \'{result_name}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    _mp_if_write_metadata_from_(result_unfiltered)
                    continue
            if filter_provided_for_(megabytes_min) or filter_provided_for_(megabytes_max):
                bytes_result = int(_mp_if_get_result_metadata_at_key_(m_key.SIZE, result_unfiltered))  # FIXME int
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
                    _mp_if_write_metadata_from_(result_unfiltered)
                    continue
            if filter_provided_for_(filename_regex):
                ml.log_event(f'filtering results using filename regex \'{filename_regex}\'')
                filename = _mp_if_get_result_metadata_at_key_(m_key.NAME, result_unfiltered)
                if not q_api.regex_matches(filename_regex, filename):
                    ml.log_event(f'regex \'{filename_regex}\' does not match for \'{filename}\'', level=ml.WARNING)
                    _mp_if_write_metadata_from_(result_unfiltered)
                    continue
            ml.log_event(f'result \'{result_name}\' meets all requirements')
            results_filtered.append(result_unfiltered)
        if sort:
            ml.log_event(f'sorting results for \'{section}\'')
            results_filtered_and_sorted = sort_(results_filtered)
        reduce_search_expectations_if_not_enough_results_found_in_(section, results_filtered_and_sorted)
        return results_filtered_and_sorted
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_active_section_from_(state_machine) -> str:
    event = f'getting active section from state machine'
    try:
        return _sm_if_get_active_section_from_(state_machine)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_active_sections_from_(state_machine) -> list:
    event = f'getting active section from state machine'
    try:
        return _sm_if_get_active_sections_from_(state_machine)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_all_sections_from_metadata_parsers() -> tuple:
    event = f'getting all sections from metadata parser'
    try:
        return _mp_if_get_all_sections_from_metadata_parsers()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_all_sections_from_parser_(meta_add=False, meta_find=False, search=False, settings=False):
    event = f'getting all sections from parser'
    try:  # FIXME break this into multiple functions
        ml.log_event(event)
        return _cfg_if_get_all_sections_from_parser_(meta_add, meta_find, search, settings)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_all_sections_from_user_config_parser() -> list:
    event = f'getting all sections from user config parser'
    try:
        return _uc_if_get_all_sections_from_user_config_parser()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_all_sections_from_search_parser() -> list:
    event = f'getting all sections from search parser'
    try:  # parser surface abstraction depth = 1
        return _sp_if_get_all_sections_from_search_parser()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_bool_from_(section: str, key: str) -> bool:
    try:  # parser surface abstraction depth = 1
        return _sp_if_get_bool_from_(section, key)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_concluded_state_for_(section) -> bool:
    event = f'getting concluded state for \'{section}\''
    try:
        return get_search_states_for_(section)[3]
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_connection_time_start():
    event = f'getting connection time start'
    try:
        return _api_if_get_connection_time_start()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_hashed_(attribute: str, detail: str, offset: int) -> tuple:
    event = f'getting hashed value with offset \'{offset}\' for attribute \'{attribute}\' and detail \'{detail}\''
    try:
        return hash_metadata(attribute, offset), hash_metadata(detail, offset)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_filtered_results_from_(state_machine) -> list:
    section = state_machine.active_section
    event = f'getting filtered results from state machine'
    try:
        filtered_results = _sm_if_get_filtered_results_from_(state_machine)
        if filtered_results is None:
            ml.log_event(f'invalid search results at \'{section}\'', level=ml.WARNING)
            reset_search_state_at_active_section_for_(state_machine)
            return list()
        return filtered_results
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_bool_from_search_parser_at_(section, key) -> bool:
    event = f'getting bool at key \'{key}\''
    try:
        return _sp_if_get_bool_at_key_(section, key)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_int_from_search_parser_at_(section, key) -> int:
    event = f'getting int at key \'{key}\''
    try:
        return _sp_if_get_int_at_key_(section, key)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_str_from_search_parser_at_(section, key) -> str:
    event = f'getting str at key \'{key}\''
    try:
        return _sp_if_get_str_at_key_(section, key)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_queued_state_for_(section) -> bool:
    event = f'getting queued state for \'{section}\''
    try:
        return get_search_states_for_(section)[0]
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_running_state_for_(section) -> bool:
    event = f'getting running state for \'{section}\''
    try:
        return get_search_states_for_(section)[1]
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def get_search_id_from_active_section_in_(state_machine) -> str:
    event = f'getting search id from active section in state machine'
    try:
        return _sm_if_get_search_id_from_active_section_in_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0])
        ml.log_event(f'error {event}')


def get_search_properties_from_(state_machine) -> tuple:
    event = f'getting search properties from state machine'
    try:  # machine surface abstraction depth = 1
        return _sm_if_get_search_properties_from_(state_machine)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_results_for_(state_machine) -> list:
    event = f'getting search results'
    try:
        return _api_if_get_search_results_for_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_search_states_for_(section) -> tuple:
    event = f'getting search state for \'{section}\''
    try:
        return _sp_if_get_search_states_for_(section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_search_term_for_(section: str) -> str:
    event = f'getting search term for \'{section}\''
    try:
        return _sp_if_get_search_term_for_(section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def get_stopped_state_for_(section) -> bool:
    event = f'getting stopped state for \'{section}\''
    try:
        return get_search_states_for_(section)[2]
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def hash_metadata(x: str, offset=0, undo=False) -> str:
    event = f'hashing metadata with offset \'{offset}\' for \'{x}\''
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        ml.log_event(f'hashed from.. \n\t\t\'{x}\' to.. \n\t\t\'{_hash}\'')
        return _hash
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def increment_search_state_at_active_section_for_(state_machine):
    event = f'incrementing search state for \'{state_machine.active_section}\''
    try:
        _sp_if_increment_search_state_for_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def mega(bytes_: int) -> int:
    event = f'converting \'{bytes_}\' bytes to megabytes'
    try:
        megabytes_ = int(bytes_ / 1000000)
        return megabytes_
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def pause_on_event(pause_type: str):
    event = f'pausing on event \'{pause_type}\''
    try:  # FIXME p0, doesn't work with new architecture, re-think
        parser_at_default = u_parser[u_key.DEFAULT]
        delay = int(parser_at_default[pause_type])
        ml.log_event(f'waiting \'{delay}\' seconds for event \'{str(pause_type)}\'')
        q_api.pause_for_(delay)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def print_search_ids_from_(active_search_ids: dict):
    event = f'printing search ids from \'{active_search_ids}\''
    try:  # FIXME p3, this is hit too frequently
        ml.log_event('active search headers are..')
        for active_search_header_name in active_search_ids.keys():
            ml.log_event(f'\tsearch header : \'{active_search_header_name}\'')
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def ready_to_start_at_(section: str, state_machine) -> bool:
    event = f'checking if search is ready to start'
    try:
        ml.log_event(event)
        queued = get_queued_state_for_(section)
        return _sp_if_ready_to_start_(queued, state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def reduce_search_expectations_if_not_enough_results_found_in_(section: str, filtered_results: list) -> None:
    event = f'evaluating filtered results for \'{section}\''
    try:
        if not enough_results_found_in_(section, filtered_results):
            _sp_if_reduce_search_expectations_for_(section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def reset_search_state_at_active_section_for_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'resetting search state at \'{section}\''
    try:
        ml.log_event(event, level=ml.WARNING)
        queued, running, stopped, concluded = True, False, False, False
        search_states = queued, running, stopped, concluded
        set_search_states_for_(section, *search_states)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def result_has_enough_seeds() -> bool:
    event = f'checking if result has enough seeds'
    try:
        pass  # TODO refactor into this function?
        return True
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def save_results_to_(state_machine, save_filtered_results=True):
    results_filter_state = 'unfiltered and filtered' if save_filtered_results else 'unfiltered'
    event = f'saving {results_filter_state} results to state machine'
    try:
        save_search_results_unfiltered_to_(state_machine)
        if save_filtered_results:
            save_search_results_filtered_to_(state_machine)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def save_search_results_filtered_to_(state_machine):
    event = f'saving filtered search results to state machine'
    try:
        _sm_if_save_filtered_search_results_to_(state_machine)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def save_search_results_unfiltered_to_(state_machine):
    event = f'saving unfiltered search results to state machine'
    try:
        _sm_if_save_unfiltered_search_results_to_(state_machine)
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def search_has_yielded_required_results_for_(state_machine) -> bool:
    event = f'checking if search has yielded required results'
    try:
        return _sp_if_search_has_yielded_required_results_for_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def search_is_concluded_in_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    event = f'checking if search concluded for \'{section}\''
    try:
        return get_bool_from_(section, s_key.CONCLUDED)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def search_is_running_in_(state_machine) -> bool:
    event = f'checking if search is running in state machine'
    try:  # machine surface abstraction depth = 1
        return _sm_if_search_is_running_in_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def search_is_stopped_in_(state_machine) -> bool:
    event = f'checking if search is stopped in state machine'
    try:  # FIXME hierarchy status < search_id < section < state_machine could be reduced
        return _sm_if_search_is_stopped_in_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def search_queue_is_full_in_(state_machine) -> bool:
    event = f'checking if search queue full'
    try:
        active_search_ids = state_machine.active_sections
        section = _sm_if_get_active_section_from_(state_machine)
        active_search_count = len(active_search_ids)
        if active_search_count < 5:  # maximum simultaneous searches allowed by api
            ml.log_event(f'search queue is not full, \'{5-active_search_count}\' spaces available')
            print_search_ids_from_(active_search_ids)
            return False
        event = f'search queue is full, cannot add \'{section}\''
        ml.log_event(event, level=ml.WARNING)
        return True
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def search_started_for_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    active_sections = get_active_sections_from_(state_machine)
    event = f'checking if search started for \'{section}\''
    try:
        if section in active_sections:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_active_section_to_(section: str, state_machine):
    event = f'setting active section for state machine to \'{section}\''
    try:
        _sm_if_set_active_section_to_(section, state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_bool_for_(section: str, key: str, boolean: bool):
    event = f'setting boolean value \'{boolean}\' for \'{section}\' at \'{key}\''
    try:
        _sp_if_set_bool_for_(section, key, boolean)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_search_id_activity_for_(state_machine, active=False) -> dict:
    # FIXME p3, this function is scrap metal, has good ideas but defunct, strip it then delete it
    event = 'setting search id activity'
    action = 'creating' if active else 'destroying'
    state = 'active' if active else 'inactive'
    try:  # FIXME p0, arg 2, search_properties is a string instead of a tuple
        section = state_machine.active_section
        # init vars before fetch attempt
        search_count, search_id, search_status = 0, '', None
        if section in state_machine.active_sections:
            search_count = state_machine.active_sections[section]['count']
            search_id = state_machine.active_sections[section]['id']
            search_status = state_machine.active_sections[section]['status']
        active_search_ids = state_machine.active_sections
        event = f'{action} {state} search id entry for state machine at \'{section}\' with id \'{search_id}\''
        if not active:
            ml.log_event(f'checking if \'{section}\' exists as active key')
            section_exists = True if section in active_search_ids else False
            if section_exists:
                ml.log_event(f'section found')
                ml.log_event(event)
                del active_search_ids[section]
                return active_search_ids  # FIXME see if this return works as expected
            ml.log_event(f'section not found', level=ml.WARNING)
            return active_search_ids  # FIXME see if this return works as expected
        ml.log_event(event)
        active_search_ids[section] = {
            'count':    search_count,
            'id':       search_id,
            'status':   search_status
        }
        return active_search_ids
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_search_ranks() -> None:
    # TODO save this to the state machine instance
    event = f'setting search ranks'
    try:
        _sp_if_set_search_ranks()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_search_states_for_(section, *search_states) -> None:
    event = f'setting search states for \'{section}\''
    try:
        _sp_if_set_search_states_for_(section, search_states)
        ml.log_event(f'search state for \'{section}\': '
                     f'\n\tqueued: {search_states[0]}'
                     f'\n\trunning: {search_states[1]}'
                     f'\n\tstopped: {search_states[2]}'
                     f'\n\tconcluded: {search_states[3]}', announce=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_time_last_read_for_(section: str) -> None:
    event = f'setting time last read for \'{section}\''
    try:
        _sp_if_set_time_last_read_for_(section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def set_time_last_searched_for_(section: str) -> None:
    event = f'setting time last searched for \'{section}\''
    try:
        _sp_if_set_time_last_searched_for_(section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def sort_(results: list) -> list:
    # TODO dynamic sort values
    event = f'sorting results'
    try:
        return sorted(results, key=lambda k: k['nbSeeders'], reverse=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def start_search_with_(state_machine):
    section = state_machine.active_section
    event = f'starting search with \'{section}\''
    try:
        search_term = get_search_term_for_(section)
        # FIXME instead of returning properties, just add them to the state machine
        search_properties = create_search_job_for_(search_term, 'all', 'all')
        add_search_properties_to_(state_machine, search_properties)
        search_count, search_id, search_status = search_properties
        if search_id is None or empty_(search_id):
            event = f'invalid search id, empty or none'
            ml.log_event(event)
            raise Exception(event)
        if search_is_running_in_(state_machine):
            ml.log_event(f'search \'{search_term}\' successfully started for \'{section}\' with id \'{search_id}\'')
            set_time_last_searched_for_(section)
            increment_search_state_at_active_section_for_(state_machine)
            return
        elif search_is_stopped_in_(state_machine):
            event = f'search stopped immediately after starting at \'{section}\''
            ml.log_event(event, level=ml.WARNING)
            increment_search_state_at_active_section_for_(state_machine)  # FIXME do this yes or no?
        else:
            event = f'stale search, bad search status and/or bad search id, re-queueing \'{section}\''
            ml.log_event(event, level=ml.WARNING)
            reset_search_state_at_active_section_for_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def update_search_properties_for_(state_machine):
    event = f'updating search properties for state machine'
    try:
        _sm_if_update_search_properties_for_(state_machine)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def validate_metadata_type_for_(metadata_kv: tuple) -> tuple:
    event = f'validating metadata type for \'{metadata_kv}\''
    try:
        parser_key, value = metadata_kv  # FIXME reminder, WAS a bug, be sure it doesn't happen again
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
                ml.log_event(f'unable to convert int to string')
                ml.log_event(e_err.args[0], level=ml.ERROR)
        value = check_for_empty_string_to_replace_with_no_data_in_(value)
        return parser_key, value
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def value_provided_for_(value_to_check) -> bool:
    event = f'checking if value provided for \'{value_to_check}\''
    try:
        return False if value_to_check == '0' else True
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def write_parsers_to_disk():
    event = f'writing parsers to disk'
    try:  # parser surface abstraction depth = 1
        ml.log_event(event)
        _cfg_if_write_parsers_to_disk()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


#### ### ### ### ### ### ### ### ### ### STM INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                STATE MACHINE INTERFACE BELOW                                       #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### STM INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###


def _sm_if_add_search_properties_to_(state_machine, search_properties: tuple) -> None:
    section = _sm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        _sm_if_init_active_search_id_for_(state_machine, section)
        state_machine.active_sections[section]['count'] = search_properties[0]
        state_machine.active_sections[section]['id'] = search_properties[1]
        state_machine.active_sections[section]['status'] = search_properties[2]
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_active_search_ids_from_(state_machine) -> list:
    event = f'getting active search id values from state machine'
    try:  # machine surface abstraction depth = 1
        active_search_ids = list()
        for section in state_machine.active_sections:
            section_id = _sm_if_get_search_id_from_(state_machine, section)
            active_search_ids.append(section_id)
        return active_search_ids
    except Exception as e_err:
        ml.log_event(f'error {event}')
        ml.log_event(e_err.args[0])


def _sm_if_get_active_section_from_(state_machine) -> str:
    try:  # machine surface abstraction depth = 0
        return state_machine.active_section
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_active_sections_from_(state_machine) -> list:
    # FIXME this returns dict or list? it works as-is but.. need to be sure
    try:  # machine surface abstraction depth = 0
        return state_machine.active_sections
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_active_section_search_id_from_(state_machine) -> str:
    try:  # machine surface abstraction depth = 1
        section = _sm_if_get_active_section_from_(state_machine)
        return state_machine.active_sections[section]['id']
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_filtered_results_from_(state_machine):
    section = _sm_if_get_active_section_from_(state_machine)
    try:
        return state_machine.active_sections[section]['filtered_results']
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_search_id_from_(state_machine, section) -> str:
    try:  # machine surface abstraction depth = 0
        return state_machine.active_sections[section]['id']
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_search_id_from_active_section_in_(state_machine) -> str:
    try:
        section = state_machine.active_section
        return _sm_if_get_search_id_from_(state_machine, section)
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_get_search_properties_from_(state_machine) -> tuple:
    # TODO just noting this object has two surfaces, could be useful
    try:  # api/machine surface abstraction depth = 1/1
        search_id = _sm_if_get_active_section_search_id_from_(state_machine)
        search_properties = _api_if_get_search_properties_for_(search_id)
        return search_properties
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sm_if_get_unfiltered_results_from_(state_machine):
    section = _sm_if_get_active_section_from_(state_machine)
    try:
        return state_machine.active_sections[section]['unfiltered_results']
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_init_active_search_id_for_(state_machine, section: str) -> None:
    try:  # machine surface abstraction depth = 0
        state_machine.active_sections[section] = dict()
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_save_filtered_search_results_to_(state_machine):
    # FIXME p0, interface function relies on wrapper function, should be opposite
    section = _sm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        filtered_results = filter_results_in_(state_machine)
        # sm_if_update_search_properties_for_(state_machine)  # TODO delete me
        state_machine.active_sections[section]['filtered_results'] = filtered_results
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_save_unfiltered_search_results_to_(state_machine):
    section = _sm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        unfiltered_results = _api_if_get_search_results_for_(state_machine)
        _sm_if_update_search_properties_for_(state_machine)
        state_machine.active_sections[section]['unfiltered_results'] = unfiltered_results
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_search_is_running_in_(state_machine) -> bool:
    # FIXME hierarchy status < search_id < section < state_machine could be reduced
    try:  # machine surface abstraction depth = 1
        search_count, search_id, search_status = _sm_if_get_search_properties_from_(state_machine)
        active_search_ids = _sm_if_get_active_search_ids_from_(state_machine)
        return True if s_key.RUNNING in search_status and search_id in active_search_ids else False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sm_if_search_is_stopped_in_(state_machine) -> bool:
    try:  # FIXME hierarchy status < search_id < section < state_machine could be reduced
        key = s_key.STOPPED
        search_count, search_id, search_status = _sm_if_get_search_properties_from_(state_machine)
        active_sections = state_machine.active_sections
        return True if key in search_status and search_id in active_sections else False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sm_if_set_active_section_to_(section: str, state_machine):
    try:
        state_machine.active_section = section
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sm_if_update_search_properties_for_(state_machine):
    section = _sm_if_get_active_section_from_(state_machine)
    search_properties = _sm_if_get_search_properties_from_(state_machine)
    try:
        state_machine.active_sections[section]['count'] = search_properties[0]
        state_machine.active_sections[section]['id'] = search_properties[1]
        state_machine.active_sections[section]['status'] = search_properties[2]
    except Exception as e_err:
        ml.log_event(e_err.args[0])


#### ### ### ### ### ### ### ### ### ### STM INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                STATE MACHINE INTERFACE ABOVE                                       #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### STM INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###

#### ### ### ### ### ### ### ### ### ### API INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                     API INTERFACE BELOW                                            #
#                                                                                                    #
#### ### ### ### ### ### ### ### ### ### API INTERFACE ### ### ### ### ### ### ### ### ### ### ### ###


def _api_if_add_result_from_(url: str, is_paused: bool):
    try:  # api surface abstraction level = 0
        q_api.add_result_from_(url, is_paused)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _api_if_create_search_job_for_(pattern: str, plugins: str, category: str) -> tuple:
    try:  # api surface abstraction level = 0
        job = q_api.qbit_client.search.start(pattern, plugins, category)
        assert job is not None, 'bad search job, fix it or handle it'
        count, sid, status = q_api.get_search_info_from_(job)
        ml.log_event(f'qbit client created search job for \'{pattern}\'')
        return count, sid, status
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _api_if_get_connection_time_start():
    try:  # api surface abstraction level = 0
        return q_api.get_connection_time_start()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _api_if_get_local_results_count():
    try:  # api surface abstraction level = 0
        return q_api.get_local_results_count()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _api_if_get_search_results_for_(state_machine) -> list:
    try:  # api surface abstraction level = 0
        search_id = get_search_id_from_active_section_in_(state_machine)
        results = q_api.get_result_object_at_(search_id)
        # FIXME p2, replace assert
        assert results is not None, 'bad results, fix it or handle it'
        # TODO just noting that this is a pseudo-hardcode
        results = results[m_key.RESULTS]
        return results
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _api_if_get_search_properties_for_(search_id: str) -> tuple:
    try:  # api surface abstraction depth = 0
        return q_api.get_search_properties_for_(search_id=search_id)
    except Exception as e_err:
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


def _cfg_if_get_all_sections_from_parser_(meta_add=False, meta_find=False, search=False, settings=False):
    # TODO deprecate cfg interface methods
    try:  # parser surface abstraction depth = 0
        if meta_add:
            return QConf.get_all_sections_from_parser_(meta_add=True)
        if meta_find:
            return QConf.get_all_sections_from_parser_(meta_find=True)
        if search:
            return QConf.get_all_sections_from_parser_(search=True)
        if settings:
            return QConf.get_all_sections_from_parser_(settings=True)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _cfg_if_get_parser_value_at_(section: str, key: str,
                                 meta_add=False, meta_find=False,
                                 search=True, settings=False):
    # TODO deprecate cfg interface methods
    try:  # parser surface abstraction depth = 0
        if meta_add:
            return QConf.read_parser_value_with_(key, section, meta_add=meta_add)
        elif meta_find:
            return QConf.read_parser_value_with_(key, section, meta_find=meta_find)
        elif settings:
            return QConf.read_parser_value_with_(key, section, settings=settings)
        elif search:  # MUST be last since defaults true
            return QConf.read_parser_value_with_(key, section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _cfg_if_set_parser_value_at_(section: str, parser_key: str, value,
                                 mp=None, search=True, settings=False):
    # TODO deprecate cfg interface methods
    try:  # parser surface abstraction depth = 0
        if mp:
            QConf.write_parser_section_with_key_(parser_key, value, section, mp)
        elif settings:
            QConf.write_parser_section_with_key_(parser_key, value, section, settings=settings)
        elif search:  # MUST be last since search defaults true
            QConf.write_parser_section_with_key_(parser_key, value, section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _cfg_if_write_parsers_to_disk():
    # TODO deprecate cfg interface methods
    try:  # parser surface abstraction depth = 0
        QConf.write_config_to_disk()
    except Exception as e_err:
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


def _metadata_added_parser(section=empty) -> RawConfigParser:
    event = f'getting metadata added parser at \'{section}\'' if section else f'getting metadata added parser'
    try:
        if not empty_(section):
            assert section in ma_parser.sections(), KeyError(f'section \'{section}\' not in parser')
        return ma_parser[section] if not empty_(section) else ma_parser
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _metadata_failed_parser(section=empty) -> RawConfigParser:
    event = f'getting metadata failed parser at \'{section}\'' if section else f'getting metadata failed parser'
    try:
        if not empty_(section):
            assert section in mf_parser.sections(), KeyError(f'section \'{section}\' not in parser')
        return mf_parser[section] if not empty_(section) else mf_parser
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _mp_if_add_section_to_(mp: RawConfigParser, hashed_section_name: str) -> None:
    event = f'adding to metadata parser, section \'{hashed_section_name}\''
    try:
        if hashed_section_name in mp.sections():
            ml.log_event(f'section name already exists for \'{hashed_section_name}\'', level=ml.WARNING)
            return
        ml.log_event(f'adding section name for \'{hashed_section_name}\'')
        mp.add_section(hashed_section_name)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _mp_if_create_section_for_(mp: RawConfigParser, result: dict) -> None:
    # FIXME p3, this could be wrapped to reduce api interface clutter
    event = f'creating metadata parser section for \'{result}\''
    try:
        offset = _uc_if_get_int_for_key_(u_key.UNI_SHIFT)
        result_name = _mp_if_get_result_metadata_at_key_(m_key.NAME, result)
        ml.log_event(f'save metadata result to parser \'{result_name}\'')
        m_section = hash_metadata(build_metadata_section_from_(result), offset=offset)
        if mp.has_section(m_section):
            ml.log_event(f'metadata parser already has section \'{m_section}\'', level=ml.WARNING)
            return
        mp.add_section(m_section)
        result_name = _mp_if_get_result_metadata_at_key_(m_key.NAME, result)
        ml.log_event(f'section for header \'{m_section}\' added to metadata @ \'{result_name}\'', announce=True)
        for metadata_kv in result.items():
            attribute, detail = validate_metadata_type_for_(metadata_kv)
            h_attr, h_dtl = get_hashed_(attribute, detail, offset)
            # FIXME p3, this will break due to bad parser arg.. revisiting, resolved?
            _cfg_if_set_parser_value_at_(m_section, h_attr, h_dtl, mp)
            pause_on_event(u_key.WAIT_FOR_USER)
        return
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _mp_if_get_all_sections_from_metadata_parsers() -> tuple:
    try:
        return *_metadata_added_parser().sections(), *_metadata_failed_parser().sections()
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _mp_if_get_metadata_from_(parser: RawConfigParser) -> dict:
    event = f'getting metadata from parser'
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
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _mp_if_get_result_metadata_at_key_(key: str, result: dict) -> str:  # QConf
    event = f'getting result metadata at key \'{key}\''
    try:  # FIXME should this interface to QConf be re-thought?
        return QConf.get_result_metadata_at_key_(key, result)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _mp_if_previously_found_(result: dict, verbose_log=True) -> bool:
    event = f'checking if previously found result \'{result}\''
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
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _mp_if_write_metadata_from_(result: dict, added=False) -> None:  # FIXME metadata debug entry
    parser = 'added' if added else 'failed'
    event = f'writing metadata to \'{parser} from \'{result}\''
    try:
        _mp_if_create_section_for_(ma_parser if added else mf_parser, result)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


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


def _search_parser(section=empty):
    event = f'getting search parser for \'{section}\''
    try:  # parser surface abstraction depth = 0
        if not empty_(section):
            assert section in s_parser.sections(), KeyError(f'section \'{section}\' not in parser')
        return s_parser[section] if not empty_(section) else s_parser
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error' + event)


def _sp_if_get_add_mode_for_(section: str) -> bool:
    try:  # parser surface abstraction depth = 0
        return _sp_if_get_bool_from_(section, s_key.ADD_PAUSED)
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sp_if_get_all_sections_from_search_parser() -> list:
    try:  # parser surface abstraction depth = 0
        return _search_parser().sections()
    except Exception as e_err:
        ml.log_event(e_err.args[0])


def _sp_if_get_bool_from_(section: str, key: str) -> bool:
    try:  # parser surface abstraction depth = 1
        return _search_parser(section).getboolean(key)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_get_bool_at_key_(section: str, key: str) -> bool:
    event = f'getting bool value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        boolean = _search_parser(section).getboolean(key)
        ml.log_event(event)
        return boolean
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_get_int_at_key_(section: str, key: str) -> int:
    event = f'getting int value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        integer_as_str = _sp_if_get_str_at_key_(section, key)
        ml.log_event(event)
        for char in integer_as_str:  # FIXME this would allow values like -79 but also 7-9 which would error
            if char not in digits_or_sign:
                raise TypeError(f'unexpected character while ' + event)
        return int(integer_as_str)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_get_str_at_key_(section: str, key: str) -> str:
    event = f'getting str value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        string = str(_search_parser(section)[key])
        return string
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_get_parser_as_sortable() -> dict:
    event = f'getting search parser as sortable'
    try:  # FIXME remove/replace this function
        return QConf.get_search_parser_as_sortable()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_get_search_states_for_(section) -> tuple:
    try:  # parser surface abstraction depth = 2
        _sp_if_set_str_for_(section, s_key.TIME_LAST_READ, str(dt.now()))  # FIXME move to function
        search_queued = _sp_if_get_bool_from_(section, s_key.QUEUED)
        search_running = _sp_if_get_bool_from_(section, s_key.RUNNING)
        search_stopped = _sp_if_get_bool_from_(section, s_key.STOPPED)
        search_concluded = _sp_if_get_bool_from_(section, s_key.CONCLUDED)
        ml.log_event(f'search state for \'{section}\': '
                     f'\n\tqueued: {search_queued}'
                     f'\n\trunning: {search_running}'
                     f'\n\tstopped: {search_stopped}'
                     f'\n\tconcluded: {search_concluded}', announce=True)
        return search_queued, search_running, search_stopped, search_concluded
        pass
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_get_search_term_for_(section: str) -> str:
    try:
        search_term = _sp_if_get_str_at_key_(section, s_key.TERM)
        return search_term if value_provided_for_(search_term) else section
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_increment_result_added_count_for_(section: str) -> None:
    event = f'incrementing result added count for \'{section}\''
    key = s_key.RESULTS_ADDED_COUNT
    try:  # parser surface abstraction depth = 1
        _search_parser(section)[key] = str(get_int_from_search_parser_at_(section, key) + 1)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_increment_search_attempt_count_for_(section: str) -> None:
    event = f'incrementing search attempt count for \'{section}\''
    try:  # FIXME bring into compliance with standard interface functions
        search_attempt_count = get_int_from_search_parser_at_(section, s_key.SEARCH_ATTEMPT_COUNT)
        ml.log_event(f'search try counter at \'{search_attempt_count}\', incrementing..')
        _sp_if_set_int_for_(section, s_key.SEARCH_ATTEMPT_COUNT, search_attempt_count + 1)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_increment_search_state_for_(state_machine):
    section = get_active_section_from_(state_machine)
    event = f'incrementing search state for \'{section}\''
    try:  # FIXME p0, working out bugs.. stripped down for now
        search_state = _sp_if_get_search_states_for_(section)
        queued, running, stopped, concluded = search_state
        if queued:
            queued, running = False, True
            ml.log_event(event + f' from queued to running')
        elif running:
            # FIXME p1, this could increment multiple times if the main_loop is too fast?
            running, stopped = False, True
            ml.log_event(event + f' from running to stopped, will be processed on next loop')
            _sp_if_increment_search_attempt_count_for_(section)
        elif stopped:
            stopped = False
            concluded = True if search_is_concluded_in_(state_machine) else False
            queued = True if not concluded else False
        elif concluded:
            ml.log_event(f'search for \'{section}\' concluded, cannot increment')
        search_states = queued, running, stopped, concluded
        _sp_if_set_search_states_for_(section, search_states)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event('error ' + event)


def _sp_if_ready_to_start_(queued: bool, state_machine) -> bool:
    try:  # FIXME label arg QbitStateMachine without recursive import?
        search_rank = get_int_from_search_parser_at_(state_machine.active_section, s_key.RANK)
        search_rank_required_to_start = _uc_if_get_int_for_key_(u_key.RANK_REQUIRED)
        queue_has_room = not search_queue_is_full_in_(state_machine)
        search_rank_allowed = search_rank <= search_rank_required_to_start
        # FIXME p0, this allows searches to start if they are already running!
        if queued and queue_has_room and search_rank_allowed:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_reduce_search_expectations_for_(section: str) -> None:
    event = f'reducing search expectations for \'{section}\''
    try:
        c_key, re_key = s_key.CONCLUDED, s_key.RESULTS_REQUIRED_COUNT
        ml.log_event(f'reducing search expectations for \'{section}\'')
        er_val = int(s_parser[section][re_key])
        if not er_val:
            ml.log_event(f'concluding search for \'{section}\'', level=ml.WARNING)
            s_parser[section][c_key] = s_key.YES
        er_val -= 1
        _cfg_if_set_parser_value_at_(section, re_key, er_val)  # FIXME fix args
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_search_has_yielded_required_results_for_(state_machine) -> bool:
    section = _sm_if_get_active_section_from_(state_machine)
    event = f'checking if search has yielded required results for \'{section}\''
    try:  # TODO refactor value fetches into parser interface calls
        attempted_searches = get_int_from_search_parser_at_(section, s_key.SEARCH_ATTEMPT_COUNT)
        max_search_attempt_count = get_int_from_search_parser_at_(section, s_key.MAX_SEARCH_COUNT)
        results_added = get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT)
        results_required = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
        if results_added >= results_required:
            _sp_if_set_end_reason_for_(section, s_key.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
            return True
        if attempted_searches >= max_search_attempt_count:
            _sp_if_set_end_reason_for_(section, s_key.TIMED_OUT)  # too many search attempts, conclude
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_set_bool_for_(section: str, key: str, boolean: bool):
    try:  # parser surface abstraction depth = 1
        _search_parser(section)[key] = s_key.YES if boolean else s_key.NO
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_set_end_reason_for_(section, reason_key):
    event = f'setting end reason for \'{section}\' with reason \'{reason_key}\''
    try:  # parser surface abstraction depth = 2
        ml.log_event(f'search \'{section}\' can be concluded, \'{reason_key}\'')
        _sp_if_set_str_for_(section, s_key.SEARCH_STOPPED_REASON, reason_key)
        if all_searches_concluded():
            exit_program()
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_set_int_for_(section: str, key: str, integer: int) -> None:
    event = f'setting int value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 1
        _search_parser(section)[key] = str(integer)
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_set_search_id_for_(section: str, search_id: str) -> None:
    try:  # parser surface abstraction depth = 2
        _sp_if_set_str_for_(section, s_key.ID, search_id)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_set_search_ranks() -> None:
    # FIXME top bug is the soft-lock this function could resolve
    try:  # parser surface abstraction depth = 2
        sort_key = s_key.TIME_LAST_SEARCHED
        sdp_as_dict = _sp_if_get_parser_as_sortable()
        sdp_as_dict_sorted = sorted(sdp_as_dict.items(), key=lambda k: k[1][sort_key])
        number_of_sections = len(sdp_as_dict_sorted)
        for search_rank in range(number_of_sections):
            # TODO this is a bit lazy, could use some refining
            section = sdp_as_dict_sorted[search_rank][0]
            _sp_if_set_str_for_(section, s_key.RANK, str(search_rank))
            ml.log_event(f'search rank \'{search_rank}\' assigned to \'{section}\'')
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_set_search_states_for_(section, search_states) -> None:
    try:
        queued, running, stopped, concluded = search_states
        _sp_if_set_bool_for_(section, s_key.QUEUED, queued)
        _sp_if_set_bool_for_(section, s_key.RUNNING, running)
        _sp_if_set_bool_for_(section, s_key.STOPPED, stopped)
        _sp_if_set_bool_for_(section, s_key.CONCLUDED, concluded)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_set_str_for_(section: str, key: str, string: str):
    event = f'setting str value for search parser at \'{key}\''
    try:  # parser surface abstraction depth = 0
        _search_parser(section)[key] = string
        _search_parser(section)[s_key.TIME_LAST_WRITTEN] = str(dt.now())  # don't do it
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _sp_if_set_time_last_read_for_(section: str) -> None:
    try:  # parser surface abstraction depth = 2
        _sp_if_set_str_for_(section, s_key.TIME_LAST_READ, str(dt.now()))
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def _sp_if_set_time_last_searched_for_(section: str) -> None:
    try:  # parser surface abstraction depth = 2
        _sp_if_set_str_for_(section, s_key.TIME_LAST_SEARCHED, str(dt.now()))
    except Exception as e_err:
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


def _user_configuration(section=empty):
    event = f'getting user config parser at \'{section}\'' if not empty_(section) else f'getting user config parser'
    try:
        if section:
            if section != default:
                ml.log_event(f'the section value \'{section}\' may be an issue', level=ml.WARNING)
        ml.log_event(f'ignoring user section \'{section}\'.. setting to \'{default}\'')
        section = default  # FIXME p3, this is a dumb patch, fix it later
        return u_parser[section] if not empty_(section) else u_parser
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _uc_if_get_all_sections_from_user_config_parser() -> list:
    event = f'getting all sections from user config parser'
    try:
        return _user_configuration().sections()
    except Exception as e_err:
        ml.log_event(e_err.args[0])
        ml.log_event(f'error {event}')


def _uc_if_get_int_for_key_(key: str) -> int:
    event = f'getting int from user configuration parser with key \'{key}\''
    try:
        val = _user_configuration(default)[key]
        for char in val:  # FIXME this would allow values like -79 but also 7-9 which would error
            if char not in digits_or_sign:
                raise TypeError(f'unexpected character in value for key \'{key}\'')
        return int(val)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


def _uc_if_get_str_for_key_(key: str) -> str:
    event = f'getting str from user configuration parser with key \'{key}\''
    try:
        val = _user_configuration(default)[key]
        return str(val)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
        ml.log_event(f'error {event}')


### ### ### ### ### ### ### ### USER CONFIG PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                            USER CONFIG PARSER INTERFACE ABOVE                                      #
#                                                                                                    #
### ### ### ### ### ### ### ### USER CONFIG PARSER INTERFACE # ### ### ### ### ### ### ### ### ### ###
