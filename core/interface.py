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


def active_section_is_in_memory_of_(state_machine):
    event = f'checking if active section is in memory of state machine'
    try:
        return _stm_if_active_section_is_in_memory_of_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def add_filtered_results_stored_in_(state_machine):
    event = f'adding results from state machine'
    section = get_active_section_from_(state_machine)
    filtered_results = get_results_filtered_from_(state_machine)
    try:
        for result in filtered_results:
            result_name = get_name_from_(result)
            if search_is_concluded_in_(state_machine):
                return
            if add_successful_for_(section, result):  # FIXME p0, sometimes this adds two values
                write_new_metadata_section_from_(result, added=True)
                if enough_results_added_for_(section):
                    ml.log(f'enough results added for \'{section}\'')
                    return  # desired result count added, stop adding
                continue  # result added, go to next
            ml.log(f'client failed to add \'{result_name}\'', level=ml.WARNING)
            write_parsers_to_disk()  # FIXME p0, debug line, consider removing
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def add_search_properties_to_(state_machine, search_properties):
    event = f'adding search properties to state machine'
    try:
        _stm_if_add_search_properties_to_(state_machine, search_properties)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def add_successful_for_(section: str, result: dict) -> bool:
    event = f'checking if add successful for \'{section}\' with result \'{result}\''
    try:
        count_before_add_attempt = _api_if_get_local_results_count()
        ml.log(f'local machine has {count_before_add_attempt} stored results before add attempt..')
        # TODO why does client fail to add so often? outside project scope?
        url = _mdp_if_get_result_metadata_at_key_(m_key.URL, result)
        _api_if_add_result_from_(url, _scp_if_get_add_mode_for_(section))
        pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
        results_added_count = _api_if_get_local_results_count() - count_before_add_attempt
        successfully_added = True if results_added_count else False
        if successfully_added:
            _scp_if_increment_result_added_count_for_(section)
        return successfully_added
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def all_searches_concluded() -> bool:
    event = f'checking if all searches concluded'
    try:
        concluded_bools = list()
        for section in get_all_sections_from_search_parser():
            concluded_bool = True if get_bool_from_(section, s_key.CONCLUDED) else False
            concluded_bools.append(concluded_bool)
        if concluded_bools and all(concluded_bools):
            ml.log(f'all searches concluded', level=ml.WARNING)
            return True
        ml.log(f'all searches are not concluded, program continuing')
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def build_metadata_guid_from_(result: dict) -> str:
    event = f'building metadata section from \'{result}\''
    try:  # FIXME p1, deprecated, refactor this into convert_to_hashed_metadata_from_()
        name, url = \
            _mdp_if_get_result_metadata_at_key_(m_key.NAME, result), \
            _mdp_if_get_result_metadata_at_key_(m_key.URL, result)
        if empty_(url):
            raise ValueError(f'empty url!')
        r_name, delimiter, r_url = hash_metadata(name), ' @ ', hash_metadata(url)
        hashed_name = r_name + delimiter + r_url
        return hashed_name
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def check_for_empty_string_to_replace_with_no_data_in_(value: str) -> str:
    event = f'checking for empty string to replace with \'NO DATA\' in value \'{value}\''
    try:
        return 'NO DATA' if empty_(value) else value
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def conclude_search_for_active_section_in_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'concluding search for active section \'{section}\''
    try:  # TODO is this a pipe?
        set_bool_for_(section, s_key.CONCLUDED, True)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def convert_to_hashed_metadata_from_(result: dict) -> dict:
    offset = get_user_preference_for_(u_key.UNI_SHIFT)
    result[hash_metadata(u_key.GUID)] = hash_metadata(build_metadata_guid_from_(result))
    event = f'building hashed metadata from result'
    try:
        return dict({get_hashed_(validate_metadata_and_type_for_(attr, dtl)[0],
                                 validate_metadata_and_type_for_(attr, dtl)[1],
                                 offset=offset) for attr, dtl in result.items()})
    except Exception as e_err:
        ml.log(f'error {event}')
        ml.log(e_err.args[0])


