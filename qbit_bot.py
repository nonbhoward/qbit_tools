from configparser import ConfigParser  # only used to type a return value
from configuration_reader import get_user_configuration
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from re import findall
from time import sleep
from user_configuration.WEB_API_CREDENTIALS import HOST, USER, PASS
# TODO delete 'import inspect' if remains unused, could be useful?
import inspect
import qbittorrentapi


class QbitTasker:
    def __init__(self, manage_log_files=False):
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=False, announce=True)
        self.config = get_user_configuration()
        assert self.config is not None, ml.log_event('!! no user configuration !!', announce=True, level=ml.ERROR)
        self.main_loop_count = 0
        self.qbit_client_connected = True if self._client_is_connected() else False
        self._connection_time_start = datetime.now()
        self._reset_search_ids()
        self.active_search_ids, self.active_header = dict(), ''
        if manage_log_files:
            self._manage_log_files()  # TODO this does nothing
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=True, announce=True)
        self.pause_on_event(self.config.hardcoded.keys.user_config_parser_keyring.WAIT_FOR_USER)

    def increment_loop_count(self):
        self.main_loop_count += 1
        ml.log_event('current connection to qbittorrent api was started at {}'.format(self._connection_time_start))
        ml.log_event('main loop has ended, {} total loops..'.format(self.main_loop_count))
        ml.log_event('when in doubt, compare parsed file keys with config reader string values', level=ml.WARNING)
        ml.log_event('when in doubt, compare parsed file keys with config reader string values', level=ml.WARNING)

    def initiate_and_monitor_searches(self):
        try:
            # FYI cannot use self._get_parser functions here because self.active_headers has not been set
            search_detail_parser_section_headers = self.config.parser.parsers.search_detail_parser.sections()
            user_config_parser = self._get_user_config_parser()
            search_detail_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            user_config_parser_keys = self._get_keyring_for_user_config_parser()
            # perform sorting on search queue
            sort_key = search_detail_parser_keys.TIME_LAST_SEARCHED
            self._set_search_order_ranking_by_(sort_key)
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_USER)
            # TODO reminder, main program loop entry here TODO $
            for search_detail_parser_section_header in search_detail_parser_section_headers:
                self.active_header = search_detail_parser_section_header
                ml.log_event(f'monitoring search header \'{self.active_header}\'')
                self._manage_state_updates(self._get_search_state())
            self._config_to_disk()
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def pause_on_event(self, pause_type):
        try:
            timestamp = _get_timestamp()
            user_config_parser_keys = self._get_keyring_for_user_config_parser()
            user_config_parser = self.config.parser.parsers.user_config_parser
            user_config_parser_at_default = user_config_parser[user_config_parser_keys.DEFAULT]
            if pause_type == user_config_parser_keys.WAIT_FOR_MAIN_LOOP:
                delay = int(user_config_parser_at_default[user_config_parser_keys.WAIT_FOR_MAIN_LOOP])
                ml.log_event('{} waiting {} seconds for main loop repeat..'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == user_config_parser_keys.WAIT_FOR_SEARCH_STATUS_CHECK:
                delay = int(user_config_parser_at_default[user_config_parser_keys.WAIT_FOR_SEARCH_STATUS_CHECK])
                ml.log_event('{} waiting {} seconds for search state check..'.format(timestamp, delay))
                sleep(delay)
            elif pause_type == user_config_parser_keys.WAIT_FOR_SEARCH_RESULT_ADD:
                delay = int(user_config_parser_at_default[user_config_parser_keys.WAIT_FOR_SEARCH_RESULT_ADD])
                ml.log_event('{} waiting {} seconds for add attempt..'.format(timestamp, delay))
                sleep(delay)
            else:
                delay = int(user_config_parser_at_default[user_config_parser_keys.WAIT_FOR_USER])
                # TODO miscellaneous is hardcoded, not that it matters, just annoying and causes upkeep
                ml.log_event('{} waiting {} seconds to let user follow log..'.format(timestamp, delay))
                sleep(delay)
            # ml.log_event('\n')  # puts one empty line after pauses, for visual affect in the log
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def transfer_files_to_remote(self):
        pass

    def _all_searches_concluded(self) -> bool:
        # TODO would be nice to exit if all jobs exceed set limits, not currently in-use
        try:
            search_parser_keys, concluded = self.config.hardcoded.keys.search_parser_keyring, list()
            for section in self.config.parser.parsers.search_detail_parser.sections():
                for key in section:
                    if key == search_parser_keys.SEARCH_CONCLUDED:
                        search_concluded = self.config.parser.parsers.search_detail_parser[section].getboolean(key)
                        concluded.append(search_concluded)
            if all(concluded):
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _check_if_search_is_concluded(self):
        try:
            search_parser_keys = self._get_keyring_for_search_detail_parser()
            if self._search_has_yielded_the_required_results():
                ml.log_event('search \'{}\' has concluded, disabling'.format(self.active_header), announce=True)
                self._update_search_states(search_parser_keys.CONCLUDED)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _check_if_section_header_metadata_exists_as_local_result(self) -> bool:
        delete_me = self.config  # suppress @staticmethod warning
        ml.log_event('TODO : ..just return hardcoded False..', level=ml.WARNING)
        return False  # TODO

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
                # TODO could unpack more details here just for readability
                ml.log_event('connect to client with.. \n\n\tclient app version {} \n\tweb api version {}\n\n'.format(
                    app_version, web_api_version), event_completed=True)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _config_set_search_id_as_active(self):
        search_id = self.active_search_ids[self.active_header]
        search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
        ml.log_event('search id \'{}\' set as active'.format(search_id))
        try:
            s_keys = self._get_keyring_for_search_detail_parser()
            search_detail_parser_at_active_header[s_keys.SEARCH_ID] = search_id
            self.active_search_ids[self.active_header] = search_id
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _config_set_search_id_as_inactive(self):
        try:
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_id = self.config.hardcoded.keys.search_parser_keyring.SEARCH_ID
            if self._search_id_active():
                search_detail_parser_at_active_header[search_id] = str(0)
                ml.log_event('search id \'{}\' set as inactive'.format(search_id))
                del self.active_search_ids[self.active_header]
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            parsers_dict = self.config.parser.parsers.parsers_keyed_by_file_path
            search_detail_parser_keys = self._get_keyring_for_search_detail_parser()
            for parser_path, parser in parsers_dict.items():
                with open(parser_path, 'w') as parser_to_write:
                    parser.write(parser_to_write)
                    ml.log_event('parser update for {}'.format(parser))
                    ml.log_event('successfully written parser to disk at \'{}\''.format(parser_path))
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_active_search_ids(self) -> str:
        try:
            active_search_id = self.active_search_ids.get(self.active_header)
            ml.log_event('get active search id \'{}\' for \'{}\''.format(active_search_id, self.active_header))
            return active_search_id
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_datetimes_from_search_parser(self) -> dict:
        # FIXME unfinished, is this function needed?
        # TODO connect this to search sorting
        try:
            search_detail_parser_keys = self._get_keyring_for_search_detail_parser()
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            datetime_elements = search_detail_parser_at_active_header[search_detail_parser_keys.DATETIME_ELEMENT_LIST]
            search_parser_datetimes = dict()
            for datetime_element in datetime_elements:
                _datetime_from_element = datetime.strptime(date_string=datetime_element)
            return _datetime_from_element
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_keyring_for_metadata_parser(self):
        try:
            metadata_detail_keyring = self.config.hardcoded.keys.metadata_parser_keyring
            return metadata_detail_keyring
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_keyring_for_search_detail_parser(self):
        try:
            search_parser_keyring = self.config.hardcoded.keys.search_parser_keyring
            return search_parser_keyring
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_keyring_for_user_config_parser(self):
        try:
            user_config_keyring = self.config.hardcoded.keys.user_config_parser_keyring
            return user_config_keyring
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_metadata_arg_from_user_config_(self, priority) -> str:
        try:
            # TODO finish all of the translations between metadata args and user config values
            metadata_parser_keys = self._get_keyring_for_metadata_parser()
            if priority == 'seeds':
                return metadata_parser_keys.SUPPLY
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

    def _get_most_popular_results(self, regex_filtered_results: list) -> list:
        search_detail_parser_keys, user_config_parser_keys = \
            self._get_keyring_for_search_detail_parser(), self._get_keyring_for_user_config_parser()
        search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
        expected_search_result_count = \
            int(search_detail_parser_at_active_header[search_detail_parser_keys.EXPECTED_SEARCH_RESULT_COUNT])
        # TODO why is expected_search_result_count == 0?
        ml.log_event('get most popular results up to count {}'.format(
            expected_search_result_count), event_completed=False)
        # TODO BUG happens here : '<' not supported between instances of 'int' and 'str'
        found_result_count = len(regex_filtered_results)
        if not _enough_results_in_(regex_filtered_results, expected_search_result_count):
            expected_search_result_count = found_result_count
        try:
            search_detail_parser_keys, user_config_parser_keys = \
                self._get_keyring_for_search_detail_parser(), self._get_keyring_for_user_config_parser()
            user_config_parser_default_section = \
                self.config.parser.parsers.user_config_parser[user_config_parser_keys.DEFAULT]
            # TODO BUG this line breaks the program due to int/str type issues
            _priority = user_config_parser_default_section[user_config_parser_keys.USER_PRIORITY]
            _sort_arg = self._get_metadata_arg_from_user_config_(_priority)
            popularity_sorted_list = sorted(regex_filtered_results, key=lambda k: k[_sort_arg], reverse=True)
            most_popular_results = list()
            for index in range(expected_search_result_count):
                # TODO should do some debug here to and see if indexes are working as expected
                most_popular_results.append(popularity_sorted_list[index])
            return most_popular_results
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def _get_parser_as_sortable_(parser_to_convert: ConfigParser) -> zip:
        try:
            sdp_dict = dict()
            for section in parser_to_convert.sections():
                sdp_dict[section] = dict()
                for section_key in parser_to_convert[section]:
                    sdp_dict[section][section_key] = parser_to_convert[section][section_key]
            return sdp_dict
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_parser_for_metadata(self):
        try:
            return self.config.parser.parsers.metadata_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_parser_for_search_details(self):
        try:
            return self.config.parser.parsers.search_detail_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_parser_for_user_config(self):
        try:
            return self.config.parser.parsers.user_config_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_priority_key_for_search_result_sorting(self):
        try:
            user_config_parser_keys = self.config.hardcoded.keys.user_config_parser_keyring
            user_config_parser = self._get_user_config_parser()
            return user_config_parser[user_config_parser_keys.DEFAULT][user_config_parser_keys.USER_PRIORITY]
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_regex_filtered_results_and_count(self) -> tuple:
        try:
            metadata_parser_keys = self._get_keyring_for_metadata_parser()
            results = self._qbit_get_search_results()
            filtered_results = list()
            filtered_result_count = 0
            if results is None:
                ml.log_event('no search results for \'{}\''.format(self.active_header), level=ml.WARNING)
                return None, 0
            ml.log_event('get filename regex pattern for active header \'{}\''.format(self.active_header))
            for result in results[metadata_parser_keys.RESULT]:
                filename = result[metadata_parser_keys.NAME]
                search_pattern = self._parsers_get_filename_regex()
                if self._pattern_matches(search_pattern, filename):
                    filtered_results.append(result)
                    filtered_result_count += 1
            ml.log_event('\'{}\' filtered results have been found'.format(filtered_result_count))
            return filtered_results, filtered_result_count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_search_detail_parser_at_active_header(self) -> ConfigParser:
        try:
            search_detail_parser = self.config.parser.parsers.search_detail_parser[self.active_header]
            return search_detail_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_search_detail_parser_sections_as_dict(self, section_header_name) -> dict:
        try:
            # TODO this isn't hard to do, but is this function being used anywhere? delete if no?
            search_detail_parser = self._get_parser_for_search_details()
            if section_header_name not in search_detail_parser.sections():
                ml.log_event('section header \'{}\' not found in search parser'.format(section_header_name))
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_search_state(self) -> tuple:
        """
        :return: search states
        """
        try:
            search_parser_keys = self._get_keyring_for_search_detail_parser()
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_detail_parser_at_active_header[search_parser_keys.TIME_LAST_READ] = str(datetime.now())
            _search_queued = search_detail_parser_at_active_header.getboolean(search_parser_keys.QUEUED)
            _search_running = search_detail_parser_at_active_header.getboolean(search_parser_keys.RUNNING)
            _search_stopped = search_detail_parser_at_active_header.getboolean(search_parser_keys.STOPPED)
            _search_concluded = search_detail_parser_at_active_header.getboolean(search_parser_keys.CONCLUDED)
            ml.log_event('search state for \'{}\': \n\tqueued: {}\n\trunning: {}\n\tstopped: {}\n\tconcluded: {}'.format(
                self.active_header, _search_queued, _search_running, _search_stopped, _search_concluded), announce=True)
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_search_term_from_search_detail_parser_at_active_header(self) -> str:
        ml.log_event('get search term for search detail parser at header \'{}\''.format(self.active_header))
        search_parser_keys = self._get_keyring_for_search_detail_parser()
        search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
        try:
            # if the section does not exist, set term to active header, then write change to parser
            if search_parser_keys.PRIMARY_SEARCH_TERM not in search_detail_parser_at_active_header.keys():
                # TODO this print indicates no search term was provided, could fill in the active section header
                # TODO with the default value just to suppress this from occurring except when a new term is added
                ml.log_event('\'{}\' not found in header keys for \'{}\', setting key value to header value'.format(
                    search_parser_keys.PRIMARY_SEARCH_TERM, self.active_header), level=ml.WARNING)
                search_term = self.active_header
                search_detail_parser_at_active_header[search_parser_keys.PRIMARY_SEARCH_TERM] = search_term
                return search_term
            search_term = search_detail_parser_at_active_header[search_parser_keys.PRIMARY_SEARCH_TERM]
            ml.log_event('search term \'{}\' has been retrieved..'.format(search_term))
            return search_term
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_user_config_parser_at_default_section(self) -> ConfigParser:
        try:
            user_config_parser_keys = self._get_keyring_for_user_config_parser()
            ucpk = user_config_parser_keys
            user_config_parser_at_default_section = \
               self.config.parser.parsers.user_config_parser[ucpk.DEFAULT]
            return user_config_parser_at_default_section
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _get_user_config_parser(self):
        try:
            user_config_parser = self.config.parser.parsers.user_config_parser
            return user_config_parser
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _hash(self, x, undo=False):
        # TODO add option in user config file to skip this and just write human readable data to metadata.cfg
        # TODO could also be accomplished by setting unicode_offset to 0
        try:
            _undo = -1 if undo else 1
            _ucp_keys = self._get_keyring_for_user_config_parser()
            # TODO the bug is in this expression
            _hash = ''.join([chr(ord(e) + int(
                self.config.parser.parsers.user_config_parser[_ucp_keys.DEFAULT][_ucp_keys.UNI_SHIFT])) * _undo
                             for e in str(x) if x])

            ml.log_event('hashed from {} to {}'.format(x, _hash))
            return _hash
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _increment_search_attempt_count(self):
        try:
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_attempt_count = int(search_detail_parser_at_active_header[search_parser_keys.SEARCH_ATTEMPT_COUNT])
            ml.log_event('search try counter at {}, incrementing..'.format(search_attempt_count))
            search_detail_parser_at_active_header[search_parser_keys.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _log_file_is_too_large(self):
        # TODO yep it's growing
        pass

    def _manage_log_files(self):
        # TODO .. someday .. when it seems interesting
        try:
            if self._log_file_is_too_large():
                pass  # idk delete it or something
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _manage_state_updates(self, section_states):
        try:
            ml.log_event('manage state updates..')
            _search_queued, _search_running, _search_stopped, _search_concluded = section_states
            # abbreviate class objects
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_detail_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            user_config_parser_keys = self.config.hardcoded.keys.user_config_parser_keyring
            # search sorting
            search_rank = \
                int(search_detail_parser_at_active_header[search_detail_parser_keys.SEARCH_RANK])
            # perform the appropriate action based on the search parser's values
            # TODO should i force search rank to be 0 to only allow the top prioritized?
            if _search_queued and not self._search_queue_full() and search_rank < 3:
                self._start_search()  # search is in queue and queue has room, attempt to start this search
            elif _search_running:
                _search_status = self._qbit_get_search_status()
                if search_detail_parser_keys.RUNNING in _search_status:
                    pass  # search is ongoing, do nothing
                elif search_detail_parser_keys.STOPPED in _search_status:
                    self._update_search_states(search_detail_parser_keys.STOPPED)  # mark search as stopped (finished)
                else:
                    self._update_search_states(search_detail_parser_keys.QUEUED)  # search status unexpected, re-queue this search
            elif _search_stopped:
                regex_filtered_results, regex_filtered_results_count = self._get_regex_filtered_results_and_count()
                if regex_filtered_results is not None and regex_filtered_results_count > 0:
                    # TODO results_key.supply could be sort by any key, how to get that value here?
                    search_priority = self._get_priority_key_for_search_result_sorting()
                    self._save_remote_metadata_to_local_results_sorting_by_(
                        search_priority, regex_filtered_results)  # search is finished, attempt to add results
                else:
                    self._update_search_states(search_detail_parser_keys.QUEUED)  # search stopped, no results found, re-queue
            elif _search_concluded:
                pass
            else:
                self._update_search_states(search_detail_parser_keys.QUEUED)
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _metadata_parser_write_to_metadata_config_file(self, result):
        try:
            metadata_parser_keys, user_config_parser_keys = \
                self._get_keyring_for_metadata_parser(), self._get_keyring_for_user_config_parser()
            ml.log_event('save metadata result to file: {}'.format(result[metadata_parser_keys.NAME]))
            metadata_section = self._hash(result[metadata_parser_keys.NAME])
            if not self.config.parser.parsers.metadata_parser.has_section(metadata_section):
                ml.log_event('qbit client has added result \'{}\' for header \'{}\''.format(
                    result[metadata_parser_keys.NAME], self.active_header), announce=True)
                self.config.parser.parsers.metadata_parser.add_section(metadata_section)
                header = metadata_section
                for attribute, detail in result.items():
                    # TODO there are some redundant log commands 'above' and 'below' this entry
                    # TODO i think this entry is causing the redundant log commands with _hash() calls
                    h_attr, d_attr = self._hash(attribute), self._hash(detail)
                    ml.log_event('detail added to metadata parser with attribute key \'{}\''.format(h_attr))
                    self.config.parser.parsers.metadata_parser[header][h_attr] = d_attr
                    self.pause_on_event(user_config_parser_keys.WAIT_FOR_USER)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _parsers_get_filename_regex(self) -> str:
        try:
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            filename_regex = search_detail_parser_at_active_header[search_parser_keys.REGEX_FILTER_FOR_FILENAME]
            if filename_regex not in search_detail_parser_at_active_header.keys():
                filename_regex = '.*'
                return filename_regex
            filename_regex = self.config.parser.parsers.search_detail_parser[self.active_header][filename_regex]
            return filename_regex
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
            search_parser_keys, user_config_parser_keys, metadata_parser_keys = \
                self.config.hardcoded.keys.search_parser_keyring, \
                self.config.hardcoded.keys.user_config_parser_keyring, \
                self.config.hardcoded.keys.metadata_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            count_before = self._qbit_count_all_torrents()
            ml.log_event('local machine has {} stored results before add attempt..'.format(count_before))
            # TODO why does this api call sometimes not add? bad result? not long enough wait?
            # self.qbit_client.torrents_add(urls=result['fileUrl'], is_paused=True)  # TODO delete
            self.qbit_client.torrents_add(urls=result[metadata_parser_keys.URL], is_paused=True)
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_SEARCH_RESULT_ADD)
            results_added = self._qbit_count_all_torrents() - count_before
            # TODO why does client fail to add so much? async opportunity? bad results? dig into api code perhaps
            if results_added > 0:  # successful add
                self._metadata_parser_write_to_metadata_config_file(result)
                search_detail_parser_at_active_header[search_parser_keys.RESULT_ADDED_COUNT] = \
                    str(int(search_detail_parser_at_active_header[search_parser_keys.RESULT_ADDED_COUNT]))
                return
            ml.log_event('client failed to add \'{}\''.format(result[metadata_parser_keys.NAME]), level=ml.WARNING)
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
            ml.log_event('qbit client created search job for \'{}\''.format(pattern))
            return _job, _status, _state, _id, _count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _qbit_get_search_results(self):
        try:
            search_id = self._get_active_search_ids()
            if search_id:
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
            ml.log_event(f'check search status for section \'{self.active_header}\'')
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_id, search_status = search_detail_parser_at_active_header[search_parser_keys.SEARCH_ID], None
            # TODO did this line below add any value? delete this line after decision
            # search_id_valid = self._active_header_search_id_is_valid()  # FIXME, i think i deleted this function?
            # TODO PRIORITY BUG, this section of code was double logging, fixed?
            ml.log_event(f'getting search status for header \'{self.active_header}\' with search id \'{search_id}\'')
            if search_id in self.active_search_ids.values():
                ongoing_search = self.qbit_client.search_status(search_id=search_id)
                search_status = ongoing_search.data[0]['status']
            if search_status is None:  # TODO fyi new line, monitor, delete comment after
                ml.log_event(f'search status is \'{search_status}\' for section \'{self.active_header}\'',
                             level=ml.WARNING)
                return search_status
            ml.log_event(f'search status is \'{search_status}\' for section \'{self.active_header}\'')
            return search_status
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _reset_search_ids(self):
        """
        upon initialization of new object, delete expired search_ids
        :return: None  # TODO should i return success?
        """
        try:
            search_parser_keys, user_config_parser_keys = self._get_keyring_for_search_detail_parser(), self._get_keyring_for_user_config_parser()
            search_detail_parser = self.config.parser.parsers.search_detail_parser
            for section_header in search_detail_parser.sections():
                ml.log_event('reset search id for section \'{}\''.format(section_header))
                self.active_header = section_header
                self._update_search_states(search_parser_keys.QUEUED)
                self.pause_on_event(user_config_parser_keys.WAIT_FOR_USER)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _result_has_enough_seeds(self, result) -> bool:
        try:
            metadata_parser_keys, search_parser_keys = \
                self.config.hardcoded.keys.metadata_parser_keyring, self.config.hardcoded.keys.search_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            # minimum_seeds = int(self.search_parser[self.active_header][search_key.minimum_seeds])  # TODO delete
            minimum_seeds = int(search_detail_parser_at_active_header[search_parser_keys.MIN_SEED])
            # result_seeds = result[results_key.supply]
            result_seeds = result[metadata_parser_keys.SUPPLY]
            if result_seeds > minimum_seeds:
                ml.log_event('result {} has {} seeds, attempting to add'.format(result['fileName'], result_seeds))
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _results_fetch_all_data(self) -> dict:
        ml.log_event('fetching results from disk', event_completed=False)
        try:
            all_data = dict()
            for section in self.config.parser.parsers.metadata_parser.sections():
                all_data[self._hash(section, True)] = dict()
                for key, detail in self.config.parser.parsers.metadata_parser[section].items():
                    all_data[self._hash(section, True)][key] = self._hash(detail, True)
            ml.log_event('fetching results from disk', event_completed=True)
            return all_data
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _save_remote_metadata_to_local_results_sorting_by_(self, attribute, regex_filtered_results: list) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        try:
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            ml.log_event('add results by {}'.format(attribute), event_completed=False)
            # TODO implement attribute here, 'rKey.nbSeeders' instead of 'popularity
            most_popular_results = self._get_most_popular_results(regex_filtered_results)
            # search_id_valid = self._active_header_search_id_is_valid()  # i think i deleted this function?
            # if not search_id_valid:
            #     ml.log_event('search id for {} is invalid'.format(self.active_header))
            #     self._update_search_states(search_parser_keys.QUEUED)  # wanted to add result but id bad, re-queue search
            #     return
            if most_popular_results is not None:
                self._check_if_search_is_concluded()  # we found some results, have we met our 'concluded' criteria?
                self._config_set_search_id_as_inactive()
                ml.log_event('results sorted by popularity for {}'.format(self.active_header))
                for result in most_popular_results:
                    if self._result_has_enough_seeds(result):
                        # TODO if add was not successful, log FAILED
                        self._qbit_add_result(result)
            ml.log_event('add results by popularity', event_completed=True)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_at_active_header_is_already_started(self):
        try:
            active_search_term = self._get_search_term_from_search_detail_parser_at_active_header()
            if active_search_term in self.active_search_ids.keys():
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_detail_parser_get_all_sections(self) -> list:
        try:
            search_detail_parser = self.config.parser.parsers.search_detail_parser
            search_detail_parser_sections = search_detail_parser.sections()
            return search_detail_parser_sections
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_detail_parser_set_search_rank(self, header, search_rank) -> None:
        try:
            search_detail_parser = self._get_parser_for_search_details()
            search_detail_parser_keys = self._get_keyring_for_search_detail_parser()
            search_detail_parser[header][search_detail_parser_keys.SEARCH_RANK] = str(search_rank)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_has_yielded_the_required_results(self) -> bool:
        """
        decides if search is ready to be marked as completed (ADDED)
        :return: bool, search completed
        """
        ml.log_event('check if search can be concluded', event_completed=False)
        try:
            search_parser_keys = self._get_keyring_for_search_detail_parser()
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            attempted_searches = \
                int(search_detail_parser_at_active_header[search_parser_keys.SEARCH_ATTEMPT_COUNT])
            max_search_attempt_count = \
                int(search_detail_parser_at_active_header[search_parser_keys.MAX_SEARCH_ATTEMPT_COUNT])
            results_added = \
                int(search_detail_parser_at_active_header[search_parser_keys.RESULT_ADDED_COUNT])
            results_required = \
                int(search_detail_parser_at_active_header[search_parser_keys.RESULT_REQUIRED_COUNT])
            if results_added > results_required:
                ml.log_event('search \'{}\' can be concluded, '
                             'requested result count has been added'.format(self.active_header),
                             event_completed=True)
                self._search_set_end_reason(search_parser_keys.REQUIRED_RESULT_COUNT_FOUND)  # enough results, concluded
                return True
            elif attempted_searches > max_search_attempt_count:
                ml.log_event('search can be concluded, '
                             'too many search attempts w/o meeting requested result count'.format(self.active_header),
                             event_completed=True)
                self._search_set_end_reason(search_parser_keys.TIMED_OUT)  # too many search attempts, conclude
                return True
            ml.log_event('search \'{}\' will be allowed to continue'.format(self.active_header), event_completed=True)
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_id_active(self) -> bool:
        try:
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            search_id = search_detail_parser_at_active_header[search_parser_keys.SEARCH_ID]
            if search_id == self.active_search_ids[self.active_header]:
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_queue_full(self) -> bool:
        ml.log_event('check search queue..')
        try:
            if self._search_at_active_header_is_already_started():
                return True  # TODO, add this feature
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                ml.log_event('search queue is NOT full..')
                ml.log_event('active search headers are..')
                for active_search_header_name in self.active_search_ids.keys():
                    ml.log_event('search header : \'{}\''.format(active_search_header_name))
                return False
            ml.log_event('search queue is FULL, cannot add header \'{}\''.format(self.active_header, announce=True))
            ml.log_event('active search headers are..')
            for active_search_header_name in self.active_search_ids.keys():
                ml.log_event('search header : \'{}\''.format(active_search_header_name))
            return True
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _search_set_end_reason(self, reason):
        try:
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            ml.log_event('setting end reason \'{}\' for search header {}'.format(reason, self.active_header))
            self.config.parser.parsers.search_detail_parser[self.active_header][search_parser_keys.SEARCH_STOPPED_REASON] = reason
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _set_search_order_ranking_by_(self, sort_key):
        """
        1. sort the key:value pair of the dict into a tuple of 2 (key, value), sorted by sort_key's value
        2. assign a search rank to each search header based on previous sort
        3. write the search rank to the search detail parser
        :param sort_key:
        :return:
        """
        try:
            search_detail_parser = self._get_parser_for_search_details()
            sdp_as_dict = self._get_parser_as_sortable_(search_detail_parser)
            # FIXME main search sorting bug, i think the search rank sorting bug was in this sorted(), delete if fix works
            sdp_as_dict_sorted = sorted(sdp_as_dict.items(), key=lambda k: k[1][sort_key])
            for search_rank in range(len(sdp_as_dict_sorted)):
                header = sdp_as_dict_sorted[search_rank][0]
                self._search_detail_parser_set_search_rank(header, search_rank)
                ml.log_event(f'search rank \'{search_rank}\' assigned to header \'{header}\'')
            pass  # TODO delete me, used as a breakpoint when debugging
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _set_time_last_searched_for_active_header(self):
        try:
            search_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_parser_detail_keys = self._get_keyring_for_search_detail_parser()
            search_parser_at_active_header[search_parser_detail_keys.TIME_LAST_SEARCHED] = str(datetime.now())
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _start_search(self):
        try:
            search_parser_keys = self._get_keyring_for_search_detail_parser()
            search_term = self._get_search_term_from_search_detail_parser_at_active_header()
            search_job, search_status, search_state, search_id, search_count = \
                self._qbit_create_search_job(search_term, 'all', 'all')
            if search_id is not None:
                if search_id is not search_parser_keys.EMPTY:
                    # TODO potential bug fix? seems to fix bug, delete this line whenever
                    self.active_search_ids[self.active_header] = search_id
            if search_parser_keys.RUNNING in search_state:  # search started successfully
                self._set_time_last_searched_for_active_header()
                ml.log_event('search started for \'{}\' with search id \'{}\''.format(self.active_header, search_id),
                             event_completed=True, announce=True)
                # TODO this function IS the error, search_ids are never added which is causing problems
                self._config_set_search_id_as_active()
                self._update_search_states(search_parser_keys.RUNNING)
            elif search_parser_keys.STOPPED in search_status:
                ml.log_event('search not successfully started for \'{}\''.format(
                    self.active_header), announce=True, level=ml.WARNING)
            else:
                ml.log_event('search_state is not \'{}\' or \'{}\', there was a problem starting the search!'.format(
                    search_parser_keys.RUNNING, search_parser_keys.STOPPED), level=ml.ERROR)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _update_search_states(self, api_state_key):
        ml.log_event('updating the search state machine..')
        try:
            search_parser_keys = self._get_keyring_for_search_detail_parser()
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            if api_state_key == search_parser_keys.QUEUED:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.YES
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.NO
                self.config.parser.parsers.search_detail_parser.remove_section(search_parser_keys.SEARCH_ID)
                ml.log_event('search for \'{}\' is queued, will be started when search queue has vacancy'.format(
                    self.active_header))
            elif api_state_key == search_parser_keys.RUNNING:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.YES
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.NO
                self._increment_search_attempt_count()
                ml.log_event('search for \'{}\' is running.. please stand by..'.format(self.active_header))
            elif api_state_key == search_parser_keys.STOPPED:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.YES
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.NO
                ml.log_event('search for \'{}\' is stopped and will be processed on next program loop'.format(
                    self.active_header))
            elif api_state_key == search_parser_keys.CONCLUDED:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.YES
                ml.log_event('search for \'{}\' has concluded due to exceeding user preferences, '
                             'no further action to be taken'.format(self.active_header))
            else:
                pass
            search_detail_parser_at_active_header[search_parser_keys.TIME_LAST_WRITTEN] = str(datetime.now())  # TODO what???
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def _write_list_of_dict_to_parser(self, list_of_dicts: dict, parser: ConfigParser) -> None:
        try:
            for _dict in list_of_dicts:
                for key, val in _dict.items():
                    pass
            # TODO above, do the opposite of the code below
            search_detail_parser = self._get_parser_for_search_details()
            sdp_dicts, sdp_dict = list(), dict()
            for section in search_detail_parser.sections():
                sdp_dict[section] = dict()
                for section_key in search_detail_parser[section]:
                    sdp_dict[section][section_key] = search_detail_parser[section][section_key]
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
