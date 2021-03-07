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
        results = filter_(results, active_section)
        if not enough_found_in_(results, active_section):
            reduce_search_expectations_for_(active_section)
            # FIXME p0, things crashing out of nowhere
            results_required_count = len(results) if results is not None else 0
        ml.log_event(f'add most popular \'{results_required_count}\' count results')
        for result in results:
            results_added_count = int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT])
            if results_added_count > results_required_count:
                ml.log_event(f'the search for \'{active_section}\' can be concluded', announce=True)
                s_parser_at_active[s_key.CONCLUDED] = s_key.YES
                return  # enough results have been added for this header, stop
            if add_is_successful_for_(result, api, active_section):
                create_metadata_section_for_(result, active_section)
                add_to_found_metadata_as_(result, added=True)
                if enough_results_added_for_(active_section):
                    ml.log_event(f'enough results added for \'{active_section}\'')
                    return  # desired result count added, stop adding
                continue  # result added, go to next
            ml.log_event(f'client failed to add \'{result[m_key.NAME]}\'', level=ml.WARNING)
            continue  # FIXME p2, delete this, no longer does anything
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def add_to_found_metadata_as_(result, added=False):
    try:
        mp = ma_parser if added else mf_parser
        create_metadata_section_for_(mp, result)
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
            val = True if s_parser[section].getboolean(s_key.CONCLUDED) else False
            concluded.append(val)
        if concluded and all(concluded):
            return True
        ml.log_event(f'all searches are not concluded, program continuing')
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def create_metadata_section_for_(mp, result):
    try:
        offset = int(u_parser[u_key.DEFAULT][u_key.UNI_SHIFT])
        ml.log_event(f'save metadata result to parser \'{result[m_key.NAME]}\'')
        m_section = hash_metadata(result[m_key.NAME], offset=offset)
        if mp.has_section(m_section):  # FIXME p3, two files, same name?
            ml.log_event(f'metadata parser already has section \'{m_section}\'', level=ml.WARNING)
            return
        mp.add_section(m_section)
        ml.log_event(f'section has been added to metadata result \'{result[m_key.NAME]}\' for header \'{m_section}\'', announce=True)
        for attribute, detail in result.items():
            h_attr, h_dtl = get_hashed_(attribute, detail, offset)
            # FIXME p3, this will break due to bad parser arg
            write_parser_value_with_(h_attr, h_dtl, m_section, mp)
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


