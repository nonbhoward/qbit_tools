from configparser import ConfigParser  # only used to type a return value
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from re import findall
from time import sleep
from user_configuration.WEB_API_CREDENTIALS import HOST, USER, PASS
import qbittorrentapi


class QbitStateManager:
    def __init__(self, manage_log_files=False):
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=False, announce=True)
        self.config = ''  # FIXME
        self.main_loop_count = 0
        self.active_search_ids, self.active_header = dict(), ''
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=True, announce=True)
        self.pause_on_event(self.config.hardcoded.keys.user_config_parser_keyring.WAIT_FOR_USER)
        if manage_log_files:
            self._manage_log_files()  # TODO this does nothing

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
            search_detail_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            user_config_parser_keys = self._get_keyring_for_user_config_parser()
            # perform sorting on search queue
            sort_key = search_detail_parser_keys.TIME_LAST_SEARCHED
            self._set_search_order_ranking_by_(sort_key)
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_USER)
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
            if _search_queued and not self._search_queue_full() and search_rank < 3:  # TODO un-hardcode this
                self._start_search()  # search is in queue and queue has room, attempt to start this search
            elif _search_running:
                _search_status = self._qbit_get_search_status()
                if search_detail_parser_keys.RUNNING in _search_status:
                    pass  # search is ongoing, do nothing
                elif search_detail_parser_keys.STOPPED in _search_status:
                    self._update_search_states(search_detail_parser_keys.STOPPED)  # mark search as stopped (finished)
                else:
                    self._update_search_states(search_detail_parser_keys.QUEUED)  # search status unexpected, re-queue
            elif _search_stopped:
                regex_filtered_results, regex_filtered_results_count = self._get_regex_filtered_results_and_count()
                if regex_filtered_results is not None and regex_filtered_results_count > 0:
                    # TODO results_key.supply could be sort by any key, how to get that value here?
                    search_priority = self._get_priority_key_for_search_result_sorting()
                    self._save_remote_metadata_to_local_results_sorting_by_(
                        search_priority, regex_filtered_results)  # search is finished, attempt to add results
                else:
                    ml.log_event(f're-queueing search for {self.active_header}..')
                    self._update_search_states(search_detail_parser_keys.QUEUED)  # no results found, re-queue
            elif _search_concluded:
                pass
            else:
                self._update_search_states(search_detail_parser_keys.QUEUED)
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_SEARCH_STATUS_CHECK)
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


if __name__ == '__main__':
    ml = MinimalLog()
    ml.log_event('this should not be run directly, user main loop')
else:
    ml = MinimalLog(__name__)
