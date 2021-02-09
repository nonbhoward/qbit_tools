from qbit_interface.api_comm import QbitApiCaller
from qbit_interface.api_helper import *
from qbit_interface.config_helper import QbitConfig
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from time import sleep


class QbitStateManager:
    def __init__(self, manage_log_files=False):
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=False, announce=True)
        self.api = QbitApiCaller()
        self.cfg = QbitConfig()
        self.main_loop_count = 0
        self.active_search_ids = dict()
        self.active_section = ''
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=True, announce=True)
        self.pause_on_event(self.cfg.user_config_keys.WAIT_FOR_USER)

    def increment_loop_count(self):
        self.main_loop_count += 1
        ml.log_event(f'current connection to client was started at \'{self.api.connection_time_start}\'')
        ml.log_event(f'main loop has ended, {self.main_loop_count} total loops..')
        for _ in range(3):
            ml.log_event('when in doubt, compare parsed file keys with '
                         'config reader string values', level=ml.WARNING)

    def initiate_and_monitor_searches(self):
        try:
            search_headers = self.cfg.get_all_sections_from_parser_(search_detail=True)
            s_keys = self.cfg.get_keyring_for_(search_detail=True)
            u_keys = self.cfg.get_keyring_for_(user_config=True)
            self.cfg.set_search_rank_using_(s_keys.TIME_LAST_SEARCHED)
            self.pause_on_event(u_keys.WAIT_FOR_USER)
            for search_detail_parser_section_header in search_headers:
                self.active_section = search_detail_parser_section_header
                ml.log_event(f'monitoring search header \'{self.active_section}\'')
                search_state = self.get_search_state()
                self.manage_state_updates(search_state)
            self.cfg.write_config_to_disk()
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def pause_on_event(self, pause_type):
        try:
            timestamp = datetime.now()
            parser = self.cfg.user_config_parser
            keys = self.cfg.user_config_keys
            parser_at_default = parser[keys.DEFAULT]
            if pause_type == keys.WAIT_FOR_MAIN_LOOP:
                delay = int(parser_at_default[keys.WAIT_FOR_MAIN_LOOP])
                ml.log_event(f'{timestamp} waiting {delay} seconds for main loop repeat..')
                sleep(delay)
            elif pause_type == keys.WAIT_FOR_SEARCH_STATUS_CHECK:
                delay = int(parser_at_default[keys.WAIT_FOR_SEARCH_STATUS_CHECK])
                ml.log_event(f'{timestamp} waiting {delay} seconds for search state check..')
                sleep(delay)
            elif pause_type == keys.WAIT_FOR_SEARCH_RESULT_ADD:
                delay = int(parser_at_default[keys.WAIT_FOR_SEARCH_RESULT_ADD])
                ml.log_event(f'{timestamp} waiting {delay} seconds for add attempt..')
                sleep(delay)
            elif pause_type == keys.WAIT_FOR_USER:
                delay = int(parser_at_default[keys.WAIT_FOR_USER])
                ml.log_event(f'{timestamp} waiting {delay} seconds to let user follow log..')
                sleep(delay)
            else:
                raise Exception(f'unknown pause type \'{pause_type}\'')
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_search_state(self) -> tuple:
        """
        :return: search states
        """
        try:
            parser_at_active_section = self.cfg.search_detail_parser[self.active_section]
            keys = self.cfg.search_detail_keys
            # record a timestamp of this read action
            parser_at_active_section[keys.TIME_LAST_READ] = str(datetime.now())
            # get search status from file
            _search_queued = parser_at_active_section.getboolean(keys.QUEUED)
            _search_running = parser_at_active_section.getboolean(keys.RUNNING)
            _search_stopped = parser_at_active_section.getboolean(keys.STOPPED)
            _search_concluded = parser_at_active_section.getboolean(keys.CONCLUDED)
            ml.log_event('search state for \'{}\': \n\tqueued: {}\n\trunning: {}\n\tstopped: {}\n\tconcluded: {}'.format(
                self.active_section, _search_queued, _search_running, _search_stopped, _search_concluded), announce=True)
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def manage_state_updates(self, section_search_state):
        try:
            ml.log_event('manage state updates..')
            _search_queued, _search_running, _search_stopped, _search_concluded = section_search_state
            parser = self.cfg.search_detail_parser
            parser_at_active_section = parser[self.active_section]
            s_keys = self.cfg.search_detail_keys
            u_keys = self.cfg.user_config_keys
            search_rank = int(parser_at_active_section[s_keys.SEARCH_RANK])
            if _search_queued and not self._search_queue_full() and search_rank < 3:  # TODO un-hardcode this
                self.api.start_search_for_(parser, self.active_section, s_keys)  # search is in queue and queue not full
            elif _search_running:
                search_status = get_search_status()  # FIXME
                if s_keys.RUNNING in search_status:
                    pass  # search is ongoing, do nothing
                elif s_keys.STOPPED in search_status:
                    self._update_search_states(s_keys.STOPPED)  # mark search as stopped (finished)
                else:
                    self._update_search_states(s_keys.QUEUED)  # search status unexpected, re-queue
            elif _search_stopped:
                regex_filtered_results, regex_filtered_results_count = self._get_regex_filtered_results_and_count()
                if regex_filtered_results is not None and regex_filtered_results_count > 0:
                    # TODO results_key.supply could be sort by any key, how to get that value here?
                    # search_priority = self._get_priority_key_for_search_result_sorting()  # TODO delete
                    u_key = self.config.user_config_keys
                    search_priority = self.config.parser_value_read_with_(
                        parser_key=u_key.USER_PRIORITY, user_config=True)
                    self._save_remote_metadata_to_local_results_sorting_by_(
                        search_priority, regex_filtered_results)  # search is finished, attempt to add results
                else:
                    ml.log_event(f're-queueing search for {self.active_section}..')
                    self._update_search_states(s_keys.QUEUED)  # no results found, re-queue
            elif _search_concluded:
                pass
            else:
                self._update_search_states(s_keys.QUEUED)
            self.pause_on_event(u_keys.WAIT_FOR_SEARCH_STATUS_CHECK)
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
            ml.log_event('search queue is FULL, cannot add header \'{}\''.format(self.active_section, announce=True))
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
                    self.active_section))
            elif api_state_key == search_parser_keys.RUNNING:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.YES
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.NO
                self._increment_search_attempt_count()
                ml.log_event('search for \'{}\' is running.. please stand by..'.format(self.active_section))
            elif api_state_key == search_parser_keys.STOPPED:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.YES
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.NO
                ml.log_event('search for \'{}\' is stopped and will be processed on next program loop'.format(
                    self.active_section))
            elif api_state_key == search_parser_keys.CONCLUDED:
                search_detail_parser_at_active_header[search_parser_keys.QUEUED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.RUNNING] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.STOPPED] = search_parser_keys.NO
                search_detail_parser_at_active_header[search_parser_keys.CONCLUDED] = search_parser_keys.YES
                ml.log_event('search for \'{}\' has concluded due to exceeding user preferences, '
                             'no further action to be taken'.format(self.active_section))
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