def enough_results_added_for_(section) -> bool:
    try:
        results_added_count = int(s_parser[section][s_key.RESULTS_ADDED_COUNT])
        results_required_count = int(s_parser[section][s_key.RESULTS_REQUIRED_COUNT])
        if results_added_count >= results_required_count:  # TODO check that indexing is perfect
            return True
        return False
    except Exception as e_err:
        print(e_err.args[0])


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
        seeds_min = int(qconf.read_parser_value_with_(s_key.MIN_SEED, section))
        bytes_min = int(qconf.read_parser_value_with_(s_key.SIZE_MIN_BYTES))
        bytes_max = int(qconf.read_parser_value_with_(s_key.SIZE_MAX_BYTES))
        megabytes_min = mega(bytes_min)
        megabytes_max = mega(bytes_max) if bytes_max != -1 else bytes_max
        filename_regex = qconf.read_parser_value_with_(s_key.REGEX_FILENAME, section)
        results_filtered = list()
        for result in results:
            if found and previously_found_(result):
                continue
            if filter_provided_for_(seeds_min):
                result_seeds = int(result[m_key.SUPPLY])
                enough_seeds = True if result_seeds > seeds_min else False
                if not enough_seeds:
                    ml.log_event(f'required seeds \'{seeds_min}\' not met by result with '
                                 f'\'{result_seeds}\' seeds, result : \'{result[m_key.NAME]}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    add_to_found_metadata_as_(result)
                    continue
            if filter_provided_for_(megabytes_min) or filter_provided_for_(megabytes_max):
                bytes_result = int(result[m_key.SIZE])
                megabytes_result = mega(bytes_result)
                if filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                    file_size_in_range = True if bytes_max > bytes_result > bytes_min else False
                elif not filter_provided_for_(megabytes_min) and filter_provided_for_(megabytes_max):
                    file_size_in_range = True if bytes_max > bytes_result else False
                else:
                    file_size_in_range = True if bytes_result > bytes_min else False
                if not file_size_in_range:
                    ml.log_event(f'size requirement \'{megabytes_min}\'MiB to \'{megabytes_max}\'MiB not met by'
                                 f'result with size \'{megabytes_result}\'MiB, result: \'{result[m_key.NAME]}\'',
                                 level=ml.WARNING)
                    pause_on_event(u_key.WAIT_FOR_USER)
                    add_to_found_metadata_as_(result)
                    continue
            if filter_provided_for_(filename_regex):
                ml.log_event(f'filtering results using filename regex \'{filename_regex}\'')
                filename = result[m_key.NAME]
                if not regex_matches(filename_regex, filename):
                    ml.log_event(f'regex \'{filename_regex}\' does not match for \'{filename}\'', level=ml.WARNING)
                    add_to_found_metadata_as_(result)
                    continue
            ml.log_event(f'result \'{result[m_key.NAME]}\' meets all requirements')
            results_filtered.append(result)
            add_to_found_metadata_as_(result, added=True)
        if sort:
            ml.log_event(f'results sorted for {section} # TODO dynamic sort values')
            results = sort_(results_filtered)
        return results
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def filter_provided_for_(parser_val) -> bool:
    try:
        return False if parser_val == -1 or parser_val == 0 else True
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


def get_hashed_(attribute, detail, offset):
    try:
        return hash_metadata(attribute, offset), hash_metadata(detail, offset)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_id_from_(state_machine) -> str:
    try:
        search_id = ''
        if state_machine.active_section in state_machine.active_search_ids:
            search_id = state_machine.active_search_ids[state_machine.active_section]
            ml.log_event(f'search id \'{search_id}\' successfully fetched')
        return search_id
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def get_search_results_for_(active_kv: tuple, api) -> list:
    try:
        results = api.get_result_object_from_(search_id=active_kv[1])
        assert results is not None, 'bad results, fix it or handle it'
        results = results['results']  # TODO do this? or no?
        return results
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def hash_metadata(x, undo=False, offset=0):
    try:
        _undo = -1 if undo else 1
        _hash = ''.join([chr(ord(e) + int(offset)) * _undo for e in str(x) if x])
        ml.log_event(f'hashed from.. \n\t\t\'{x}\' \n\t\tto \n\t\t\'{_hash}\'')
        return _hash
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def increment_result_added_count_for_(section):
    try:
        s_parser[section][s_key.RESULTS_ADDED_COUNT] = \
            str(int(s_parser[section][s_key.RESULTS_ADDED_COUNT]) + 1)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def mega(bytes_: int) -> int:
    try:
        megabytes_ = int(bytes_ / 1000000)
        return megabytes_
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


def previously_found_(result, verbose_log=False):
    try:
        result_name = result[m_key.NAME]
        added_or_found = [*ma_parser.sections(), *mf_parser.sections()]
        if result_name in added_or_found:
            if verbose_log:
                ml.log_event(f'old result found, skipping \'{result_name}\'')
            return True
        ml.log_event(f'new result found \'{result_name}\'')
        return False
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def print_search_ids_from_(active_search_ids):
    try:  # FIXME p3, this is hit too frequently
        ml.log_event('active search headers are..')
        for active_search_header_name in active_search_ids.keys():
            ml.log_event(f'\tsearch header : \'{active_search_header_name}\'')
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def read_parser_value_with_(key, section, meta_add=False, meta_find=False, search=True, settings=False):
    # TODO this interface is lazy, above is a bool, and what is below? this is needlessly confusing
    # FIXME p2, address TODO
    try:
        if meta_add:
            return qconf.read_parser_value_with_(key, section, meta_add=meta_add)
        elif meta_find:
            return qconf.read_parser_value_with_(key, section, meta_find=meta_find)
        elif settings:
            return qconf.read_parser_value_with_(key, section, settings=settings)
        elif search:  # MUST be last since defaults true
            return qconf.read_parser_value_with_(key, section)
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
        write_parser_value_with_(re_key, er_val, section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def regex_matches(filename_regex, filename) -> bool:
    try:
        regex_match = findall(filename_regex, filename)
        if regex_match:
            ml.log_event(f'pattern \'{filename_regex}\' matched against filename \'{filename}\'')
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


def search_set_end_reason(section, reason_key):
    try:
        s_parser[section][s_key.SEARCH_STOPPED_REASON] = reason_key
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)


def set_search_rank_using_(sort_key):
    """
    1. sort the key:value pair of the dict into a tuple of 2 (key, value), sorted by sort_key's value
    2. assign a search rank to each search header based on previous sort
    3. write the search rank to the search detail parser
    :param sort_key:
    :return:
    """
    try:
        sdp_as_dict = qconf.get_search_parser_as_sortable()
        sdp_as_dict_sorted = sorted(sdp_as_dict.items(), key=lambda k: k[1][sort_key])
        number_of_sections = len(sdp_as_dict_sorted)
        for search_rank in range(number_of_sections):
            # TODO this is a bit lazy, could use some refining
            header = sdp_as_dict_sorted[search_rank][0]
            s_parser[header][s_key.RANK] = str(search_rank)
            ml.log_event(f'search rank \'{search_rank}\' assigned to header \'{header}\'')
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
    try:  # TODO, how is this used, refresh?
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


def write_parser_value_with_(parser_key, value, section, mp=None, search=True, settings=False):
    try:  # FIXME p2, clunky interface, refactor
        if mp:
            qconf.write_parser_section_with_key_(parser_key, value, section, mp)
        elif settings:
            qconf.write_parser_section_with_key_(parser_key, value, section, settings=settings)
        elif search:  # MUST be last since search defaults true
            qconf.write_parser_section_with_key_(parser_key, value, section)
    except Exception as e_err:
        ml.log_event(e_err.args[0], level=ml.ERROR)