def create_search_job_for_(pattern: str, plugins: str, category: str):
    event = f'creating search job for \'{pattern}\''
    try:
        return _api_if_create_search_job_for_(pattern, plugins, category)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def empty_(test_string: str) -> bool:
    event = f'checking if value \'{test_string}\' is empty string'
    try:
        return True if test_string == '' else False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def enough_results_added_for_(section: str) -> bool:
    event = f'checking if enough results added for \'{section}\''
    try:
        results_added = get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT)
        results_required = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
        if results_added >= results_required:  # TODO check that indexing is perfect
            return True
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def enough_results_found_in_(section: str, filtered_results: list) -> bool:
    event = f'checking if enough results found in \'{section}\''
    try:
        expected_results_count = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
        filtered_results_count = 0
        if filtered_results is not None:
            filtered_results_count = len(filtered_results)
        if filtered_results_count < expected_results_count:
            ml.log(f'not enough results were found! \'{filtered_results_count}\' '
                         f'results, consider adjusting search parameters', level=ml.WARNING)
            return False
        ml.log(f'search yielded adequate results, \'{filtered_results_count}\' results found')
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def exit_program():
    event = f'exiting program'
    try:
        write_parsers_to_disk()
        ml.log(event)
        exit()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def filter_provided_for_(parser_val) -> bool:
    event = f'checking if filter provided'
    try:
        return False if parser_val == -1 or parser_val == 0 else True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def filter_results_in_(state_machine, found=True, sort=True):
    # FIXME p1, this function needs a lot of work offloading to level 0 abstraction interfaces..
    results_filtered_and_sorted = list()
    section = get_active_section_from_(state_machine)
    results_unfiltered = _stm_if_get_results_unfiltered_from_(state_machine)
    seeds_min = get_int_from_search_parser_at_(section, s_key.MIN_SEED)
    bytes_min = get_int_from_search_parser_at_(section, s_key.SIZE_MIN_BYTES)
    bytes_max = get_int_from_search_parser_at_(section, s_key.SIZE_MAX_BYTES)
    megabytes_min = mega(bytes_min)
    megabytes_max = mega(bytes_max) if bytes_max != -1 else bytes_max
    keywords_to_add = get_keywords_to_add_from_(section)
    keywords_to_skip = get_keywords_to_skip_from_(section)
    event = f'filtering results for \'{section}\''
    try:
        results_filtered = list()
        for result_unfiltered in results_unfiltered:
            result_name = _mdp_if_get_result_metadata_at_key_(m_key.NAME, result_unfiltered)
            if found and _mdp_if_previously_found_(result_unfiltered):
                continue  # filter this result
            if filter_provided_for_(seeds_min):
                result_seeds = int(_mdp_if_get_result_metadata_at_key_(m_key.SUPPLY, result_unfiltered))  # FIXME int
                enough_seeds = True if result_seeds > seeds_min else False
                if not enough_seeds:
                    ml.log(f'required seeds \'{seeds_min}\' not met by result with '
                           f'\'{result_seeds}\' seeds, result : \'{result_name}\'',
                           level=ml.WARNING)
                    write_new_metadata_section_from_(result_unfiltered)  # remember this result
                    continue  # filter this result
            if filter_provided_for_(megabytes_min) or filter_provided_for_(megabytes_max):
                bytes_result = int(_mdp_if_get_result_metadata_at_key_(m_key.SIZE, result_unfiltered))  # FIXME int
                megabytes_result = mega(bytes_result)
                if filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                    file_size_in_range = True if bytes_max > bytes_result > bytes_min else False
                elif not filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                    file_size_in_range = True if bytes_max > bytes_result else False
                else:
                    file_size_in_range = True if bytes_result > bytes_min else False
                if not file_size_in_range:
                    ml.log(f'size requirement \'{megabytes_min}\'MiB to \'{megabytes_max}\'MiB not met by '
                           f'result with size \'{megabytes_result}\'MiB, result: \'{result_name}\'',
                           level=ml.WARNING)
                    write_new_metadata_section_from_(result_unfiltered)  # remember this result
                    continue  # filter this result
            # FIXME p0, entry point for continued implementation of add/skip keyword paradigm
            if filter_provided_for_(keywords_to_add):
                ml.log(f'filtering results using add keywords \'{keywords_to_add}\'')
                filename = get_result_metadata_filename_at_(result_unfiltered)
                if keyword_in_(filename, keywords_to_skip) or not keyword_in_(filename, keywords_to_add):
                    write_new_metadata_section_from_(result_unfiltered)  # remember this result
                    continue  # filter this result
            ml.log(f'result \'{result_name}\' meets all requirements')
            results_filtered.append(result_unfiltered)
        if sort:
            ml.log(f'sorting results for \'{section}\'')
            results_filtered_and_sorted = sort_(results_filtered)
        reduce_search_expectations_if_not_enough_results_found_in_(section, results_filtered_and_sorted)
        return results_filtered_and_sorted
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_active_section_from_(state_machine) -> str:
    event = f'getting active section from state machine'
    try:
        return _stm_if_get_active_section_from_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_active_sections_from_(state_machine) -> list:
    event = f'getting active section from state machine'
    try:
        return _stm_if_get_active_sections_from_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_all_sections_from_metadata_parsers() -> tuple:
    event = f'getting all sections from metadata parser'
    try:
        return _mdp_if_get_all_sections_from_metadata_parsers()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_all_sections_from_user_config_parser() -> list:
    event = f'getting all sections from user config parser'
    try:
        return _ucp_if_get_all_sections_from_user_config_parser()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_all_sections_from_search_parser() -> list:
    event = f'getting all sections from search parser'
    try:  # parser surface abstraction depth = 1
        return _scp_if_get_all_sections_from_search_parser()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_bool_from_(section: str, key: str) -> bool:
    event = f'getting bool from \'{section}\' at \'{key}\''
    try:  # parser surface abstraction depth = 1
        return _scp_if_get_bool_from_(section, key)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_concluded_state_for_(section) -> bool:
    event = f'getting concluded state for \'{section}\''
    try:  # FIXME not used
        return get_search_state_for_(section)[3]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_connection_time_start():
    event = f'getting connection time start'
    try:
        return _api_if_get_connection_time_start()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_hashed_(attribute: str, detail: str, offset: int) -> tuple:
    event = f'getting hashed value with offset \'{offset}\' for attribute \'{attribute}\' and detail \'{detail}\''
    try:
        return hash_metadata(attribute), hash_metadata(detail)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_bool_from_search_parser_at_(section, key) -> bool:
    event = f'getting bool at key \'{key}\''
    try:  # FIXME not used
        return _scp_if_get_bool_at_key_(section, key)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_int_from_search_parser_at_(section, key) -> int:
    event = f'getting int at key \'{key}\''
    try:
        return _scp_if_get_int_at_key_(section, key)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_name_from_(result) -> str:
    event = f'getting name from result'
    try:
        return _mdp_if_get_result_metadata_at_key_(m_key.NAME, result)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_queued_state_for_(section) -> bool:
    event = f'getting queued state for \'{section}\''
    try:  # FIXME not used
        return get_search_state_for_(section)[0]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_keywords_to_add_from_(section: str) -> list:
    event = f'getting keywords to add from \'{section}\''
    try:
        kw_to_add_csv = get_str_from_search_parser_at_(section, s_key.KEYWORDS_ADD)
        return [kw.strip() for kw in kw_to_add_csv.split(sep=',')]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_keywords_to_skip_from_(section: str) -> list:
    event = f'getting keywords to skip from \'{section}\''
    try:
        kw_to_skip_csv = get_str_from_search_parser_at_(section, s_key.KEYWORDS_SKIP)
        return [kw.strip() for kw in kw_to_skip_csv.split(sep=',')]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_result_metadata_filename_at_(result_unfiltered) -> str:
    event = f'getting result metadata filename'
    try:
        return _mdp_if_get_result_metadata_at_key_(m_key.NAME, result_unfiltered)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_results_filtered_from_(state_machine) -> list:
    section = state_machine.active_section
    event = f'getting filtered results from state machine'
    try:
        filtered_results = _stm_if_get_filtered_results_from_(state_machine)
        if filtered_results is None:
            ml.log(f'invalid search results at \'{section}\'', level=ml.WARNING)
            reset_search_state_at_active_section_for_(state_machine)
            return list()
        return filtered_results
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_results_unfiltered_from_(state_machine):
    event = f'getting results unfiltered from state machine'
    try:
        return _stm_if_get_results_unfiltered_from_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_user_preference_for_(key):
    event = f'getting user preference for \'{key}\''
    try:  # FIXME handle diff return types, str/int/etc
        return _ucp_if_get_int_for_key_(key)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_str_from_search_parser_at_(section, key) -> str:
    event = f'getting str at key \'{key}\''
    try:
        return _scp_if_get_str_at_key_(section, key)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_running_state_for_(section) -> bool:
    event = f'getting running state for \'{section}\''
    try:  # FIXME not used
        return get_search_state_for_(section)[1]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_search_id_from_active_section_in_(state_machine) -> str:
    event = f'getting search id from active section in state machine'
    try:
        return _stm_if_get_search_id_from_active_section_in_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def get_search_properties_from_(state_machine) -> tuple:
    event = f'getting search properties from state machine'
    try:  # machine surface abstraction depth = 1
        return _stm_if_get_search_properties_from_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_results_for_(state_machine) -> list:
    event = f'getting search results'
    try:
        return _api_if_get_search_results_for_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_state_for_(section) -> tuple:
    event = f'getting search state for \'{section}\''
    try:
        # TODO print_search_state_for_(section) here
        return _scp_if_get_search_states_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_state_for_active_section_in_(state_machine) -> tuple:
    section = get_active_section_from_(state_machine)
    event = f'getting search state for active section'
    try:
        return get_search_state_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_term_for_(section: str) -> str:
    event = f'getting search term for \'{section}\''
    try:
        return _scp_if_get_search_term_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_search_term_for_active_section_in_(state_machine) -> str:
    section = get_active_section_from_(state_machine)
    event = f'getting search term for active section'
    try:
        return get_search_term_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def get_stopped_state_for_(section) -> bool:
    event = f'getting stopped state for \'{section}\''
    try:  # FIXME not used
        return get_search_state_for_(section)[2]
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def hash_metadata(x: str, undo=False) -> str:
    offset = get_user_preference_for_(u_key.UNI_SHIFT)
    event = f'hashing metadata with offset \'{offset}\' for \'{x}\''
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        ml.log(f'hashed from.. \n\t\t\'{x}\' to.. \n\t\t\'{_hash}\'')
        return _hash
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def increment_search_state_at_active_section_for_(state_machine):
    event = f'incrementing search state for \'{state_machine.active_section}\''
    try:
        _scp_if_increment_search_state_for_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def keyword_in_(filename: str, keywords: list, require_all_kw=False) -> bool:
    event = f'checking if keywords in filename'
    try:
        kw_found_indices = [kw in lower_(filename) for kw in keywords]
        return all(kw_found_indices) if require_all_kw else any(kw_found_indices)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def lower_(filename: str) -> str:
    event = f'converting filename to lower'
    try:
        return ''.join([char.lower() if char in upper else char for char in filename])
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def mega(bytes_: int) -> int:
    event = f'converting \'{bytes_}\' bytes to megabytes'
    try:
        megabytes_ = int(bytes_ / 1000000)
        return megabytes_
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def none_value_(test_value) -> bool:
    event = f'checking if test_value is None'
    try:
        return True if test_value is None else False
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def pause_on_event(pause_type: str):
    event = f'pausing on event \'{pause_type}\''
    try:  # FIXME p0, doesn't work with new architecture, re-think
        parser_at_default = u_parser[u_key.DEFAULT]
        delay = int(parser_at_default[pause_type])
        ml.log(f'waiting \'{delay}\' seconds for event \'{str(pause_type)}\'')
        q_api.pause_for_(delay)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def print_search_ids_from_(active_search_ids: dict):
    event = f'printing search ids from \'{active_search_ids}\''
    try:  # FIXME p3, this is hit too frequently
        ml.log('active search headers are..')
        for active_search_header_name in active_search_ids.keys():
            ml.log(f'\tsearch header : \'{active_search_header_name}\'')
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def print_search_state_for_(section):
    event = f'printing search state for \'{section}\''
    search_queued, search_running, search_stopped, search_concluded = get_search_state_for_(section)
    try:
        ml.log(f'search state for \'{section}\': '
               f'\n\tqueued: {search_queued}'
               f'\n\trunning: {search_running}'
               f'\n\tstopped: {search_stopped}'
               f'\n\tconcluded: {search_concluded}', announcement=True)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def ready_to_start_at_(section: str) -> bool:
    event = f'checking if search is ready to start'
    try:
        ml.log(event)
        return _scp_if_ready_to_start_at_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def ready_to_start_at_active_section_in_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    event = f'checking if search is ready to start'
    try:
        ml.log(event)
        queue_has_room = not search_queue_is_full_in_(state_machine)
        if queue_has_room:
            return ready_to_start_at_(section)
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def reduce_search_expectations_if_not_enough_results_found_in_(section: str, results_filtered: list) -> None:
    event = f'evaluating filtered results for \'{section}\''
    try:
        if not enough_results_found_in_(section, results_filtered):
            _scp_if_reduce_search_expectations_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def reset_search_state_at_active_section_for_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'resetting search state at \'{section}\''
    try:
        ml.log(event, level=ml.WARNING)
        queued, running, stopped, concluded = True, False, False, False
        search_states = queued, running, stopped, concluded
        set_search_states_for_(section, *search_states)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def result_has_enough_seeds() -> bool:
    event = f'checking if result has enough seeds'
    try:  # TODO refactor into this function?
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def save_results_to_(state_machine, save_results_filtered=True):
    result_filter_state = 'unfiltered and filtered' if save_results_filtered else 'unfiltered'
    event = f'saving {result_filter_state} results to state machine'
    try:
        save_search_results_unfiltered_to_(state_machine)
        if save_results_filtered:
            save_search_results_filtered_to_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def save_search_results_filtered_to_(state_machine):
    event = f'saving filtered search results to state machine'
    try:
        _stm_if_save_filtered_search_results_to_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def save_search_results_unfiltered_to_(state_machine):
    event = f'saving unfiltered search results to state machine'
    try:
        _stm_if_save_unfiltered_search_results_to_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


