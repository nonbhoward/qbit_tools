from qbit_interface.api_comm import QbitApiCaller
from qbit_interface.api_helper import *
from user_configuration.settings_io import QbitConfig
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
            parser_at_active = self.cfg.search_settings_and_status[self.active_section]
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
            parser = self.cfg.get_parser_for_(search=True)
            parser_at_active = parser[self.active_section]
            keys = self.cfg.get_keyring_for_(search=True)
            search_attempt_count = int(parser_at_active[keys.SEARCH_ATTEMPT_COUNT])
            ml.log_event(f'search try counter at {search_attempt_count}, incrementing..')
            parser_at_active[keys.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def initiate_and_monitor_searches(self):
        try:
            search_sections = self.cfg.get_all_sections_from_parser_(search=True)
            search = self.cfg.get_keyring_for_(search=True)
            settings = self.cfg.get_keyring_for_(settings=True)
            self.cfg.set_search_rank_using_(search.TIME_LAST_SEARCHED)
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
            parser = self.cfg.search_settings_and_status
            parser_at_active = parser[self.active_section]
            search = self.cfg.search_detail_keys
            settings = self.cfg.user_config_keys
            _temp = self.cfg.read_parser_value_with_key_(search.SEARCH_RANK, self.active_section, search=True)
            search_rank = int(_temp)
            if search_queued and not self.search_queue_full() and search_rank < 3:  # TODO un-hardcode this
                self.start_search()
            elif search_running:
                search_id = self.active_search_ids[self.active_section]
                search_status = self.api.get_search_status(search_id)
                ml.log_event(f'ongoing searches are..')
                for section_header, search_id in self.active_search_ids:
                    ml.log_event(f'\t header \'{section_header}\' with id \'{search_id}\'')
                if search.RUNNING in search_status:
                    pass  # search ongoing, do nothing
                elif search.STOPPED in search_status:
                    self.update_search_states(search.STOPPED)  # mark search as stopped (finished)
                else:
                    self.update_search_states(search.QUEUED)  # unexpected state, re-queue
            elif search_stopped:
                regex_filtered_results, regex_filtered_results_count = self._get_regex_filtered_results_and_count()
                if regex_filtered_results is not None and regex_filtered_results_count > 0:
                    # TODO results_key.supply could be sort by any key, how to get that value here?
                    # search_priority = self._get_priority_key_for_search_result_sorting()  # TODO delete
                    s_parser = self.cfg.get_parser_for_(search=True)
                    s_key = self.cfg.get_keyring_for_(search=True)
                    u_parser = self.cfg.get_parser_for_(settings=True)
                    # u_key = self.config.user_config_keys  # TODO delete me
                    u_key = self.cfg.get_keyring_for_(settings=True)
                    # search_priority = self.config.parser_value_read_with_(
                    #     parser_key=u_key.USER_PRIORITY, settings=True)
                    search_priority = u_parser[u_key.USER_PRIORITY]
                    # FIXME below function deleted and code moved below.. delete after consolidation..
                    # self._save_remote_metadata_to_local_results_sorting_by_(search_priority, regex_filtered_results)
                    search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
                    ml.log_event('add results by {}'.format(search_priority), event_completed=False)
                    # TODO implement attribute here, 'rKey.nbSeeders' instead of 'popularity
                    most_popular_results = self.get_most_popular_results(regex_filtered_results)
                    if not self.active_header_search_id_is_valid():
                        ml.log_event('search id for {} is invalid'.format(self.active_section))
                        self.update_search_states(
                            search_parser_keys.QUEUED)  # wanted to add result but id bad, re-queue search
                        return
                    if most_popular_results is not None:
                        self.check_if_search_is_concluded()  # we found some results, have we met our 'concluded' criteria?
                        self.set_search_id_as_inactive()
                        ml.log_event('results sorted by popularity for {}'.format(self.active_section))
                        for result in most_popular_results:
                            if self.result_has_enough_seeds(result):
                                # self._qbit_add_result(result)  # FIXME, deleted this function and put code below..
                                count_before = self.count_all_local_results()
                                ml.log_event(f'local machine has {count_before} stored results before add attempt..')
                                self.qbit_client.torrents_add(urls=result[metadata_parser_keys.URL], is_paused=True)
                                self.pause_on_event(user_config_parser_keys.WAIT_FOR_SEARCH_RESULT_ADD)
                                results_added = self.count_all_local_results() - count_before
                                # TODO why does client fail to add so much? async opportunity? bad results? dig into api code perhaps
                                if results_added > 0:  # successful add
                                    self._metadata_parser_write_to_metadata_config_file(result)
                                    search_detail_parser_at_active_header[search_parser_keys.RESULTS_ADDED_COUNT] = \
                                        str(int(search_detail_parser_at_active_header[
                                                    search_parser_keys.RESULTS_ADDED_COUNT]))
                                    return
                                ml.log_event('client failed to add \'{}\''.format(result[metadata_parser_keys.NAME]),
                                             level=ml.WARNING)
                                # TODO if add was not successful, log FAILED
                    ml.log_event('add results by popularity', event_completed=True)
                    # TODO add_result goes here
                else:
                    ml.log_event(f're-queueing search for {self.active_section}..')
                    self.update_search_states(search.QUEUED)  # no results found, re-queue
            elif search_concluded:
                pass
            else:
                self.update_search_states(search.QUEUED)
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
            parser = self.cfg.search_settings_and_status
            keys = self.cfg.search_detail_keys
            search_term = parser[self.active_section][keys.PRIMARY_SEARCH_TERM]
            search_properties = self.api.create_search_job(search_term, 'all', 'all')
            search_job, search_status, search_state, search_id, search_count = search_properties
            if search_id is None or empty_(search_id):
                raise Exception('search id invalid, no! no! no! no! no!')
            if keys.RUNNING in search_state:  # for search sorting
                key = keys.TIME_LAST_SEARCHED
                tls = datetime.now()
                self.cfg.write_parser_value_with_key_(key, tls, self.active_section, search=True)
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
            parser = self.cfg.get_parser_for_(search=True)
            search = self.cfg.get_keyring_for_(search=True)
            parser_at_active = parser[self.active_section]
            if api_state_key == search.QUEUED:
                parser_at_active[search.QUEUED] = search.YES
                parser_at_active[search.RUNNING] = search.NO
                parser_at_active[search.STOPPED] = search.NO
                parser_at_active[search.CONCLUDED] = search.NO
                parser.remove_section(search.SEARCH_ID)  # queued, delete any existing search id
                ml.log_event('search for \'{}\' is queued, will be started when search queue has vacancy'.format(
                    self.active_section))
            elif api_state_key == search.RUNNING:
                parser_at_active[search.QUEUED] = search.NO
                parser_at_active[search.RUNNING] = search.YES
                parser_at_active[search.STOPPED] = search.NO
                parser_at_active[search.CONCLUDED] = search.NO
                self.increment_search_attempt_count()
                ml.log_event('search for \'{}\' is running.. please stand by..'.format(self.active_section))
            elif api_state_key == search.STOPPED:
                parser_at_active[search.QUEUED] = search.NO
                parser_at_active[search.RUNNING] = search.NO
                parser_at_active[search.STOPPED] = search.YES
                parser_at_active[search.CONCLUDED] = search.NO
                ml.log_event('search for \'{}\' is stopped and will be processed on next program loop'.format(
                    self.active_section))
            elif api_state_key == search.CONCLUDED:
                parser_at_active[search.QUEUED] = search.NO
                parser_at_active[search.RUNNING] = search.NO
                parser_at_active[search.STOPPED] = search.NO
                parser_at_active[search.CONCLUDED] = search.YES
                ml.log_event('search for \'{}\' has concluded due to exceeding user preferences, '
                             'no further action to be taken'.format(self.active_section))
            else:
                pass
            parser_at_active[search.TIME_LAST_WRITTEN] = str(datetime.now())  # TODO what???
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
