from configparser import ConfigParser  # only used to type a return value
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from re import findall
from time import sleep
from user_configuration.WEB_API_CREDENTIALS import HOST, USER, PASS
import qbittorrentapi


class QbitTasker:
    def __init__(self, user_configuration=None, debug=False, delete_log_files=False):
        ml.log_event('initialize {}'.format(self.__class__), event_completed=False, announce=True)
        assert user_configuration is not None, ml.log_event('!! no user configuration !!', announce=True, level=ml.ERROR)
        self.main_loop_count = 0
        self.qbit_client_connected = True if self._client_is_connected() else False
        # TODO i really hate this debug section, it can be done more dynamically?
        if not debug:
            self.config, self.parsers, self.key_ring = \
                self._get_convenience_objects(user_configuration, debug)
        else:
            self.config, self.parsers, self.key_ring, self.search_detail_parser_section = \
                self._get_convenience_objects(user_configuration, debug)
        self._connection_time_start = datetime.now()
        self._reset_search_ids()
        self.active_search_ids, self.active_header = dict(), ''
        ml.log_event('initialize {}'.format(self.__class__), event_completed=True, announce=True)

    def increment_loop_count(self):
        self.main_loop_count += 1

    def initiate_and_monitor_searches(self):
        try:
            # FYI cannot use _get_parser function here because self.active_headers has not been established
            section_headers = self.parsers.search_detail_parser.sections()
            for section_header in section_headers:
                # TODO couldn't active_header be stored in the data structure? it is referenced VERY OFTEN
                self.active_header = section_header
                ml.log_event('monitoring search header {}'.format(self.active_header))
                self._manage_state_updates(self._get_search_state())
            self._config_to_disk()
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def pause_on_event(self, pause_type):
        try:
            timestamp = _get_timestamp()
            user_config_parser_keys = self._get_keyring_for_user_config()
            self.user_config_parser_at_default_section = self._get_user_config_parser_at_default_section()
            if pause_type == user_config_parser_keys.WAIT_MAIN_LOOP:
                delay = int(self.parsers.user_config_parser[user_config_parser_keys.DEFAULT_SECTION_HEADER_TITLE][user_config_parser_keys.WAIT_MAIN_LOOP])
                ml.log_event('{} waiting {} seconds for main loop repeat..'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == user_config_parser_keys.SEARCH_STATUS_CHECK:
                delay = int(self.parsers.user_config_parser[user_config_parser_keys.DEFAULT_SECTION_HEADER_TITLE][user_config_parser_keys.SEARCH_STATUS_CHECK])
                ml.log_event('{} waiting {} seconds for search state check..'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == user_config_parser_keys.ADD_RESULT:
                delay = int(self.parsers.user_config_parser[user_config_parser_keys.DEFAULT_SECTION_HEADER_TITLE][user_config_parser_keys.ADD_RESULT])
                ml.log_event('{} waiting {} seconds for add attempt..'.format(timestamp, delay))
                sleep(delay)
            else:
                delay = int(self.parsers.user_config_parser[user_config_parser_keys.DEFAULT_SECTION_HEADER_TITLE][user_config_parser_keys.USER])
                # TODO miscellaneous is hardcoded, not that it matters, just annoying and causes upkeep
                ml.log_event('{} waiting {} seconds to let user follow log..'.format(timestamp, delay))
                sleep(delay)
            ml.log_event('\n')  # puts one empty line after pauses, for visual affect in the log
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def transfer_files_to_remote(self):
        pass

    def _all_searches_concluded(self) -> bool:
        # TODO would be nice to exit if all jobs exceed set limits, not currently in-use
        try:
            search_detail_keys, concluded = self.key_ring.search_detail_keyring, list()
            # for section in self.config.parsers[SEARCH].sections():  # TODO delete
            for section in self.parsers.search_detail_parser.sections():
                for key in section:
                    if key == search_detail_keys.SEARCH_CONCLUDED:
                        # search_concluded = self.config.parsers[SEARCH][section].getboolean(key)  # TODO delete
                        search_concluded = self.config.parser.parsers.search_detail_parser[section].getboolean(key)
                        concluded.append(search_concluded)
            if all(concluded):
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _check_if_search_is_concluded(self):
        try:
            search_detail_keys = self._get_keyring_for_search_details()
            if self._search_has_yielded_the_required_results():
                ml.log_event('search {} has concluded, disabling'.format(self.active_header), announce=True)
                # self._update_search_states(CONCLUDED)  # TODO delete
                self._update_search_states(search_detail_keys.CONCLUDED)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _client_is_connected(self) -> bool:
        """
        connect to the client, fetch check app version and web api version
        :return: bool, true if able to populate all data successfully
        """
        ml.log_event('connect to client', event_completed=False)
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                ml.log_event('connect to client with.. \nclient app version {} \nweb api version {}'.format(
                    app_version, web_api_version), event_completed=True)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _log_file_is_too_large(self):
        # TODO yep it's growing
        pass

    def _manage_log_files(self):
        # TODO .. someday .. when it seems interesting
        try:
            if self._log_file_is_too_large():
                # idk delete it or something
                pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _parsers_get_filename_regex(self) -> str:
        try:
            search_detail_keys = self.key_ring.search_detail_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            filename_regex = search_detail_parser_at_active_header[search_detail_keys.FILENAME_REGEX]
            # if search_key.pattern not in self.search_parser[self.active_header].keys():  # TODO delete
            # if FILENAME_REGEX not in self.config.parsers[self.active_header].keys():  # TODO delete
            search_detailkey_value = search_detail_parser_at_active_header.keys()
            if filename_regex not in search_detail_parser_at_active_header.keys():
                filename_regex = '.*'
                return filename_regex
            # filename_regex = self.config.parsers[SEARCH][self.active_header][FILENAME_REGEX]  # TODO delete
            filename_regex = self.config.parser.parsers.search_detail_parser[self.active_header][filename_regex]
            return filename_regex
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _parsers_get_search_term(self) -> str:
        ml.log_event('get search term for {}'.format(self.active_header))
        search_detail_keys = self._get_keyring_for_search_details()
        search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
        try:
            # search_term = search_detail_parser_at_active_header[search_detail_keys.SEARCH_TERM]
            search_term = self.config.parser.parsers.search_detail_parser[search_detail_keys.DEFAULT][search_detail_keys.SEARCH_TERM]
            if search_term not in self.config.parser.parsers.search_detail_parser[self.active_header].keys():
                # TODO this print indicates no search term was provided, could fill in the active section header
                # TODO with the default value just to suppress this from occurring except when a new term is added
                ml.log_event('key {} not found in header {}, setting key value to default header value'.format(
                    search_term, self.active_header), level=ml.WARNING)
                search_term = self.active_header
                self._write_active_header_keys_to_search_detail_parser()
                return search_term
            search_term = self.config.parser.config.parser.parsers.search_detail_parser[self.active_header][search_term]
            return search_term
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _check_if_section_header_metadata_exists_as_local_result(self) -> bool:
        ml.log_event('TODO : ..just return hardcoded False..', level=ml.WARNING)
        return False  # TODO

    def _config_set_search_id_as_active(self):
        # search_id = self.active_search_ids.get(self.active_header, '')
        # TODO NOW this line below is throwing the current exception
        search_id = self.active_search_ids[self.active_header]
        # TODO NOW this line above is throwing the current exception
        search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
        ml.log_event('search id {} set as active'.format(search_id))
        try:
            s_keys = self._get_keyring_for_search_details()
            # self.config.parsers[self.active_header][SEARCH_ID] = search_id
            search_detail_parser_at_active_header[s_keys.SEARCH_ID] = search_id
            self.active_search_ids[self.active_header] = search_id
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _config_set_search_id_as_inactive(self):
        try:
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_id = self.config.hardcoded.keys.search_detail_keyring.SEARCH_ID
            if self._search_id_active():
                # self.config.parser.parsers.parsers_keyed_by_file_path.search_parser[self.active_header][search_id] = str(0) # TODO delete
                search_detail_parser_at_active_header[search_id] = str(0)
                ml.log_event('search id {} set as inactive'.format(search_id))
                del self.active_search_ids[self.active_header]
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            # config_file_paths = [self.config.paths.data, self.config.paths.user_config]  # TODO delete
            parsers_dict = self.parsers.parsers_keyed_by_file_path
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
                    ml.log_event('successfully written parser {} to disk at {}'.format(parser, parser_path))
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _filter_results(self):
        try:
            md_keys = self.key_ring.metadata_keyring
            filtered_result_count, filtered_results, results = 0, list(), self._qbit_get_search_results()
            if results is None:
                return None, 0
            # for result in results(META_RESULTS): # TODO delete
            ml.log_event('get filename regex pattern for active header {}'.format(self.active_header))
            for result in results(md_keys.RESULT):
                # filename = result[META_NAME]  # TODO delete
                filename = result[md_keys.NAME]
                search_pattern = self._parsers_get_filename_regex()
                if self._pattern_matches(search_pattern, filename):
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
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_search_detail_parser_at_active_header(self) -> ConfigParser:
        try:
            search_detail_parser = self.config.parser.parsers.search_detail_parser[self.active_header]
            return search_detail_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def _get_convenience_objects(user_configuration, debug=False) -> tuple:
        # TODO deprecated once all getters in-place
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

    def _get_user_config_parser_at_default_section(self) -> ConfigParser:
        try:
            user_config_parser_keys = self._get_keyring_for_user_config()
            ucpk = user_config_parser_keys
            user_config_parser_at_default_section = \
               self.config.parser.parsers.user_config_parser[ucpk.DEFAULT_SECTION_HEADER_TITLE]
            return user_config_parser_at_default_section
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_most_popular_results(self, filtered_results) -> list:
        # search_detail_keys, user_config_parser_keys = self.key_ring.search_detail_keyring, self.key_ring.user_config_keyring  # TODO delete
        search_detail_keys, user_config_parser_keys = self._get_keyring_for_search_details(), self._get_keyring_for_user_config()
        # expected_search_result_count = self.config.parsers[SEARCH][EXPECTED_RESULT_COUNT]
        expected_search_result_count = self.config.parser.parsers.search_detail_parser[self.active_header][search_detail_keys.RESULT_COUNT]
        ml.log_event('get most popular results from {} up to count {}'.format(
            filtered_results, expected_search_result_count), event_completed=False)
        found_result_count = len(filtered_results)
        if not _enough_results_in_(filtered_results, expected_search_result_count):
            expected_search_result_count = found_result_count
        try:
            # user_config_parser = self._get_user_config_parser()
            search_detail_keys, user_config_parser_keys = self._get_keyring_for_search_details(), self._get_keyring_for_user_config()
            user_config_parser_default_section = self.config.parser.parsers.user_config_parser[user_config_parser_keys.DEFAULT_SECTION_HEADER_TITLE]
            # popularity_sorted_list = sorted(filtered_results, key=lambda k: k[PRIORITY], reverse=True)  # TODO delete
            # TODO BUG this line breaks the program due to int/str type issues
            _result_property_priority = user_config_parser_keys.PRIORITY
            _priority = user_config_parser_default_section[_result_property_priority]
            # TODO bug solution = arg needs to be equal to 'nbSeeders'
            arg = 'nbSeeders'  # TODO delete me
            popularity_sorted_list = sorted(filtered_results, key=lambda k: k[arg], reverse=True)
            most_popular_results = list()
            for index in range(expected_search_result_count):
                # TODO should do some debug here to and see if indexes are working as expected
                most_popular_results.append(popularity_sorted_list[index])
            return most_popular_results
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_priority_key_for_search_result_sorting(self):
        try:
            user_config_parser_keys = self.key_ring.user_config_keyring
            return self.config.parser.parsers.user_config_parser[user_config_parser_keys.DEFAULT_SECTION_HEADER_TITLE][user_config_parser_keys.PRIORITY]
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_keyring_for_metadata_details(self):
        try:
            metadata_keyring = self.config.hardcoded.keys.metadata_detailkeyring
            return metadata_keyring
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_keyring_for_search_details(self):
        try:
            search_detailkeyring = self.config.hardcoded.keys.search_detail_keyring
            return search_detailkeyring
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_keyring_for_user_config(self):
        try:
            user_config_keyring = self.config.hardcoded.keys.user_config_keyring
            return user_config_keyring
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_metadata_parser_at_result_name_section(self, section_header):
        try:
            metadata_parser = self.config.parser.parsers.metadata_parser
            metadata_parser_at_section_header = metadata_parser[section_header]
            if metadata_parser.has_section(section_header):
                ml.log_event('warning, section_header {} already exists, overwriting the existing entry '.format(section_header))
                already_added = self._check_if_section_header_metadata_exists_as_local_result(metadata_parser_at_section_header)
                if already_added:
                    ml.log_event('metadata result for section header {} already exists in local results'.format(section_header))
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_search_state(self) -> tuple:
        """
        :return: search states
        """
        ml.log_event('get search state for {}'.format(self.active_header))
        try:
            search_detail_keys = self._get_keyring_for_search_details()
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_detail_parser_at_active_header[search_detail_keys.LAST_READ] = str(datetime.now())
            _search_queued = search_detail_parser_at_active_header.getboolean(search_detail_keys.QUEUED)
            _search_running = search_detail_parser_at_active_header.getboolean(search_detail_keys.RUNNING)
            _search_stopped = search_detail_parser_at_active_header.getboolean(search_detail_keys.STOPPED)
            _search_concluded = search_detail_parser_at_active_header.getboolean(search_detail_keys.CONCLUDED)
            ml.log_event('search state for {}: \nqueued: {}\nrunning: {}\nstopped: {}\nconcluded: {}'.format(
                self.active_header, _search_queued, _search_running, _search_stopped, _search_concluded))
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_user_config_parser(self):
        try:
            user_config_parser = self.config.parser.parsers.user_config_parser
            return user_config_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _hash(self, x, un=False):
        try:
            _pol = -1 if un else 1
            _uk = self._get_keyring_for_user_config()
            # TODO the bug is in this expression
            # _hash = ''.join([chr(ord(e) + int(self.parsers.user_config_parser.get(u_keys.UNI_SHIFT))) * _pol for e in str(x) if x])
            _hash = ''.join([chr(ord(e) + int(self.config.parser.parsers.user_config_parser[_uk.DEFAULT_SECTION_HEADER_TITLE][_uk.UNI_SHIFT])) * _pol for e in str(x) if x])
            ml.log_event('hashed from {} to {}'.format(x, _hash))
            return _hash
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _increment_search_attempt_count(self):
        try:
            search_detail_keys = self.key_ring.search_detail_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            # search_attempt_count = int(self.parsers[self.active_header][s_keys.SEARCH_ATTEMPT_COUNT])
            search_attempt_count = int(search_detail_parser_at_active_header[search_detail_keys.SEARCH_ATTEMPT_COUNT])
            ml.log_event('search try counter at {}, incrementing..'.format(search_attempt_count))
            search_detail_parser_at_active_header[search_detail_keys.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
            # self.config.parser.parsers.search_detail_parser[self.active_header][s_keys.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)  # TODO delete
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _manage_state_updates(self, section_states):
        try:
            ml.log_event('manage state updates..')
            # as_keys, user_config_parser_keys = self.key_ring.api_state_keyring, self.key_ring.user_config_keyring
            search_detail_keys, user_config_parser_keys = self.key_ring.search_detail_keyring, self.key_ring.user_config_keyring
            _search_queue_full = self._search_queue_full()
            _search_queued, _search_running, _search_stopped, _search_concluded = section_states
            if _search_queued and not _search_queue_full:
                self._start_search()  # search is in queue and queue has room, attempt to start this search
            elif _search_running:
                _search_status = self._qbit_get_search_status()
                if search_detail_keys.RUNNING in _search_status:
                    pass  # search is ongoing, do nothing
                elif search_detail_keys.STOPPED in _search_status:
                    self._update_search_states(search_detail_keys.STOPPED)  # mark search as stopped (finished)
                else:
                    self._update_search_states(search_detail_keys.QUEUED)  # search status unexpected, re-queue this search
            elif _search_stopped:
                filtered_results, filtered_results_count = self._filter_results()
                if filtered_results is not None and filtered_results_count > 0:
                    # TODO results_key.supply could be sort by any key, how to get that value here?
                    search_priority = self._get_priority_key_for_search_result_sorting()
                    self._save_remote_metadata_to_local_results_sorting_by_(
                        search_priority, filtered_results)  # search is finished, attempt to add results
                else:
                    self._update_search_states(search_detail_keys.QUEUED)  # search stopped, no results found, re-queue
            elif _search_concluded:
                pass
            else:
                self._update_search_states(search_detail_keys.QUEUED)
            self.pause_on_event(user_config_parser_keys.SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def _pattern_matches(search_pattern, filename) -> bool:
        try:
            pattern_match = findall(search_pattern, filename)
            if pattern_match:
                ml.log_event('matched pattern {} to {}'.format(search_pattern, filename))
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _qbit_add_result(self, result):
        try:
            search_detail_keys, user_config_parser_keys = \
                self.key_ring.search_detail_keyring, self.key_ring.user_config_keyring
            count_before = self._qbit_count_all_torrents()
            ml.log_event('local machine has {} stored results before add attempt..'.format(count_before), announce=True)
            # TODO why does this api call sometimes not add? bad result? not long enough wait?
            self.qbit_client.torrents_add(urls=result['fileUrl'], is_paused=True)
            self.pause_on_event(user_config_parser_keys.ADD_RESULT)
            results_added = self._qbit_count_all_torrents() - count_before
            if results_added > 0:
                ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                self._metadata_parser_write_to_metadata_config_file(result)
                ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                # self.config.parsers[self.active_header][RESULTS_ADDED] = str(int(  # TODO delete
                #     self.config.parsers[self.active_header][RESULTS_ADDED]) + results_added)  # TODO delete
                self.config.parser.parsers.search_detail_parser[self.active_header][search_detail_keys.RESULT_ADDED_COUNT] = str(int(
                    self.config.parser.parsers.search_detail_parser[self.active_header][search_detail_keys.RESULT_ADDED_COUNT]
                ))
                return
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _qbit_count_all_torrents(self) -> int:
        try:
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            return local_result_count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _qbit_create_search_job(self, pattern, plugins, category) -> tuple:
        try:
            _job = self.qbit_client.search.start(pattern, plugins, category)
            _status = _job.status()
            _state = _status.data[0]['status']
            _id = str(_status.data[0]['id'])
            _count = _status.data[0]['total']
            ml.log_event('qbit client created search job for {}'.format(pattern))
            return _job, _status, _state, _id, _count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _qbit_get_search_results(self):
        try:
            search_id = self._get_active_search_ids()
            search_id_valid = self._active_header_search_id_is_valid()
            if search_id_valid:
                results = self.qbit_client.search_results(search_id)
                ml.log_event('qbit client get search results', event_completed=True)
                return results
            return None
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _qbit_get_search_status(self) -> str:
        """
        :return: the status of the search at search_id
        """
        try:
            ml.log_event('checking search status for section: {}'.format(self.active_header))
            search_detail_keys = self.key_ring.search_detail_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            # TODO delete
            # search_id, search_status = self.config.parser.parsers.search_detail_parser[self.active_header][search_detail_keys.SEARCH_ID], None
            search_id, search_status = search_detail_parser_at_active_header[search_detail_keys.SEARCH_ID], None
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
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _reset_search_ids(self):
        """
        upon initialization of new object, delete expired search_ids
        :return: None  # TODO should i return success?
        """
        ml.log_event('reset search ids',event_completed=False)
        try:
            search_detail_keys, user_config_parser_keys = self._get_keyring_for_search_details(), self._get_keyring_for_user_config()
            search_detail_parser = self.config.parser.parsers.search_detail_parser
            for section_header in search_detail_parser.sections():
                self.active_header = section_header
                ml.log_event('reset search_id for section: {}'.format(self.active_header))
                self._update_search_states(search_detail_keys.QUEUED)
                self.pause_on_event(user_config_parser_keys.USER)
                ml.log_event('reset search ids', event_completed=True)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _result_has_enough_seeds(self, result) -> bool:
        try:
            md_keys, search_detail_keys = self.key_ring.metadata_keyring, self.key_ring.search_detail_keyring
            # minimum_seeds = int(self.search_parser[self.active_header][search_key.minimum_seeds])  # TODO delete
            minimum_seeds = int(self.config.parser.parsers.search_detail_parser[self.active_header][search_detail_keys.MIN_SEED_COUNT])
            # result_seeds = result[results_key.supply]
            result_seeds = result[md_keys.SUPPLY]
            if result_seeds > minimum_seeds:
                ml.log_event('result {} has {} seeds, attempting to add'.format(result['fileName'], result_seeds))
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _metadata_parser_write_to_metadata_config_file(self, result):
        ml.log_event('store result {} in metadata parser'.format(result))
        try:
            md_keys, uc_key = self.key_ring.metadata_keyring, self.key_ring.user_config_keyring
            metadata_parser_at_result_name_section = self._get_metadata_parser_at_result_name_section
            # if not self.result_parser.has_section(self._hash(result['fileName'])):  # TODO delete
            if not self.parsers.metadata_parser.has_section(self._hash(result[md_keys.NAME])):
                # self.result_parser.add_section(self._hash(result['fileName']))  # TODO delete
                self.parsers.metadata_parser.add_section(self._hash(result(md_keys.NAME)))
                header = self._hash(result['fileName'])
                for attribute, detail in result.items():
                    # TODO there are some redundant log commands 'above' and 'below' this entry
                    # TODO i think this entry is causing the redundant log commands with _hash() calls
                    h_attr, d_attr = self._hash(attribute), self._hash(detail)
                    ml.log_event('add to results ledger, attribute {} detail {}'.format(h_attr, d_attr))
                    # self.result_parser[header][h_attr] = d_attr  # TODO delete
                    self.parsers.metadata_parser[header][h_attr] = d_attr
                    self.pause_on_event(uc_key.OTHER)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

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
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _save_remote_metadata_to_local_results_sorting_by_(self, attribute, filtered_results) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        try:
            search_detail_keys = self.key_ring.search_detail_keyring
            ml.log_event('add results by {}'.format(attribute), event_completed=False)
            # TODO implement attribute here, 'rKey.nbSeeders' instead of 'popularity
            most_popular_results = self._get_most_popular_results(filtered_results)
            search_id_valid = self._active_header_search_id_is_valid()
            if not search_id_valid:
                ml.log_event('search id for {} is invalid'.format(self.active_header))
                self._update_search_states(search_detail_keys.QUEUED)  # wanted to add result but id bad, re-queue search
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
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_detail_keys = self.key_ring.search_detail_keyring
            # search_id = self.search_parser[self.active_header][search_key.id]
            # search_id = self.parsers[self.active_header][search_detail_keys.SEARCH_ID]
            search_id = search_detail_parser_at_active_header[search_detail_keys.SEARCH_ID]
            if search_id == self.active_search_ids[self.active_header]:
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _active_header_search_id_is_valid(self) -> bool:
        search_id = self.active_search_ids.get(self.active_header, '')
        ml.log_event('check if search id {} is valid'.format(search_id))
        search_detail_keys = self.key_ring.search_detail_keyring
        try:
            if search_id is not None:
                if search_id != search_detail_keys.EMPTY:
                    return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

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
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_has_yielded_the_required_results(self) -> bool:
        """
        decides if search is ready to be marked as completed (ADDED)
        :return: bool, search completed
        """
        ml.log_event('check if search can be concluded', event_completed=False)
        try:
            search_detail_keys = self.key_ring.search_detail_keyring
            # search_detail_parser = self.parsers.search_detail_parser  # TODO bug delete
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            attempted_searches = \
                int(search_detail_parser_at_active_header[self.active_header][search_detail_keys.SEARCH_ATTEMPT_COUNT])
            max_search_attempt_count = \
                int(search_detail_parser_at_active_header[self.active_header][search_detail_keys.MAX_SEARCH_ATTEMPT_COUNT])
            results_added = \
                int(search_detail_parser_at_active_header[self.active_header][search_detail_keys.RESULT_ADDED_COUNT])
            results_required = \
                int(search_detail_parser_at_active_header[self.active_header][search_detail_keys.RESULT_REQUIRED_COUNT])
            if results_added > results_required:
                ml.log_event('search {} can be concluded, '
                             'requested result count has been added'.format(self.active_header),
                             event_completed=True)
                # self._search_set_end_reason(REQUIRED_RESULTS_FOUND)  # TODO delete
                self._search_set_end_reason(search_detail_keys.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
                return True
            elif attempted_searches > max_search_attempt_count:
                ml.log_event('search can be concluded, '
                             'too many search attempts w/o meeting requested result count'.format(self.active_header),
                             event_completed=True)
                # self._search_set_end_reason(TIMED_OUT)  # too many search attempts without required results, conclude  # TODO delete
                self._search_set_end_reason(search_detail_keys.TIMED_OUT)  # too many search attempts, conclude
                return True
            ml.log_event('search {} will be allowed to continue'.format(self.active_header), event_completed=True)
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_set_end_reason(self, reason):
        try:
            search_detail_keys = self.key_ring.search_detail_keyring
            ml.log_event('setting end reason \'{}\' for search header {}'.format(reason, self.active_header))
            # self.search_parser[self.active_header][search_key.end_reason] = reason  # TODO delete
            self.config.parser.parsers.search_detail_parser[self.active_header][search_detail_keys.SEARCH_STOPPED_REASON] = reason
            # search_key.end_reason = reason  # TODO delete after you remember what this did
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _start_search(self):
        try:
            search_detail_keys, search_term = self._get_keyring_for_search_details(), self._parsers_get_search_term()
            search_job, search_status, search_state, search_id, search_count = \
                self._qbit_create_search_job(search_term, 'all', 'all')
            if search_id is not None:
                if search_id is not search_detail_keys.EMPTY:
                    # TODO potential bug fix? seems to fix bug, delete this line whenever
                    self.active_search_ids[self.active_header] = search_id
            if search_detail_keys.RUNNING in search_state:  # search started successfully
                ml.log_event('search started for {}'.format(self.active_header), event_completed=True)
                # TODO this function IS the error, search_ids are never added which is causing problems
                self._config_set_search_id_as_active()
                self._update_search_states(search_detail_keys.RUNNING)
            elif search_detail_keys.STOPPED in search_status:
                ml.log_event('search not successfully started for {}'.format(
                    self.active_header), announce=True, level=ml.WARNING)
            else:
                ml.log_event('search_state is not {} or {}, there was a problem starting the search!'.format(
                    search_detail_keys.RUNNING, search_detail_keys.STOPPED), level=ml.ERROR)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _update_search_states(self, api_state_key):
        ml.log_event('updating the search state machine..')
        try:
            search_detail_keys = self._get_keyring_for_search_details()
            search_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            if api_state_key == search_detail_keys.QUEUED:
                search_parser_at_active_header[search_detail_keys.QUEUED] = search_detail_keys.YES
                search_parser_at_active_header[search_detail_keys.RUNNING] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.STOPPED] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.CONCLUDED] = search_detail_keys.NO
                self.config.parser.parsers.search_detail_parser.remove_section(search_detail_keys.SEARCH_ID)
            elif api_state_key == search_detail_keys.RUNNING:
                search_parser_at_active_header[search_detail_keys.QUEUED] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.RUNNING] = search_detail_keys.YES
                search_parser_at_active_header[search_detail_keys.STOPPED] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.CONCLUDED] = search_detail_keys.NO
                self._increment_search_attempt_count()
            elif api_state_key == search_detail_keys.STOPPED:
                search_parser_at_active_header[search_detail_keys.QUEUED] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.RUNNING] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.STOPPED] = search_detail_keys.YES
                search_parser_at_active_header[search_detail_keys.CONCLUDED] = search_detail_keys.NO
            elif api_state_key == search_detail_keys.CONCLUDED:
                search_parser_at_active_header[search_detail_keys.QUEUED] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.RUNNING] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.STOPPED] = search_detail_keys.NO
                search_parser_at_active_header[search_detail_keys.CONCLUDED] = search_detail_keys.YES
            else:
                pass
            # self.config.parser.config.parser.parsers.search_detail_parser[active_header][sd_key.LAST_WRITE] = str(datetime.now())
            dt_now = str(datetime.now())
            search_parser_at_active_header[search_detail_keys.LAST_WRITE] = dt_now  # TODO what???
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _write_active_header_keys_to_search_detail_parser(self):
        # TODO, is
        try:
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_detail_keys = self._get_keyring_for_search_details()
            for key in search_detail_keys:
                search_detail_parser_at_active_header[key] = ''
                pass
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


def _enough_results_in_(filtered_results, expected_result_count):
    try:
        filtered_results_count = len(filtered_results)
        if filtered_results_count < expected_result_count:
            return False
        return True
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def _get_timestamp():
    return datetime.now()


if __name__ == '__main__':
    ml = MinimalLog()
    ml.log_event('this should not be run directly, user main loop')
else:
    ml = MinimalLog(__name__)