def search_at_active_section_has_completed_in_(state_machine) -> bool:
    event = f'checking if search at active section has completed'
    try:
        return _scp_if_search_at_active_section_has_completed_in_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_concluded_in_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    results_required_count = get_int_from_search_parser_at_(section, s_key.RESULTS_REQUIRED_COUNT)
    results_added_count = get_int_from_search_parser_at_(section, s_key.RESULTS_ADDED_COUNT)
    event = f'checking if search concluded for \'{section}\''
    try:
        if results_added_count > results_required_count:
            ml.log(f'the search for \'{section}\' can be concluded', announcement=True)
            set_bool_for_(section, s_key.CONCLUDED, True)
        return get_bool_from_(section, s_key.CONCLUDED)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_running_at_(section) -> bool:
    event = f'checking if search is running in \'{section}\''
    try:  # machine surface abstraction depth = 1
        return _stm_if_search_is_running_at_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_running_at_active_section_in_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    event = f'checking if search is running at active section'
    try:  # machine surface abstraction depth = 1
        return search_is_running_at_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_stopped_at_(section) -> bool:
    event = f'checking if search is stopped at \'{section}\''
    try:  # machine surface abstraction depth = 1
        return _stm_if_search_is_stopped_at_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_stopped_at_active_section_in_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    event = f'checking if search is stopped at active section'
    try:  # machine surface abstraction depth = 1
        return search_is_stopped_at_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_stopped_in_(state_machine) -> bool:
    event = f'checking if search is stopped in state machine'
    try:  # FIXME hierarchy status < search_id < section < state_machine could be reduced
        return _stm_if_search_is_stopped_in_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_is_stored_in_(state_machine) -> bool:
    event = f'checking if search is running in state machine'
    try:  # machine surface abstraction depth = 1
        return _stm_if_search_is_stored_in_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_queue_is_full_in_(state_machine) -> bool:
    event = f'checking if search queue full'
    try:
        active_search_ids = state_machine.active_sections
        section = _stm_if_get_active_section_from_(state_machine)
        active_search_count = len(active_search_ids)
        if active_search_count < 5:  # maximum simultaneous searches allowed by api
            ml.log(f'search queue is not full, \'{5-active_search_count}\' spaces available')
            print_search_ids_from_(active_search_ids)
            return False
        event = f'search queue is full, cannot add \'{section}\''
        ml.log(event, level=ml.WARNING)
        return True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def search_started_for_(state_machine) -> bool:
    section = get_active_section_from_(state_machine)
    active_sections = get_active_sections_from_(state_machine)
    event = f'checking if search started for \'{section}\''
    try:
        if section in active_sections:
            return True
        return False
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_active_section_to_(section: str, state_machine):
    event = f'setting active section for state machine to \'{section}\''
    try:
        _stm_if_set_active_section_to_(section, state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_bool_for_(section: str, key: str, boolean: bool):
    event = f'setting boolean value \'{boolean}\' for \'{section}\' at \'{key}\''
    try:
        _scp_if_set_bool_for_(section, key, boolean)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


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
            ml.log(f'checking if \'{section}\' exists as active key')
            section_exists = True if section in active_search_ids else False
            if section_exists:
                ml.log(f'section found')
                ml.log(event)
                del active_search_ids[section]
                return active_search_ids  # FIXME see if this return works as expected
            ml.log(f'section not found', level=ml.WARNING)
            return active_search_ids  # FIXME see if this return works as expected
        ml.log(event)
        active_search_ids[section] = {
            'count':    search_count,
            'id':       search_id,
            'status':   search_status
        }
        return active_search_ids
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_search_ranks() -> None:
    # TODO save this to the state machine instance
    event = f'setting search ranks'
    try:
        _scp_if_set_search_ranks()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_search_states_for_(section, *search_states) -> None:
    event = f'setting search states for \'{section}\''
    try:
        _scp_if_set_search_states_for_(section, search_states)
        ml.log(f'search state for \'{section}\': '
                     f'\n\tqueued: {search_states[0]}'
                     f'\n\trunning: {search_states[1]}'
                     f'\n\tstopped: {search_states[2]}'
                     f'\n\tconcluded: {search_states[3]}', announcement=True)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_time_last_read_for_(section: str) -> None:
    event = f'setting time last read for \'{section}\''
    try:
        _scp_if_set_time_last_read_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_time_last_searched_for_(section: str) -> None:
    event = f'setting time last searched for \'{section}\''
    try:
        _scp_if_set_time_last_searched_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def set_time_last_searched_for_active_section_in_(state_machine) -> None:
    section = get_active_section_from_(state_machine)
    event = f'setting time last searched for active section'
    try:
        set_time_last_searched_for_(section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def sort_(results: list) -> list:
    # TODO dynamic sort values
    event = f'sorting results'
    try:
        return sorted(results, key=lambda k: k['nbSeeders'], reverse=True)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def start_search_with_(state_machine):
    section = get_active_section_from_(state_machine)
    search_term = get_search_term_for_active_section_in_(state_machine)
    search_properties = create_search_job_for_(search_term, 'all', 'all')
    add_search_properties_to_(state_machine, search_properties)
    event = f'starting search with \'{section}\''
    search_id = ''
    try:
        search_count, search_id, search_status = search_properties
        write_search_id_to_search_parser_at_(section, search_id)
    except Exception as tuple_exc:
        for arg in tuple_exc.args:
            ml.log(arg)
        ml.log(f'error {event}')
    if search_is_stored_in_(state_machine):
        ml.log(f'search \'{search_term}\' successfully started for \'{section}\' with id \'{search_id}\'')
        set_time_last_searched_for_active_section_in_(state_machine)
        increment_search_state_at_active_section_for_(state_machine)
        return
    ml.log(f'stale search, bad search status and/or bad search id, re-queueing \'{section}\'', level=ml.WARNING)
    reset_search_state_at_active_section_for_(state_machine)


def update_search_properties_for_(state_machine):
    event = f'updating search properties for state machine'
    try:
        _stm_if_update_search_properties_for_(state_machine)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def validate_metadata_and_type_for_(attr: str, dtl: str) -> tuple:
    expected_value_types = [int, str]
    parser_key, parser_value = attr, dtl
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
        parser_value = check_for_empty_string_to_replace_with_no_data_in_(parser_value)
        return parser_key, parser_value
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def value_provided_for_(value_to_check) -> bool:
    event = f'checking if value provided for \'{value_to_check}\''
    try:
        return False if value_to_check == '0' else True
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def write_new_metadata_section_from_(result: dict, added=False) -> None:
    parser = 'added' if added else 'failed'
    event = f'writing metadata to \'{parser} from \'{result}\''
    try:
        result_hashed = convert_to_hashed_metadata_from_(result)
        _mdp_if_create_section_for_(ma_parser if added else mf_parser, result_hashed)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def write_parsers_to_disk():
    event = f'writing parsers to disk'
    try:  # parser surface abstraction depth = 1
        ml.log(event)
        _cfg_if_write_parsers_to_disk()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def write_search_id_to_search_parser_at_(section, search_id) -> None:
    event = f'writing search id \'{search_id}\' to search parser at section \'{section}\''
    try:
        _scp_if_set_str_for_(section, s_key.ID, search_id)
    except Exception as e_err:
        ml.log(e_err.args[0])
        ml.log(f'error {event}')


### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                        API INTERFACE BELOW                                         #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###


def _api_if_add_result_from_(url: str, is_paused: bool):
    try:  # api surface abstraction level = 0
        q_api.add_result_from_(url, is_paused)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _api_if_create_search_job_for_(pattern: str, plugins: str, category: str) -> tuple:
    try:  # api surface abstraction level = 0
        job = q_api.qbit_client.search.start(pattern, plugins, category)
        assert job is not None, 'bad search job, fix it or handle it'
        count, sid, status = q_api.get_search_info_from_(job)
        ml.log(f'qbit client created search job for \'{pattern}\'')
        return count, sid, status
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _api_if_get_connection_time_start():
    try:  # api surface abstraction level = 0
        return q_api.get_connection_time_start()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _api_if_get_local_results_count():
    try:  # api surface abstraction level = 0
        return q_api.get_local_results_count()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _api_if_get_search_results_for_(state_machine) -> list:
    search_id = get_search_id_from_active_section_in_(state_machine)
    results = q_api.get_result_object_at_(search_id)
    try:  # api surface abstraction level = 0
        if results is None:  # FYI this could cause permanent fatal errors depending on search id handling
            raise ValueError('unexpected empty results')
        return results[m_key.RESULTS]
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _api_if_get_search_properties_for_(search_id: str) -> tuple:
    try:  # api surface abstraction depth = 0
        return q_api.get_search_properties_for_(search_id=search_id)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                        API INTERFACE ABOVE                                         #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### api if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                         CFG INTERFACE BELOW                                        #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###


def _cfg_if_get_parser_value_at_(section: str, key: str,
                                 meta_add=False, meta_find=False,
                                 search=True, settings=False):
    try:  # TODO deprecate cfg interface methods
        if meta_add:
            return QConf.read_parser_value_with_(key, section, meta_add=meta_add)
        elif meta_find:
            return QConf.read_parser_value_with_(key, section, meta_find=meta_find)
        elif settings:
            return QConf.read_parser_value_with_(key, section, settings=settings)
        elif search:  # MUST be last since defaults true
            return QConf.read_parser_value_with_(key, section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _cfg_if_set_parser_value_at_(section: str, parser_key: str, value,
                                 mp=None, search=True, settings=False):
    try:  # TODO deprecate cfg interface methods
        if mp:
            QConf.write_parser_section_with_key_(parser_key, value, section, mp)
        elif settings:
            QConf.write_parser_section_with_key_(parser_key, value, section, settings=settings)
        elif search:  # MUST be last since search defaults true
            QConf.write_parser_section_with_key_(parser_key, value, section)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _cfg_if_write_parsers_to_disk():
    try:  # TODO deprecate cfg interface methods
        QConf.write_config_to_disk()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                         CFG INTERFACE ABOVE                                        #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### cfg if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### mdp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                   METADATA PARSER INTERFACE BELOW                                  #
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
    hashed_result_guid = hashed_result[hash_metadata(m_key.GUID, True)]
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
    try:  # FIXME should this interface to QConf be re-thought?
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
#                                   METADATA PARSER INTERFACE ABOVE                                  #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### mdp if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### scp if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    SEARCH PARSER INTERFACE BELOW                                   #
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
    try:  # parser surface abstraction depth = 0
        return _scp_if_get_bool_from_(section, s_key.ADD_PAUSED)
    except Exception as e_err:
        ml.log(e_err.args[0])


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
        ml.log(event)
        for char in integer_as_str:  # FIXME this would allow values like -79 but also 7-9 which would error
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


def _scp_if_get_parser_as_sortable() -> dict:
    event = f'getting search parser as sortable'
    try:  # FIXME remove/replace this function
        return QConf.get_search_parser_as_sortable()
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_get_search_id_for_(section: str) -> str:
    try:
        search_id = _scp_if_get_str_at_key_(section, s_key.ID)
        return search_id
    except Exception as e_err:
        ml.log(e_err.args[0])


def _scp_if_get_search_states_for_(section) -> tuple:
    try:  # parser surface abstraction depth = 2
        _scp_if_set_str_for_(section, s_key.TIME_LAST_READ, str(dt.now()))  # FIXME move to function
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
    event = f'incrementing search attempt count for \'{section}\''
    try:  # FIXME bring into compliance with standard interface functions
        search_attempt_count = get_int_from_search_parser_at_(section, s_key.SEARCH_ATTEMPT_COUNT)
        ml.log(f'search try counter at \'{search_attempt_count}\', incrementing..')
        _scp_if_set_int_for_(section, s_key.SEARCH_ATTEMPT_COUNT, search_attempt_count + 1)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log(f'error {event}')


def _scp_if_increment_search_state_for_(state_machine):
    section = get_active_section_from_(state_machine)
    event = f'incrementing search state for \'{section}\''
    try:  # FIXME p0, working out bugs.. stripped down for now
        search_state = _scp_if_get_search_states_for_(section)
        queued, running, stopped, concluded = search_state
        if queued:
            queued, running = False, True
            ml.log(event + f' from queued to running')
        elif running:
            # FIXME p1, this could increment multiple times if the main_loop is too fast?
            running, stopped = False, True
            ml.log(event + f' from running to stopped, will be processed on next loop')
            _scp_if_increment_search_attempt_count_for_(section)
        elif stopped:
            stopped = False
            concluded = True if search_is_concluded_in_(state_machine) else False
            queued = True if not concluded else False
        elif concluded:
            ml.log(f'search for \'{section}\' concluded, cannot increment')
        search_states = queued, running, stopped, concluded
        _scp_if_set_search_states_for_(section, search_states)
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)
        ml.log('error ' + event)


def _scp_if_ready_to_start_at_(section) -> bool:
    try:  # FIXME label arg QbitStateMachine without recursive import?
        # FIXME p0, this allows searches to start if they are already running!
        search_rank = get_int_from_search_parser_at_(section, s_key.RANK)  # TODO delete me
        search_rank = _scp_if_get_int_at_key_(section, s_key.RANK)
        search_rank_required_to_start = _ucp_if_get_int_for_key_(u_key.RANK_REQUIRED)
        search_rank_allowed = search_rank <= search_rank_required_to_start
        queued = _scp_if_get_search_states_for_(section)[0]
        if queued and search_rank_allowed:
            return True
        return False
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
        _cfg_if_set_parser_value_at_(section, re_key, er_val)  # FIXME fix args
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


def _scp_if_set_search_ranks() -> None:
    # FIXME top bug is the soft-lock this function could resolve
    try:  # parser surface abstraction depth = 2
        sort_key = s_key.TIME_LAST_SEARCHED
        scp_as_dict = _scp_if_get_parser_as_sortable()
        scp_as_sorted_list_of_tuples = sorted(scp_as_dict.items(), key=lambda k: k[1][sort_key])
        number_of_sections = len(scp_as_sorted_list_of_tuples)
        for ranked_search_index in range(number_of_sections):
            section = scp_as_sorted_list_of_tuples[ranked_search_index][0]
            _scp_if_set_str_for_(section, s_key.RANK, str(ranked_search_index))
            ml.log(f'search rank \'{ranked_search_index}\' assigned to \'{section}\'')
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
#                                    SEARCH PARSER INTERFACE ABOVE                                   #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### scp if ### ### ### ### ### ### ### ### ### ### ### ###

### ### ### ### ### ### ### ### ### ### ### ### stm if ### ### ### ### ### ### ### ### ### ### ### ###
#                                                                                                    #
#                                    STATE MACHINE INTERFACE BELOW                                   #
#                                                                                                    #
### ### ### ### ### ### ### ### ### ### ### ### stm if ### ### ### ### ### ### ### ### ### ### ### ###


def _stm_if_active_section_is_in_memory_of_(state_machine):
    section = _stm_if_get_active_section_from_(state_machine)
    active_sections = _stm_if_get_active_sections_from_(state_machine)
    try:
        return True if section in active_sections else False
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_add_search_properties_to_(state_machine, search_properties: tuple) -> None:
    section = _stm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        _stm_if_init_active_search_id_for_(state_machine, section)
        state_machine.active_sections[section]['count'] = search_properties[0]
        state_machine.active_sections[section]['id'] = search_properties[1]
        state_machine.active_sections[section]['status'] = search_properties[2]
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_active_search_ids_from_(state_machine) -> list:
    event = f'getting active search id values from state machine'
    try:  # machine surface abstraction depth = 1
        active_search_ids = list()
        for section in state_machine.active_sections:
            section_id = _stm_if_get_search_id_from_(state_machine, section)
            active_search_ids.append(section_id)
        return active_search_ids
    except Exception as e_err:
        ml.log(f'error {event}')
        ml.log(e_err.args[0])


def _stm_if_get_active_section_from_(state_machine) -> str:
    try:  # machine surface abstraction depth = 0
        return state_machine.active_section
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_get_active_sections_from_(state_machine) -> list:
    # FIXME this returns dict or list? it works as-is but.. need to be sure
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


def _stm_if_get_filtered_results_from_(state_machine):
    section = _stm_if_get_active_section_from_(state_machine)
    try:
        return state_machine.active_sections[section]['filtered_results']
    except Exception as e_err:
        ml.log(e_err.args[0])


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
    # TODO just noting this object has two surfaces, could be useful
    try:  # api/machine surface abstraction depth = 1/1
        search_id = _stm_if_get_active_section_search_id_from_(state_machine)
        search_properties = _api_if_get_search_properties_for_(search_id)
        return search_properties
    except Exception as e_err:
        ml.log(e_err.args[0], level=ml.ERROR)


def _stm_if_get_results_unfiltered_from_(state_machine):
    section = _stm_if_get_active_section_from_(state_machine)
    try:
        return state_machine.active_sections[section]['unfiltered_results']
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_init_active_search_id_for_(state_machine, section: str) -> None:
    try:  # machine surface abstraction depth = 0
        state_machine.active_sections[section] = dict()
    except Exception as e_err:
        ml.log(e_err.args[0])


def _stm_if_save_filtered_search_results_to_(state_machine):
    # FIXME p0, interface function relies on wrapper function, should be opposite
    section = _stm_if_get_active_section_from_(state_machine)
    try:  # machine surface abstraction depth = 0
        filtered_results = filter_results_in_(state_machine)
        # sm_if_update_search_properties_for_(state_machine)  # TODO delete me
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
        active_search_ids = _stm_if_get_active_search_ids_from_(state_machine)
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
    try:
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
