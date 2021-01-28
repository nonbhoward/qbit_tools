from data_src.configuration_file_reader import *
from data_src.WEB_API_CREDENTIALS import HOST, USER, PASS
from minimalog.minimal_log import MinimalLog
from re import findall
from time import sleep
import datetime
import qbittorrentapi
behavior_key, config_file, config_path, results_key, search_key = bKey(), cFile(), cPath(), rKey(), sKey()


class QbitTasker:
    def __init__(self):
        ml.log_event('initialize {}'.format(self.__class__), event_completed=False, announce=True)
        self.qbit_client_connected = True if self._client_is_connected() else False
        self.data_path = self._get_data_path()
        self.search_config_filename, self.result_config_filename, self.behavior_config_filename = \
            self._get_config_filename(SEARCH), self._get_config_filename(RESULT), self._get_config_filename(BEHAVIOR)
        self.search_parser, self.result_parser, self.behavior_parser = \
            self._config_get_parser(SEARCH), self._config_get_parser(RESULT), self._config_get_parser(SETTINGS)
        self._connection_time_start = datetime.datetime.now()
        self._reset_search_ids()
        self.active_search_ids, self.active_header = dict(), ''
        ml.log_event('initialize {}'.format(self.__class__), event_completed=True, announce=True)

    def initiate_and_monitor_searches(self):
        try:
            for section_header in self.search_parser.sections():
                self.active_header = section_header
                ml.log_event('monitoring search header {}'.format(self.active_header))
                self._manage_state_updates(self._get_search_state())
            self._config_to_disk()
        except KeyError as k_err:
            ml.log_event(k_err)

    def pause_on_event(self, pause_type):
        try:
            if pause_type == LOOPS:
                timestamp, delay = _get_timestamp(), int(self.behavior_parser[DEFAULT][behavior_key.wait_between_main_loops])
                ml.log_event('{} waiting {} seconds for loop..\n\n'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == SEARCH:
                timestamp, delay = _get_timestamp(), int(self.behavior_parser[DEFAULT][behavior_key.wait_between_searches])
                ml.log_event('{} waiting {} seconds for search..\n\n'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == ADD:
                timestamp, delay = _get_timestamp(), int(self.behavior_parser[DEFAULT][behavior_key.wait_between_result_adds])
                ml.log_event('{} waiting {} seconds for add..\n\n'.format(timestamp, delay))
                sleep(delay)
            else:
                timestamp, delay = _get_timestamp(), int(self.behavior_parser[DEFAULT][behavior_key.wait_for_some_other_reason])
                ml.log_event('{} waiting {} seconds for other..\n\n'.format(timestamp, delay))
                sleep(delay)
        except ValueError as v_err:
            ml.log_event(v_err)

    def transfer_files_to_remote(self):
        pass

    def _save_remote_metadata_to_local_results_sorting_by_(self, attribute, filtered_results) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        ml.log_event('add results by {}'.format(attribute), event_completed=False)
        # TODO implement attribute here, 'rKey.nbSeeders' instead of 'popularity
        most_popular_results = self._get_most_popular_results(filtered_results)
        search_id_valid = self._search_id_is_valid()
        if not search_id_valid:
            ml.log_event('search id for {} is invalid'.format(self.active_header))
            self._update_search_states(QUEUED)  # wanted to add result but search_id was bad, re-queue search
            return False
        if most_popular_results is not None:
            self._check_if_search_is_concluded()  # we found some results, have we met our 'concluded' criteria?
            self._config_set_search_id_as_inactive()
            ml.log_event('results sorted by popularity for {}'.format(self.active_header))
            for result in most_popular_results:
                if self._result_has_enough_seeds(result):
                    self._qbit_add_result(result)
        ml.log_event('add results by popularity', event_completed=True)

    def _all_searches_concluded(self) -> bool:
        # TODO would be nice to exit if all jobs exceed set limits
        try:
            concluded = list()
            for section in self.search_parser.sections():
                for key in self.search_parser[section]:
                    if key == search_key.concluded:
                        search_concluded = self.search_parser[section].getboolean(key)
                        concluded.append(search_concluded)
            if all(concluded):
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err)

    def _check_if_search_is_concluded(self):
        try:
            if self._search_has_yielded_the_required_results():
                ml.log_event('search {} has concluded, disabling'.format(self.active_header), announce=True)
                self._update_search_states(CONCLUDED)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _client_is_connected(self) -> bool:
        """
        connect to the client, fetch check app version and web api version
        :return: bool, true if able to populate all data successfully
        """
        ml.log_event('connecting to client', event_completed=False)
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                ml.log_event('connecting to client app version {} web api version {}'.format(
                    app_version, web_api_version), event_completed=True)
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event(r_err)

    @staticmethod
    def _config_file_has_sections(config_parser) -> bool:
        ml.log_event('check if config for {} has sections'.format(config_parser), False)
        try:
            config_file_section_count = len(config_parser.sections())
            if config_file_section_count > 0:
                ml.log_event('check if config for {} has sections'.format(config_parser), True)
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event('{}: configuration file has no sections'.format(r_err))

    def _config_get_search_pattern(self) -> str:
        ml.log_event('get search pattern for {}'.format(self.active_header))
        try:
            if search_key.pattern not in self.search_parser[self.active_header].keys():
                search_pattern = '.*'
                return search_pattern
            search_pattern = self.search_parser[self.active_header][search_key.pattern]
            return search_pattern
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_get_search_term(self) -> str:
        ml.log_event('get search term for {}'.format(self.active_header))
        try:
            if 'search_term' not in self.search_parser[self.active_header].keys():
                search_term = self.active_header
                return search_term
            search_term = self.search_parser[self.active_header]['search_term']
            search_term = self.search_parser[self.active_header][search_key.term]
            return search_term
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_increment_search_try_counter(self):
        try:
            search_try_count = int(self.search_parser[self.active_header][search_key.attempts])
            ml.log_event('search try counter at {}, incrementing..'.format(search_try_count))
            self.search_parser[self.active_header][search_key.attempts] = str(search_try_count + 1)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_set_search_id_as_active(self):
        search_id = self.active_search_ids.get(self.active_header, '')
        ml.log_event('search id {} set as active'.format(search_id))
        try:
            self.search_parser[self.active_header][search_key.id] = search_id
            self.active_search_ids[self.active_header] = search_id
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_set_search_id_as_inactive(self):
        try:
            search_id = self.search_parser[self.active_header][search_key.id]
            if self._search_id_active():
                self.search_parser[self.active_header][search_key.id] = str(0)
                ml.log_event('search id {} set as inactive'.format(search_id))
                del self.active_search_ids[self.active_header]
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            parser_data = self._get_all_parsers()
            for parser in parser_data:
                ml.log_event('.. {} ..'.format(parser[0]))
                with open(parser[0], 'w') as parser_file:
                    parser[1].write(parser_file)
        except OSError as o_err:
            ml.log_event(o_err)

    def _filter_results(self):
        filtered_results_count, filtered_results, results = 0, list(), self._qbit_get_search_results()
        if results is None:
            return None, 0
        for result in results[results_key.results]:
            file_name = result[results_key.name]
            search_pattern = self._config_get_search_pattern()
            if self._pattern_matches(search_pattern, file_name):
                filtered_results.append(result)
                filtered_results_count += 1
        ml.log_event('{} filtered results found'.format(filtered_results_count))
        return filtered_results, filtered_results_count

    def _get_active_search_ids(self) -> str:
        try:
            active_search_id = self.active_search_ids.get(self.active_header)
            ml.log_event('get active search id {} for {}'.format(active_search_id, self.active_header))
            return active_search_id
        except KeyError as k_err:
            ml.log_event(k_err)

    def _get_most_popular_results(self, filtered_results) -> list:
        expected_search_result_count = self.search_parser[search_key.expected_search_result_count]
        ml.log_event('get most popular results from {} up to count {}'.format(
            filtered_results, expected_search_result_count), event_completed=False)
        found_result_count = len(filtered_results)
        expected_search_result_count = found_result_count if not \
            _enough_results_in_(filtered_results) else expected_search_result_count
        try:
            popularity_sorted_list = sorted(filtered_results, key=lambda k: k[results_key.seeders], reverse=True)
            most_popular_results = list()
            for index in range(expected_search_result_count):
                # TODO should do some debug here to and see if indexes are working as expected
                most_popular_results.append(popularity_sorted_list[index])
            return most_popular_results
        except IndexError as i_err:
            ml.log_event(i_err)

    def _get_all_parsers(self) -> tuple:
        try:
            parser_data = (self.behavior_config_filename, self.behavior_parser), \
                          (self.result_config_filename, self.result_parser), \
                          (self.search_config_filename, self.search_parser)
            return parser_data
        except ValueError as v_err:
            ml.log_event(v_err)

    def _get_priority_key_for_search_result_sorting(self):
        # TODO refactoring other stuff then fixing this
        try:
            if self.behavior_parser[behavior_key.result_priority] == results_key.supply:
                if 'something' == results_key.supply:
                    return results_key.priority
            priority_key = self.result_parser[results_key.priority]

            return results_key.supply
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)
        pass

    def _get_search_state(self) -> tuple:
        """
        :return: search states
        """
        ml.log_event('get search state for {}'.format(self.active_header))
        try:
            self.search_parser[self.active_header][search_key.last_read] = str(datetime.datetime.now())
            _search_queued = self.search_parser[self.active_header].getboolean(search_key.queued)
            _search_running = self.search_parser[self.active_header].getboolean(search_key.running)
            _search_stopped = self.search_parser[self.active_header].getboolean(search_key.stopped)
            _search_concluded = self.search_parser[self.active_header].getboolean(search_key.concluded)
            ml.log_event('\n\nsearch state for {}: \nqueued: {}\nrunning: {}\nstopped: {}\nconcluded: {}\n\n'.format(
                self.active_header, _search_queued, _search_running, _search_stopped, _search_concluded))
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except KeyError as k_err:
            ml.log_event(k_err)

    def _hash(self, x, un=False):
        try:
            _pol = -1 if un else 1
            _hash = ''.join([chr(ord(e) + int(self.behavior_parser[DEFAULT][behavior_key.unicode_shift_offset]) * _pol) for e in str(x) if x])
            ml.log_event('hashed from {} to {}'.format(x, _hash))
            return _hash
        except ValueError as v_err:
            ml.log_event(v_err)

    def _manage_state_updates(self, section_states):
        ml.log_event('manage state updates..')
        _search_queued, _search_running, _search_stopped, _search_concluded = section_states
        if _search_queued and not self._search_queue_full():
            self._start_search()  # search is in queue and queue has room, attempt to start this search
        elif _search_running:
            _search_status = self._qbit_get_search_status()
            if search_key.running in _search_status:
                pass  # search is ongoing, do nothing
            elif search_key.stopped in _search_status:
                self._update_search_states(search_key.stopped)  # mark search as stopped (finished)
            else:
                self._update_search_states(search_key.queued)  # search status unexpected, re-queue this search
        elif _search_stopped:
            filtered_results, filtered_results_count = self._filter_results()
            if filtered_results is not None and filtered_results_count > 0:
                # TODO results_key.supply could be sort by any key, how to get that value here?
                search_priority = self._get_priority_key_for_search_result_sorting()
                self._save_remote_metadata_to_local_results_sorting_by_(
                    search_priority, filtered_results)  # search is finished, attempt to add results
            else:
                self._update_search_states(QUEUED)  # search is stopped, but no results found, re-queue this search
        elif _search_concluded:
            pass
        else:
            self._update_search_states(QUEUED)
        self.pause_on_event(SEARCH)

    @staticmethod
    def _pattern_matches(search_pattern, file_name) -> bool:
        try:
            pattern_match = findall(search_pattern, file_name)
            if pattern_match:
                ml.log_event('matched pattern {} to {}'.format(search_pattern, file_name))
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event(str(r_err) + 'error with regex, search_pattern: {} file_name: {}'.format(
                search_pattern, file_name), level=ml.ERROR)

    def _qbit_add_result(self, result):
        try:
            count_before = self._qbit_count_all_torrents()
            ml.log_event('local machine has {} stored results before add attempt..'.format(count_before), announce=True)
            self.qbit_client.torrents_add(urls=result['fileUrl'], is_paused=True)
            self.pause_on_event(ADD)
            results_added = self._qbit_count_all_torrents() - count_before
            if results_added > 0:
                ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                self._result_parser_store(result)
                ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                self.search_parser[self.active_header]['results_added'] = str(int(
                    self.search_parser[self.active_header]['results_added']) + results_added)
                return
        except ConnectionError as c_err:
            ml.log_event(c_err, level=ml.ERROR)

    def _qbit_count_all_torrents(self) -> int:
        try:
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            return local_result_count
        except RuntimeError as r_err:
            ml.log_event(r_err, level=ml.ERROR)

    def _qbit_create_search_job(self, pattern, plugins, category) -> tuple:
        try:
            _job = self.qbit_client.search.start(pattern, plugins, category)
            _status = _job.status()
            _state = _status.data[0]['status']
            _id = str(_status.data[0]['id'])
            _count = _status.data[0]['total']
            ml.log_event('qbit client created search job for {}'.format(pattern))
            return _job, _status, _state, _id, _count
        except ConnectionError as c_err:
            ml.log_event(c_err, level=ml.ERROR)

    def _qbit_get_search_results(self):
        try:
            search_id = self._get_active_search_ids()
            search_id_valid = self._search_id_is_valid(search_id)
            if search_id_valid:
                results = self.qbit_client.search_results(search_id)
                ml.log_event('qbit client get search results', event_completed=True)
                return results
            return None
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _qbit_get_search_status(self) -> str:
        """
        :return: the status of the search at search_id
        """
        try:
            ml.log_event('checking search status for section: {}'.format(self.active_header))
            search_id, search_status = self.search_parser[self.active_header]['search_id'], None
            search_id_valid = self._search_id_is_valid(search_id)
            if search_id_valid:
                ml.log_event('getting search status for header {} with search_id {}'.format(
                    self.active_header, search_id))
                if search_id in self.active_search_ids.values():
                    ongoing_search = self.qbit_client.search_status(search_id=search_id)
                    search_status = ongoing_search.data[0]['status']
            ml.log_event('search status for section: {} is {}'.format(self.active_header, search_status))
            ml.log_event('qbit client get search status')
            return search_status
        except ConnectionError as c_err:
            event = 'unable to process search for section: {}'.format(self.active_header)
            ml.log_event(event, level=ml.ERROR)

    def _reset_search_ids(self):
        """
        upon initialization of new object, delete expired search_ids
        :return: None  # TODO should i return success?
        """
        ml.log_event('reset search ids',event_completed=False)
        try:
            for section_header in self.search_parser.sections():
                self.active_header = section_header
                ml.log_event('reset search_id for section: {}'.format(self.active_header))
                self._update_search_states(QUEUED)
                ml.log_event('reset search ids', event_completed=True)
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _result_has_enough_seeds(self, result) -> bool:
        try:
            minimum_seeds = int(self.search_parser[self.active_header][search_key.minimum_seeds])
            result_seeds = result[results_key.supply]
            if result_seeds > minimum_seeds:
                ml.log_event('result {} has {} seeds, attempting to add'.format(result['fileName'], result_seeds))
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _result_parser_store(self, result):
        ml.log_event('store result {} in result parser'.format(result))
        try:
            if not self.result_parser.has_section(self._hash(result['fileName'])):
                self.result_parser.add_section(self._hash(result['fileName']))
                header = self._hash(result['fileName'])
                for attribute, detail in result.items():
                    # TODO there are some redundant log commands 'above' and 'below' this entry
                    # TODO i think this entry is causing the redundant log commands with _hash() calls
                    h_attr, d_attr = self._hash(attribute), self._hash(detail)
                    ml.log_event('add to results ledger, attribute {} detail {}'.format(h_attr, d_attr))
                    self.result_parser[header][h_attr] = d_attr
                    self.pause_on_event(99)
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _results_fetch_all_data(self) -> dict:
        ml.log_event('fetching results from disk', event_completed=False)
        try:
            all_data = dict()
            for section in self.result_parser.sections():
                all_data[self._hash(section, True)] = dict()
                for key, detail in self.result_parser[section].items():
                    all_data[self._hash(section, True)][key] = self._hash(detail, True)
            ml.log_event('fetching results from disk', event_completed=True)
            return all_data
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _search_id_active(self) -> bool:
        try:
            search_id = self.search_parser[self.active_header][search_key.id]
            if search_id == self.active_search_ids[self.active_header]:
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _search_id_is_valid(self) -> bool:
        search_id = self.active_search_ids.get(self.active_header, '')
        ml.log_event('check if search id {} is valid'.format(search_id))
        try:
            if search_id is not None:
                if search_id != EMPTY:
                    return True
            return False
        except ValueError as v_err:
            ml.log_event(v_err, level=ml.ERROR)

    def _search_queue_full(self) -> bool:
        ml.log_event('check search queue..')
        try:
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                ml.log_event('search queue is not full, currently active search ids: {}'.format(self.active_search_ids.keys()))
                return False
            ml.log_event('search queue is FULL, cannot add {}.. currently active search ids: {}'.format(
                self.active_header, self.active_search_ids.keys()), announce=True)
            return True
        except RuntimeError as r_err:
            ml.log_event(r_err, level=ml.ERROR)

    def _search_has_yielded_the_required_results(self) -> bool:
        """
        decides if search is ready to be marked as completed (ADDED)
        :return: bool, search completed
        """
        ml.log_event('check if search can be concluded', event_completed=False)
        try:
            attempted_searches = int(self.search_parser[self.active_header][search_key.attempts])
            maximum_allowed_search_attempts = int(self.search_parser[self.active_header][search_key.attempts_max])
            results_added = int(self.search_parser[self.active_header][search_key.results_added])
            results_required = int(self.search_parser[self.active_header][search_key.results_required])
            if results_added > results_required:
                ml.log_event('search {} can be concluded, '
                             'requested result count has been added'.format(self.active_header),
                             event_completed=True)
                self._search_set_end_reason(REQUIRED_RESULTS_FOUND)  # enough results have been added, conclude
                return True
            elif attempted_searches > maximum_allowed_search_attempts:
                ml.log_event('search can be concluded, '
                             'too many search attempts w/o meeting requested result count'.format(self.active_header),
                             event_completed=True)
                self._search_set_end_reason(TIMED_OUT)  # too many search attempts without required results, conclude
                return True
            ml.log_event('search {} will be allowed to continue'.format(self.active_header), event_completed=True)
            return False
        except KeyError as k_err:
            ml.log_event(k_err)
            
    def _search_set_end_reason(self, reason):
        try:
            ml.log_event('setting end reason \'{}\' for search header {}'.format(reason, self.active_header))
            self.search_parser[self.active_header][search_key.end_reason] = reason
            search_key.end_reason = reason
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _start_search(self):
        try:
            search_term = self._config_get_search_term()
            search_job, search_status, search_state, search_id, search_count = \
                self._qbit_create_search_job(search_term, 'all', 'all')
            if RUNNING in search_state:  # search started successfully
                ml.log_event('search started for {}'.format(self.active_header), event_completed=True)
                self._config_set_search_id_as_active()
                self._update_search_states(STARTING)
            elif STOPPED in search_status:
                ml.log_event('search not successfully started for {}'.format(
                    self.active_header), announce=True, level=ml.WARNING)
        except KeyError as k_err:
            ml.log_event('{}: unable to process search job'.format(k_err), level=ml.ERROR)

    def _update_search_states(self, job_state):
        ml.log_event('updating the search state machine..')
        try:
            if job_state == QUEUED:
                self.search_parser.remove_section(search_key.id)
                self.search_parser[self.active_header]['search_queued'] = YES
                self.search_parser[self.active_header]['search_running'] = NO
                self.search_parser[self.active_header]['search_stopped'] = NO
                self.search_parser[self.active_header]['search_concluded'] = NO
            elif job_state == STARTING:
                self.search_parser[self.active_header]['search_queued'] = NO
                self.search_parser[self.active_header]['search_running'] = YES
                self.search_parser[self.active_header]['search_stopped'] = NO
                self.search_parser[self.active_header]['search_concluded'] = NO
                self._config_increment_search_try_counter()
            elif job_state == STOPPED:
                self.search_parser[self.active_header]['search_queued'] = NO
                self.search_parser[self.active_header]['search_running'] = NO
                self.search_parser[self.active_header]['search_stopped'] = YES
                self.search_parser[self.active_header]['search_concluded'] = NO
            elif job_state == CONCLUDED:
                self.search_parser[self.active_header]['search_queued'] = NO
                self.search_parser[self.active_header]['search_running'] = NO
                self.search_parser[self.active_header]['search_stopped'] = NO
                self.search_parser[self.active_header]['search_concluded'] = YES
            else:
                pass
            self.search_parser[self.active_header]['last_write'] = str(datetime.datetime.now())
        except KeyError as k_err:
            ml.log_event(k_err)


def _enough_results_in_(filtered_results, expected_results):
    try:
        if len(filtered_results) < expected_results:
            return False
        return True
    except ValueError as v_err:
        ml.log_event(v_err)


def _get_timestamp():
    return datetime.datetime.now()


if __name__ == '__main__':
    ml = MinimalLog()
else:
    ml = MinimalLog(__name__)
