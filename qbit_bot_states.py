from minimalog.minimal_log import MinimalLog
from qbit_interface.api_comm import QbitApiCaller
from qbit_interface.api_helper import *
from qbit_interface.config_helper import QbitConfig
from time import sleep


class QbitStateManager:
    def __init__(self):
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=False, announce=True)
        self.api = QbitApiCaller()
        self.cfg = QbitConfig()
        self.main_loop_count = 0
        self.active_search_ids = dict()
        self.active_section = ''
        ml.log_event('initialize \'{}\''.format(self.__class__), event_completed=True, announce=True)
        self.pause_on_event(self.cfg.user_config_keys.WAIT_FOR_USER)

    def get_search_state(self) -> tuple:
        try:
            parser_at_active = self.cfg.search_detail_parser[self.active_section]
            keys = self.cfg.search_detail_keys
            parser_at_active[keys.TIME_LAST_READ] = str(datetime.now())
            # get search status from file
            search_queued = parser_at_active.getboolean(keys.QUEUED)
            search_running = parser_at_active.getboolean(keys.RUNNING)
            search_stopped = parser_at_active.getboolean(keys.STOPPED)
            search_concluded = parser_at_active.getboolean(keys.CONCLUDED)
            ml.log_event(f'search state for \'{self.active_section}\': '
                         f'\n\tqueued: {search_queued}'
                         f'\n\trunning: {search_running}'
                         f'\n\tstopped: {search_stopped}'
                         f'\n\tconcluded: {search_concluded}', announce=True)
            return search_queued, search_running, search_stopped, search_concluded
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def increment_loop_count(self):
        ml.log_event(f'current connection to client was started at \'{self.api.connection_time_start}\'')
        self.main_loop_count += 1
        ml.log_event(f'main loop has ended, {self.main_loop_count} total loops..')
        for _ in range(3):
            ml.log_event('when in doubt, compare parsed file keys with '
                         'config reader string values', level=ml.WARNING)

    def increment_search_attempt_count(self):
        try:
            parser = self.cfg.get_parser_for_(search_detail=True)
            parser_at_active = parser[self.active_section]
            keys = self.cfg.get_keyring_for_(search_detail=True)
            search_attempt_count = int(parser_at_active[keys.SEARCH_ATTEMPT_COUNT])
            ml.log_event(f'search try counter at {search_attempt_count}, incrementing..')
            parser_at_active[keys.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def initiate_and_monitor_searches(self):
        try:
            search_sections = self.cfg.get_all_sections_from_parser_(search_detail=True)
            s_keys = self.cfg.get_keyring_for_(search_detail=True)
            u_keys = self.cfg.get_keyring_for_(user_config=True)
            self.cfg.set_search_rank_using_(s_keys.TIME_LAST_SEARCHED)
            self.pause_on_event(u_keys.WAIT_FOR_USER)
            for search_section in search_sections:
                self.active_section = search_section
                ml.log_event(f'monitoring search header \'{self.active_section}\'')
                search_state = self.get_search_state()
                self.manage_state_updates(search_state)
            self.cfg.write_config_to_disk()
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def manage_state_updates(self, section_search_state):
        try:
            ml.log_event('begin to manage state updates..')
            search_queued, search_running, search_stopped, search_concluded = section_search_state
            parser = self.cfg.search_detail_parser
            parser_at_active = parser[self.active_section]
            s_keys = self.cfg.search_detail_keys
            u_keys = self.cfg.user_config_keys
            _temp = self.cfg.parser_value_read_with_(s_keys.SEARCH_RANK, self.active_section, search_detail=True)
            search_rank = int(_temp)
            if search_queued and not self.search_queue_full() and search_rank < 3:  # TODO un-hardcode this
                self.start_search()
            elif search_running:
                search_id = self.active_search_ids[self.active_section]
                search_status = self.api.get_search_status(search_id)
                ml.log_event(f'ongoing searches are..')
                for section_header, search_id in self.active_search_ids:
                    ml.log_event(f'\t header \'{section_header}\' with id \'{search_id}\'')
                if s_keys.RUNNING in search_status:
                    pass  # search ongoing, do nothing
                elif s_keys.STOPPED in search_status:
                    self.update_search_states(s_keys.STOPPED)  # mark search as stopped (finished)
                else:
                    self.update_search_states(s_keys.QUEUED)  # unexpected state, re-queue
            elif search_stopped:
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
                    self.update_search_states(s_keys.QUEUED)  # no results found, re-queue
            elif search_concluded:
                pass
            else:
                self.update_search_states(s_keys.QUEUED)
            self.pause_on_event(u_keys.WAIT_FOR_SEARCH_STATUS_CHECK)
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

    def search_queue_full(self) -> bool:
        ml.log_event('check search queue..')
        try:
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                ml.log_event('search queue is NOT full..')
                ml.log_event('active search headers are..')
                for active_search_header_name in self.active_search_ids.keys():
                    ml.log_event(f'search header : \'{active_search_header_name}\'')
                return False
            ml.log_event(f'search queue is FULL, cannot add header \'{self.active_section}\'', announce=True)
            ml.log_event('active search headers are..')
            for active_search_header_name in self.active_search_ids.keys():
                ml.log_event(f'search header : \'{active_search_header_name}\'')
            return True
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def start_search(self):
        try:
            parser = self.cfg.search_detail_parser
            keys = self.cfg.search_detail_keys
            search_term = parser[self.active_section][keys.PRIMARY_SEARCH_TERM]
            search_properties = self.api.create_search_job(search_term, 'all', 'all')
            search_job, search_status, search_state, search_id, search_count = search_properties
            if search_id is None or empty_(search_id):
                raise Exception('search id invalid, no! no! no! no! no!')
            if keys.RUNNING in search_state:  # for search sorting
                key = keys.TIME_LAST_SEARCHED
                tls = datetime.now()
                self.cfg.parser_value_write_with_(key, tls, self.active_section, search_detail=True)
                ml.log_event(f'search started for \'{self.active_section}\' with search id \'{search_id}\'',
                             event_completed=True, announce=True)
                self.active_search_ids[self.active_section] = search_id
                self.update_search_states(keys.RUNNING)
            elif keys.STOPPED in search_status:
                ml.log_event(f'search not successfully started for \'{self.active_section}\'',
                             announce=True, level=ml.WARNING)
            else:
                ml.log_event(f'search_state is not \'{keys.RUNNING}\' or \'{keys.STOPPED}\', there was a '
                             f'problem starting the search!', level=ml.ERROR)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def update_search_states(self, api_state_key):
        ml.log_event('updating the search state machine..')
        try:
            parser = self.cfg.get_parser_for_(search_detail=True)
            s_keys = self.cfg.get_keyring_for_(search_detail=True)
            parser_at_active = parser[self.active_section]
            if api_state_key == s_keys.QUEUED:
                parser_at_active[s_keys.QUEUED] = s_keys.YES
                parser_at_active[s_keys.RUNNING] = s_keys.NO
                parser_at_active[s_keys.STOPPED] = s_keys.NO
                parser_at_active[s_keys.CONCLUDED] = s_keys.NO
                parser.remove_section(s_keys.SEARCH_ID)  # queued, delete any existing search id
                ml.log_event('search for \'{}\' is queued, will be started when search queue has vacancy'.format(
                    self.active_section))
            elif api_state_key == s_keys.RUNNING:
                parser_at_active[s_keys.QUEUED] = s_keys.NO
                parser_at_active[s_keys.RUNNING] = s_keys.YES
                parser_at_active[s_keys.STOPPED] = s_keys.NO
                parser_at_active[s_keys.CONCLUDED] = s_keys.NO
                self.increment_search_attempt_count()
                ml.log_event('search for \'{}\' is running.. please stand by..'.format(self.active_section))
            elif api_state_key == s_keys.STOPPED:
                parser_at_active[s_keys.QUEUED] = s_keys.NO
                parser_at_active[s_keys.RUNNING] = s_keys.NO
                parser_at_active[s_keys.STOPPED] = s_keys.YES
                parser_at_active[s_keys.CONCLUDED] = s_keys.NO
                ml.log_event('search for \'{}\' is stopped and will be processed on next program loop'.format(
                    self.active_section))
            elif api_state_key == s_keys.CONCLUDED:
                parser_at_active[s_keys.QUEUED] = s_keys.NO
                parser_at_active[s_keys.RUNNING] = s_keys.NO
                parser_at_active[s_keys.STOPPED] = s_keys.NO
                parser_at_active[s_keys.CONCLUDED] = s_keys.YES
                ml.log_event('search for \'{}\' has concluded due to exceeding user preferences, '
                             'no further action to be taken'.format(self.active_section))
            else:
                pass
            parser_at_active[s_keys.TIME_LAST_WRITTEN] = str(datetime.now())  # TODO what???
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


def empty_(test_string) -> bool:
    try:
        if test_string == '':
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    ml.log_event('this should not be run directly, user main loop')
else:
    ml = MinimalLog(__name__)
