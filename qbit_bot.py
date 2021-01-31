from datetime import datetime
from minimalog.minimal_log import MinimalLog
from re import findall
from time import sleep
from user_configuration.WEB_API_CREDENTIALS import HOST, USER, PASS
import qbittorrentapi


class QbitTasker:
    def __init__(self, user_configuration=None, debug=False):
        ml.log_event('initialize {}'.format(self.__class__), event_completed=False, announce=True)
        assert user_configuration is not None, ml.log_event('no user configuration', announce=True, level=ml.ERROR)
        self.main_loop_count = 0
        self.qbit_client_connected = True if self._client_is_connected() else False
        # TODO i really hate this debug section, it can be done more dynamically?
        if not debug:
            self.config, self.parsers, self.key_ring = \
                self._get_convenience_objects(user_configuration, debug)
        else:
            self.config, self.parsers, self.key_ring, self.search_details_parser_sections = \
                self._get_convenience_objects(user_configuration, debug)
        self._connection_time_start = datetime.now()
        self._reset_search_ids()
        self.active_search_ids, self.active_header = dict(), ''
        ml.log_event('initialize {}'.format(self.__class__), event_completed=True, announce=True)

    def increment_loop_count(self):
        self.main_loop_count += 1

    def initiate_and_monitor_searches(self):
        try:
            # search_term = self.config.hardcoded.keys.search_detail_keys.SEARCH_TERM  # TODO delete me?
            section_headers = self.config.parser.parsers.search_detail_parser.sections()
            for section_header in section_headers:
                # TODO couldn't active_header be stored in the data structure? it is referenced VERY OFTEN
                self.active_header = section_header
                ml.log_event('monitoring search header {}'.format(self.active_header))
                self._manage_state_updates(self._get_search_state())
            self._config_to_disk()
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def pause_on_event(self, pause_type):
        try:
            timestamp = _get_timestamp()
            p_keys, uc_keys = self.key_ring.parser_keyring, self.key_ring.user_config_keyring
            if pause_type == uc_keys.MAIN_LOOP:
                delay = int(self.parsers.user_config_parser[p_keys.DEFAULT][uc_keys.MAIN_LOOP])
                ml.log_event('{} waiting {} seconds for loop..\n\n'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == uc_keys.SEARCH_STATUS_CHECK:
                delay = int(self.parsers.user_config_parser[p_keys.DEFAULT][uc_keys.SEARCH_STATUS_CHECK])
                ml.log_event('{} waiting {} seconds for search..\n\n'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == uc_keys.ADD_RESULT:
                delay = int(self.parsers.user_config_parser[p_keys.DEFAULT][uc_keys.ADD_RESULT])
                ml.log_event('{} waiting {} seconds for add..\n\n'.format(timestamp, delay))
                sleep(delay)
            else:
                delay = int(self.parsers.user_config_parser[p_keys.DEFAULT][uc_keys.OTHER])
                ml.log_event('{} waiting {} seconds for other..\n\n'.format(timestamp, delay))
                sleep(delay)
        except ValueError as v_err:
            ml.log_event(v_err, level=ml.ERROR)

    def transfer_files_to_remote(self):
        pass

    def _all_searches_concluded(self) -> bool:
        # TODO would be nice to exit if all jobs exceed set limits, not currently in-use
        try:
            t_keys, concluded = self.key_ring.search_state_keyring, list()
            # for section in self.config.parsers[SEARCH].sections():  # TODO delete
            for section in self.parsers.search_detail_parser.sections():
                for key in section:
                    if key == t_keys.SEARCH_CONCLUDED:
                        # search_concluded = self.config.parsers[SEARCH][section].getboolean(key)  # TODO delete
                        search_concluded = self.parsers.search_detail_parser[section].getboolean(key)
                        concluded.append(search_concluded)
            if all(concluded):
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _check_if_search_is_concluded(self):
        try:
            t_keys = self.key_ring.search_state_keyring
            if self._search_has_yielded_the_required_results():
                ml.log_event('search {} has concluded, disabling'.format(self.active_header), announce=True)
                # self._update_search_states(CONCLUDED)  # TODO delete
                self._update_search_states(t_keys.SEARCH_CONCLUDED)
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

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
            ml.log_event(r_err, level=ml.ERROR)

    def _parsers_get_file_name_regex(self) -> str:
        ml.log_event('get search pattern for {}'.format(self.active_header))
        try:
            s_keys = self.key_ring.search_detail_keyring
            file_name_regex = self.parsers.search_detail_parser[self.active_header][s_keys.FILE_NAME_REGEX]
            # if search_key.pattern not in self.search_parser[self.active_header].keys():  # TODO delete
            # if FILENAME_REGEX not in self.config.parsers[self.active_header].keys():  # TODO delete
            if file_name_regex not in self.config.parsers[self.active_header].keys():
                file_name_regex = '.*'
                return file_name_regex
            # file_name_regex = self.config.parsers[SEARCH][self.active_header][FILENAME_REGEX]  # TODO delete
            file_name_regex = self.parsers.search_detail_parser[self.active_header][file_name_regex]
            return file_name_regex
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _parsers_get_search_term(self) -> str:
        ml.log_event('get search term for {}'.format(self.active_header))
        try:
            search_term = self.config.hardcoded.keys.search_detail_keyring.SEARCH_TERM
            if search_term not in self.config.parser.parsers.search_detail_parser[self.active_header].keys():
                ml.log_event('key {} not found in header {}, setting key value to header value'.format(
                    search_term, self.active_header), level=ml.WARNING)
                search_term = self.active_header
                return search_term
            search_term = self.config.parser.parsers.search_detail_parser[self.active_header][search_term]
            return search_term
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _config_set_search_id_as_active(self):
        search_id = self.active_search_ids.get(self.active_header, '')
        ml.log_event('search id {} set as active'.format(search_id))
        try:
            s_keys = self.key_ring.search_detail_keyring
            # self.config.parsers[self.active_header][SEARCH_ID] = search_id
            self.parsers.search_detail_parser[self.active_header][s_keys.SEARCH_ID] = search_id
            self.active_search_ids[self.active_header] = search_id
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _config_set_search_id_as_inactive(self):
        try:
            search_id = self.config.hardcoded.keys.search_detail_keyring.SEARCH_ID
            if self._search_id_active():
                self.config.parser.parsers_keyed_by_file_path.search_parser[self.active_header][search_id] = str(0)
                ml.log_event('search id {} set as inactive'.format(search_id))
                del self.active_search_ids[self.active_header]
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            # config_file_paths = [self.config.paths.data, self.config.paths.user_config]  # TODO delete
            parsers_dict = self.parsers.parsers_keyed_by_file_path
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
        except OSError as o_err:
            ml.log_event(o_err, level=ml.ERROR)

    def _filter_results(self):
        try:
            m_keys = self.key_ring.metadata_keyring
            filtered_result_count, filtered_results, results = 0, list(), self._qbit_get_search_results()
            if results is None:
                return None, 0
            # for result in results(META_RESULTS): # TODO delete
            for result in results(m_keys.RESULT):
                # file_name = result[META_NAME]  # TODO delete
                file_name = result[m_keys.NAME]
                search_pattern = self._parsers_get_file_name_regex()
                if self._pattern_matches(search_pattern, file_name):
                    filtered_results.append(result)
                    filtered_result_count += 1
            ml.log_event('{} filtered results found'.format(filtered_result_count))
            return filtered_results, filtered_result_count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_active_search_ids(self) -> str:
        try:
            active_search_id = self.active_search_ids.get(self.active_header)
            ml.log_event('get active search id {} for {}'.format(active_search_id, self.active_header))
            return active_search_id
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    @staticmethod
    def _get_convenience_objects(user_configuration, debug=False) -> tuple:
        # TODO if this is used too often, consider changing the data structure
        try:
            convenience_objects = [
                user_configuration,
                user_configuration.parser.parsers,
                user_configuration.hardcoded.keys
            ]
            if debug:  # allow easy access to section_headers keys in search_detail_parser
                convenience_objects.append(user_configuration.parser.parsers.search_detail_parser._sections)
            return * convenience_objects,
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_most_popular_results(self, filtered_results) -> list:
        s_keys, uc_keys = self.key_ring.search_detail_keyring, self.key_ring.user_config_keyring
        # expected_search_result_count = self.config.parsers[SEARCH][EXPECTED_RESULT_COUNT]
        expected_search_result_count = self.parsers.search_detail_parser[self.active_header][s_keys.RESULT_COUNT]
        ml.log_event('get most popular results from {} up to count {}'.format(
            filtered_results, expected_search_result_count), event_completed=False)
        found_result_count = len(filtered_results)
        if not _enough_results_in_(filtered_results, expected_search_result_count):
            expected_search_result_count = found_result_count
        try:
            # popularity_sorted_list = sorted(filtered_results, key=lambda k: k[PRIORITY], reverse=True)  # TODO delete
            popularity_sorted_list = sorted(filtered_results, key=lambda k: k[uc_keys.PRIORITY], reverse=True)
            most_popular_results = list()
            for index in range(expected_search_result_count):
                # TODO should do some debug here to and see if indexes are working as expected
                most_popular_results.append(popularity_sorted_list[index])
            return most_popular_results
        except IndexError as i_err:
            ml.log_event(i_err, level=ml.ERROR)

    def _get_priority_key_for_search_result_sorting(self):
        try:
            p_keys, uc_keys = self.key_ring.parser_keyring, self.key_ring.user_config_keyring
            # return self.config.parsers[USER_CONFIG][PRIORITY]  # TODO delete
            return self.config.parsers.user_config_parser[p_keys.DEFAULT][uc_keys.PRIORITY]
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _get_search_state(self) -> tuple:
        """
        :return: search states
        """
        ml.log_event('get search state for {}'.format(self.active_header))
        try:
            s_keys, t_keys = self.key_ring.search_detail_keyring, self.key_ring.search_state_keyring
            self.parsers.search_detail_parser[self.active_header][s_keys.LAST_READ] = str(datetime.now())
            _search_queued = self.parsers.search_detail_parser[self.active_header].getboolean(t_keys.SEARCH_QUEUED)
            _search_running = self.parsers.search_detail_parser[self.active_header].getboolean(t_keys.SEARCH_RUNNING)
            _search_stopped = self.parsers.search_detail_parser[self.active_header].getboolean(t_keys.SEARCH_STOPPED)
            _search_concluded = self.parsers.search_detail_parser[self.active_header].getboolean(t_keys.SEARCH_CONCLUDED)
            ml.log_event('\n\nsearch state for {}: \nqueued: {}\nrunning: {}\nstopped: {}\nconcluded: {}\n\n'.format(
                self.active_header, _search_queued, _search_running, _search_stopped, _search_concluded))
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _hash(self, x, un=False):
        try:
            _pol, u_keys = -1 if un else 1, self.key_ring.user_config_keyring
            _hash = ''.join([chr(ord(e) + int(self.parsers.user_config_parser.get(
                u_keys.UNI_SHIFT))) * _pol for e in str(x) if x])
            ml.log_event('hashed from {} to {}'.format(x, _hash))
            return _hash
        except ValueError as v_err:
            ml.log_event(v_err, level=ml.ERROR)

    def _increment_search_attempt_count(self):
        try:
            s_keys = self.key_ring.search_detail_keyring
            search_attempt_count = int(self.parsers[self.active_header][s_keys.SEARCH_ATTEMPT_COUNT])
            ml.log_event('search try counter at {}, incrementing..'.format(search_attempt_count))
            self.parsers.search_detail_parser[self.active_header][
                s_keys.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _manage_state_updates(self, section_states):
        try:
            ml.log_event('manage state updates..')
            t_keys, uc_keys = self.key_ring.search_state_keyring, self.key_ring.user_config_keyring
            _search_queued, _search_running, _search_stopped, _search_concluded = section_states
            if _search_queued and not self._search_queue_full():
                self._start_search()  # search is in queue and queue has room, attempt to start this search
            elif _search_running:
                _search_status = self._qbit_get_search_status()
                if t_keys.SEARCH_RUNNING in _search_status:
                    pass  # search is ongoing, do nothing
                elif t_keys.SEARCH_STOPPED in _search_status:
                    self._update_search_states(t_keys.SEARCH_STOPPED)  # mark search as stopped (finished)
                else:
                    self._update_search_states(t_keys.SEARCH_QUEUED)  # search status unexpected, re-queue this search
            elif _search_stopped:
                filtered_results, filtered_results_count = self._filter_results()
                if filtered_results is not None and filtered_results_count > 0:
                    # TODO results_key.supply could be sort by any key, how to get that value here?
                    search_priority = self._get_priority_key_for_search_result_sorting()
                    self._save_remote_metadata_to_local_results_sorting_by_(
                        search_priority, filtered_results)  # search is finished, attempt to add results
                else:
                    self._update_search_states(t_keys.SEARCH_QUEUED)  # search stopped, no results found, re-queue
            elif _search_concluded:
                pass
            else:
                self._update_search_states(t_keys.SEARCH_QUEUED)
            self.pause_on_event(uc_keys.SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

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
            s_keys, uc_keys = self.key_ring.search_detail_keyring, self.key_ring.user_config_keyring
            count_before = self._qbit_count_all_torrents()
            ml.log_event('local machine has {} stored results before add attempt..'.format(count_before), announce=True)
            self.qbit_client.torrents_add(urls=result['fileUrl'], is_paused=True)
            # self.pause_on_event(ADD)  # TODO delete
            self.pause_on_event(uc_keys.ADD_RESULT)
            results_added = self._qbit_count_all_torrents() - count_before
            if results_added > 0:
                ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                self._result_parser_store(result)
                ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                # self.config.parsers[self.active_header][RESULTS_ADDED] = str(int(  # TODO delete
                #     self.config.parsers[self.active_header][RESULTS_ADDED]) + results_added)  # TODO delete
                self.parsers.search_detail_parser[self.active_header][s_keys.RESULT_ADDED_COUNT] = str(int(
                    self.parsers.search_detail_parser[self.active_header][s_keys.RESULT_ADDED_COUNT]
                ))
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
            search_id_valid = self._active_header_search_id_is_valid()
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
            s_keys = self.key_ring.search_detail_keyring
            search_id, search_status = self.parsers.search_detail_parser[self.active_header][s_keys.SEARCH_ID], None
            search_id_valid = self._active_header_search_id_is_valid()
            if search_id_valid:
                # TODO PRIORITY BUG, this section of code is double logging, why?
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
            search_parser = self.config.parser.parsers.search_detail_parser
            queued = self.config.hardcoded.keys.search_state_keyring.SEARCH_QUEUED
            for section_header in search_parser.sections():
                self.active_header = section_header
                ml.log_event('reset search_id for section: {}'.format(self.active_header))
                self._update_search_states(queued)
                ml.log_event('reset search ids', event_completed=True)
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _result_has_enough_seeds(self, result) -> bool:
        try:
            m_key, s_key = self.key_ring.metadata_keyring, self.key_ring.search_detail_keyring
            # minimum_seeds = int(self.search_parser[self.active_header][search_key.minimum_seeds])  # TODO delete
            minimum_seeds = int(self.parsers.search_detail_parser[self.active_header][s_key.MIN_SEED_COUNT])
            # result_seeds = result[results_key.supply]
            result_seeds = result[m_key.SUPPLY]
            if result_seeds > minimum_seeds:
                ml.log_event('result {} has {} seeds, attempting to add'.format(result['fileName'], result_seeds))
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _result_parser_store(self, result):
        ml.log_event('store result {} in result parser'.format(result))
        try:
            m_key, uc_key = self.key_ring.metadata_keyring, self.key_ring.user_config_keyring
            # if not self.result_parser.has_section(self._hash(result['fileName'])):  # TODO delete
            if not self.parsers.metadata_parser.has_section(self._hash(result[m_key.NAME])):
                # self.result_parser.add_section(self._hash(result['fileName']))  # TODO delete
                self.parsers.metadata_parser.add_section(self._hash(result(m_key.NAME)))
                header = self._hash(result['fileName'])
                for attribute, detail in result.items():
                    # TODO there are some redundant log commands 'above' and 'below' this entry
                    # TODO i think this entry is causing the redundant log commands with _hash() calls
                    h_attr, d_attr = self._hash(attribute), self._hash(detail)
                    ml.log_event('add to results ledger, attribute {} detail {}'.format(h_attr, d_attr))
                    # self.result_parser[header][h_attr] = d_attr  # TODO delete
                    self.parsers.metadata_parser[header][h_attr] = d_attr
                    self.pause_on_event(uc_key.OTHER)
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _results_fetch_all_data(self) -> dict:
        ml.log_event('fetching results from disk', event_completed=False)
        try:
            all_data = dict()
            # for section in self.result_parser.sections():  # TODO delete
            for section in self.parsers.metadata_parser.sections():
                all_data[self._hash(section, True)] = dict()
                # for key, detail in self.result_parser[section].items():  # TODO delete
                for key, detail in self.parsers.metadata_parser[section].items():
                    all_data[self._hash(section, True)][key] = self._hash(detail, True)
            ml.log_event('fetching results from disk', event_completed=True)
            return all_data
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _save_remote_metadata_to_local_results_sorting_by_(self, attribute, filtered_results) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        try:
            t_keys = self.key_ring.search_state_keyring
            ml.log_event('add results by {}'.format(attribute), event_completed=False)
            # TODO implement attribute here, 'rKey.nbSeeders' instead of 'popularity
            most_popular_results = self._get_most_popular_results(filtered_results)
            search_id_valid = self._active_header_search_id_is_valid()
            if not search_id_valid:
                ml.log_event('search id for {} is invalid'.format(self.active_header))
                self._update_search_states(t_keys.SEARCH_QUEUED)  # wanted to add result but id bad, re-queue search
                return False
            if most_popular_results is not None:
                self._check_if_search_is_concluded()  # we found some results, have we met our 'concluded' criteria?
                self._config_set_search_id_as_inactive()
                ml.log_event('results sorted by popularity for {}'.format(self.active_header))
                for result in most_popular_results:
                    if self._result_has_enough_seeds(result):
                        self._qbit_add_result(result)
            ml.log_event('add results by popularity', event_completed=True)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_id_active(self) -> bool:
        try:
            s_key = self.key_ring.search_detail_keyring
            # search_id = self.search_parser[self.active_header][search_key.id]
            search_id = self.parsers[self.active_header][s_key.SEARCH_ID]
            if search_id == self.active_search_ids[self.active_header]:
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _active_header_search_id_is_valid(self) -> bool:
        search_id = self.active_search_ids.get(self.active_header, '')
        ml.log_event('check if search id {} is valid'.format(search_id))
        m_keys = self.key_ring.metadata_keyring.misc_keyring
        try:
            if search_id is not None:
                if search_id != m_keys.EMPTY:
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
            ssr_keys = self.key_ring.search_stopped_reason_keys
            s_key, search_detail_parser = self.key_ring.search_detail_keyring, self.parsers.search_detail_parser
            # TODO delete block
            # attempted_searches = int(self.search_parser[self.active_header][search_key.attempts])
            # maximum_allowed_search_attempts = int(self.search_parser[self.active_header][search_key.attempts_max])
            # results_added = int(self.search_parser[self.active_header][search_key.results_added])
            # results_required = int(self.search_parser[self.active_header][search_key.results_required])
            attempted_searches = int(search_detail_parser[self.active_header][s_key.SEARCH_ATTEMPT_COUNT])
            max_search_attempt_count = int(search_detail_parser[self.active_header][s_key.MAX_SEARCH_ATTEMPT_COUNT])
            results_added = int(search_detail_parser[self.active_header][s_key.RESULT_ADDED_COUNT])
            results_required = int(search_detail_parser[self.active_header][s_key.RESULT_REQUIRED_COUNT])
            if results_added > results_required:
                ml.log_event('search {} can be concluded, '
                             'requested result count has been added'.format(self.active_header),
                             event_completed=True)
                # self._search_set_end_reason(REQUIRED_RESULTS_FOUND)  # TODO delete
                self._search_set_end_reason(ssr_keys.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
                return True
            elif attempted_searches > max_search_attempt_count:
                ml.log_event('search can be concluded, '
                             'too many search attempts w/o meeting requested result count'.format(self.active_header),
                             event_completed=True)
                # self._search_set_end_reason(TIMED_OUT)  # too many search attempts without required results, conclude  # TODO delete
                self._search_set_end_reason(ssr_keys.TIMED_OUT)  # too many search attempts, conclude
                return True
            ml.log_event('search {} will be allowed to continue'.format(self.active_header), event_completed=True)
            return False
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)
            
    def _search_set_end_reason(self, reason):
        try:
            s_keys = self.key_ring.search_detail_keyring
            ml.log_event('setting end reason \'{}\' for search header {}'.format(reason, self.active_header))
            # self.search_parser[self.active_header][search_key.end_reason] = reason  # TODO delete
            self.parsers.search_detail_parser[self.active_header][s_keys.SEARCH_STOPPED_REASON] = reason
            # search_key.end_reason = reason  # TODO delete after you remember what this did
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)

    def _start_search(self):
        try:
            t_keys = self.key_ring.search_state_keyring
            search_term = self._parsers_get_search_term()
            search_job, search_status, search_state, search_id, search_count = \
                self._qbit_create_search_job(search_term, 'all', 'all')
            if t_keys.SEARCH_RUNNING in search_state:  # search started successfully
                ml.log_event('search started for {}'.format(self.active_header), event_completed=True)
                self._config_set_search_id_as_active()
                # self._update_search_states(STARTING)  # TODO delete
                self._update_search_states(t_keys.SEARCH_RUNNING)
            elif t_keys.SEARCH_STOPPED in search_status:
                ml.log_event('search not successfully started for {}'.format(
                    self.active_header), announce=True, level=ml.WARNING)
        except KeyError as k_err:
            ml.log_event('{}: unable to process search job'.format(k_err), level=ml.ERROR)

    def _update_search_states(self, job_state):
        ml.log_event('updating the search state machine..')
        try:
            search_parser = self.config.parser.parsers.search_detail_parser
            search_keys = self.config.hardcoded.keys.search_detail_keyring
            active_header = self.active_header
            search_id = self._parsers_get_search_term()
            _queued = self.config.hardcoded.keys.search_state_keyring.SEARCH_QUEUED
            _running = self.config.hardcoded.keys.search_state_keyring.SEARCH_RUNNING
            _stopped = self.config.hardcoded.keys.search_state_keyring.SEARCH_STOPPED
            _concluded = self.config.hardcoded.keys.search_state_keyring.SEARCH_CONCLUDED
            yes, no = self.config.hardcoded.keys.parser_keyring.YES, self.config.hardcoded.keys.parser_keyring.NO
            # TODO bug, section headers is not populating, search_parser loses data somewhere after here
            if job_state == _queued:
                # self.search_parser.remove_section('search_id')  # TODO delete this line after implementing replacement
                self.config.parser.parsers.search_detail_parser.remove_section(search_keys.SEARCH_ID)
                self.config.parser.parsers.search_detail_parser[active_header][_queued] = yes
                self.config.parser.parsers.search_detail_parser[active_header][_running] = no
                self.config.parser.parsers.search_detail_parser[active_header][_stopped] = no
                self.config.parser.parsers.search_detail_parser[active_header][_concluded] = no
            elif job_state == _running:
                self.config.parser.parsers.search_detail_parser[active_header][_queued] = no
                self.config.parser.parsers.search_detail_parser[active_header][_running] = yes
                self.config.parser.parsers.search_detail_parser[active_header][_stopped] = no
                self.config.parser.parsers.search_detail_parser[active_header][_concluded] = no
                self._increment_search_attempt_count()
            elif job_state == _stopped:
                self.config.parser.parsers.search_detail_parser[active_header][_queued] = no
                self.config.parser.parsers.search_detail_parser[active_header][_running] = no
                self.config.parser.parsers.search_detail_parser[active_header][_stopped] = yes
                self.config.parser.parsers.search_detail_parser[active_header][_concluded] = no
            elif job_state == _concluded:
                self.config.parser.parsers.search_detail_parser[active_header][_queued] = no
                self.config.parser.parsers.search_detail_parser[active_header][_running] = no
                self.config.parser.parsers.search_detail_parser[active_header][_stopped] = no
                self.config.parser.parsers.search_detail_parser[active_header][_concluded] = yes
            else:
                pass
            self.config.parser.parsers.search_detail_parser[active_header][search_keys.LAST_WRITE] = str(datetime.now())
        except KeyError as k_err:
            ml.log_event(k_err, level=ml.ERROR)


def _enough_results_in_(filtered_results, expected_result_count):
    try:
        filtered_results_count = len(filtered_results)
        if filtered_results_count < expected_result_count:
            return False
        return True
    except ValueError as v_err:
        ml.log_event(v_err, level=ml.ERROR)


def _get_timestamp():
    return datetime.now()


if __name__ == '__main__':
    ml = MinimalLog()
    ml.log_event('this should not be run directly, user main loop')
else:
    ml = MinimalLog(__name__)
