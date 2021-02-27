from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from qbit_bot_helper import enough_results_in_
from qbit_bot_helper import get_all_sections_from_parser_
from qbit_bot_helper import hash_metadata
from qbit_bot_helper import m_key, s_key, u_key
from qbit_bot_helper import m_parser, s_parser, u_parser
from qbit_bot_helper import reduce_search_expectations_for_
from qbit_bot_helper import set_search_rank_using_
from qbit_interface.api_comm import QbitApiCaller
from user_configuration.settings_io import QbitConfig
from time import sleep


class QbitStateManager:
    def __init__(self):
        ml.log_event(f'initialize \'{self.__class__}\'', event_completed=False, announce=True)
        self.api = QbitApiCaller()
        self.main_loop_count = 0
        self.active_search_ids = dict()
        self.active_section = ''
        ml.log_event(f'initialize \'{self.__class__}\'', event_completed=True, announce=True)
        self.pause_on_event(u_key.WAIT_FOR_USER)

    def get_search_state(self) -> tuple:
        try:
            parser_at_active = s_parser[self.active_section]
            parser_at_active[s_key.TIME_LAST_READ] = str(dt.now())
            # get search status from file
            search_queued = parser_at_active.getboolean(s_key.QUEUED)
            search_running = parser_at_active.getboolean(s_key.RUNNING)
            search_stopped = parser_at_active.getboolean(s_key.STOPPED)
            search_concluded = parser_at_active.getboolean(s_key.CONCLUDED)
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
            ml.log_event('REMEMBER, when debugging, start by comparing parser '
                         'keys with settings io string values', level=ml.WARNING)

    def increment_search_attempt_count(self):
        try:
            parser_at_active = s_parser[self.active_section]
            search_attempt_count = int(parser_at_active[s_key.SEARCH_ATTEMPT_COUNT])
            ml.log_event(f'search try counter at {search_attempt_count}, incrementing..')
            parser_at_active[s_key.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def initiate_and_monitor_searches(self):
        try:
            search_sections = get_all_sections_from_parser_(search=True)
            set_search_rank_using_(s_key.TIME_LAST_SEARCHED)
            self.pause_on_event(u_key.WAIT_FOR_USER)
            for search_section in search_sections:
                self.active_section = search_section
                ml.log_event(f'monitoring search header \'{self.active_section}\'')
                search_state = self.get_search_state()
                self.manage_state_updates(search_state)
            conf.write_config_to_disk()
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def manage_state_updates(self, section_search_state):
        try:
            ml.log_event('begin to manage state updates..')
            search_queued, search_running, search_stopped, search_concluded = section_search_state
            # shared  parser variables
            s_parser_at_active = s_parser[self.active_section]
            u_parser_at_default = u_parser[u_key.DEFAULT]
            # shared variables
            expected_results_count = int(s_parser_at_active[s_key.EXPECTED_SEARCH_RESULT_COUNT])
            unicode_offset = u_parser_at_default[u_key.UNI_SHIFT]
            if self.active_section in self.active_search_ids:
                search_id = self.active_search_ids[self.active_section]
            else:
                search_id = ''
            search_priority = u_parser_at_default[u_key.USER_PRIORITY]  # TODO allow for other priorities?
            search_rank = int(conf.read_parser_value_with_(s_key.RANK, self.active_section, search=True))
            if search_queued and not self.search_queue_full() and search_rank < 3:  # TODO un-hardcode this
                self.start_search()
            elif search_running:
                search_status = self.api.get_search_status(search_id)
                if search_status is None:
                    ml.log_event(f'bad search id \'{search_id}\', ignored and re-queued', level=ml.WARNING)
                    self.update_search_states(s_key.QUEUED)  # search should be running, but status is None.. requeue
                    return
                ml.log_event(f'ongoing searches are..')
                for section_header, search_id in self.active_search_ids.items():
                    ml.log_event(f'\t header \'{section_header}\' with id \'{search_id}\'')
                if s_key.RUNNING in search_status:
                    pass  # search ongoing, do nothing
                elif s_key.STOPPED in search_status:
                    self.update_search_states(s_key.STOPPED)  # mark search as stopped (finished)
                else:
                    self.update_search_states(s_key.QUEUED)  # unexpected state, re-queue
            elif search_stopped:
                filename_regex = conf.read_parser_value_with_(key=s_key.REGEX_FILTER_FOR_FILENAME,
                                                              section=self.active_section, search=True)
                results = self.api.get_search_results(search_id=search_id, use_filename_regex_filter=True,
                                                      filename_regex=filename_regex, metadata_filename_key=m_key.NAME)
                if results is None or self.active_section not in self.active_search_ids:
                    ml.log_event(f'^^ ???what the fuck is this call occurring <100us prior??? ^^')
                    # FIXME there is an undiscovered bug less than 100us before this log event call
                    ml.log_event(f'search \'{self.active_section}\' is stale, re-queued', level=ml.WARNING)
                    self.update_search_states(s_key.QUEUED)
                    return
                assert self.active_section in self.active_search_ids, 'active section not in active search ids!'
                self.set_search_id_as_(search_id, active=False)  # TODO should this be moved earlier or later?
                results_count = len(results)
                # TODO results_key.supply could be sort by any key
                ml.log_event(f'add results by {search_priority}')
                ml.log_event(f'get most popular \'{expected_results_count}\' count results')
                if not enough_results_in_(results, expected_results_count):
                    c_key, er_key = s_key.CONCLUDED, s_key.EXPECTED_SEARCH_RESULT_COUNT
                    reduce_search_expectations_for_(self.active_section, c_key, er_key)
                    expected_results_count = results_count
                # TODO remove hardcoded nbSeeders
                sorted_results = sorted(results, key=lambda k: k['nbSeeders'], reverse=True)
                self.update_search_states(s_key.QUEUED)  # wanted to add result but id bad, re-queue search
                searches_concluded = dict()
                active_is_concluded = s_parser_at_active.getboolean(s_key.CONCLUDED)
                if active_is_concluded:
                    conf.write_parser_value_with_key_(parser_key=s_key.CONCLUDED, value='yes',
                                                      section=self.active_section, search=True)
                for section in s_parser.sections():
                    searches_concluded[section] = s_parser_at_active.getboolean(s_key.CONCLUDED)
                if all(searches_concluded.values()):
                    ml.log_event('all search tasks concluded, exiting program')
                    exit()
                ml.log_event(f'results sorted by popularity for {self.active_section}')
                minimum_seeds = int(s_parser_at_active[s_key.MIN_SEED])
                for result in sorted_results:
                    results_added_count = int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT])
                    if results_added_count > expected_results_count:
                        # TODO this would be a successful conclusion
                        return  # enough results have been added for this header, stop
                    result_seeds = result[m_key.SUPPLY]
                    enough_seeds = True if result_seeds > minimum_seeds else False
                    if enough_seeds:
                        count_before = self.api.count_all_local_results()
                        ml.log_event(f'local machine has {count_before} stored results before add attempt..')
                        # FIXME NEXT, move api call to api_comm.py
                        self.api.qbit_client.torrents_add(urls=result[m_key.URL], is_paused=True)
                        self.pause_on_event(u_key.WAIT_FOR_SEARCH_RESULT_ADD)
                        results_added = self.api.count_all_local_results() - count_before
                        # TODO why does client fail to add so often? outside project scope?
                        if results_added > 0:  # successful add
                            results_added_count += 1
                            s_parser_at_active[s_key.RESULTS_ADDED_COUNT] = str(results_added_count)
                            ml.log_event(f'save metadata result to file: {result[m_key.NAME]}')
                            metadata_section = hash_metadata(result[m_key.NAME], offset=unicode_offset)
                            if m_parser.has_section(metadata_section):
                                ml.log_event(f'metadata parser already has section \'{metadata_section}\'',
                                             level=ml.WARNING)
                                # FIXME this could be a bug if two files had the same name.. do i care? at this time, no
                                continue
                            ml.log_event(f'qbit client has added result \'{result[m_key.NAME]}\' for '
                                         f'header \'{self.active_section}\'', announce=True)
                            m_parser.add_section(metadata_section)
                            for attribute, detail in result.items():
                                h_attr, d_attr = \
                                    hash_metadata(attribute, offset=unicode_offset), \
                                    hash_metadata(detail, offset=unicode_offset)
                                conf.write_parser_value_with_key_(parser_key=h_attr, value=d_attr,
                                                                  section=metadata_section, metadata=True)
                                self.pause_on_event(u_key.WAIT_FOR_USER)
                            if results_added_count > expected_results_count:
                                return
                            s_parser_at_active[s_key.RESULTS_ADDED_COUNT] = \
                                str(int(s_parser_at_active[s_key.RESULTS_ADDED_COUNT]))
                        ml.log_event(f'client failed to add \'{result[m_key.NAME]}\'', level=ml.WARNING)
                else:
                    ml.log_event(f're-queueing search for {self.active_section}..')
                    self.update_search_states(s_key.QUEUED)  # no results found, re-queue
            elif search_concluded:
                pass
            else:
                ml.log_event(f'header \'{self.active_section}\' is restricted from starting by search '
                             f'rank and/or search queue, this is by design', level=ml.WARNING)
                self.update_search_states(s_key.QUEUED)
            self.pause_on_event(u_key.WAIT_FOR_SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    @staticmethod
    def pause_on_event( pause_type):
        try:
            timestamp = dt.now()
            parser_at_default = u_parser[u_key.DEFAULT]
            if pause_type == u_key.WAIT_FOR_MAIN_LOOP:
                delay = int(parser_at_default[u_key.WAIT_FOR_MAIN_LOOP])
                ml.log_event(f'{timestamp} waiting {delay} seconds for main loop repeat..')
                sleep(delay)
            elif pause_type == u_key.WAIT_FOR_SEARCH_STATUS_CHECK:
                delay = int(parser_at_default[u_key.WAIT_FOR_SEARCH_STATUS_CHECK])
                ml.log_event(f'{timestamp} waiting {delay} seconds for search state check..')
                sleep(delay)
            elif pause_type == u_key.WAIT_FOR_SEARCH_RESULT_ADD:
                delay = int(parser_at_default[u_key.WAIT_FOR_SEARCH_RESULT_ADD])
                ml.log_event(f'{timestamp} waiting {delay} seconds for add attempt..')
                sleep(delay)
            elif pause_type == u_key.WAIT_FOR_USER:
                delay = int(parser_at_default[u_key.WAIT_FOR_USER])
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
                    ml.log_event(f'\tsearch header : \'{active_search_header_name}\'')
                return False
            ml.log_event(f'search queue is FULL, cannot add header \'{self.active_section}\'', announce=True)
            ml.log_event('active search headers are..')
            for active_search_header_name in self.active_search_ids.keys():
                ml.log_event(f'\tsearch header : \'{active_search_header_name}\'')
            return True
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def set_search_id_as_(self, search_id: str, active=False):
        try:
            if not active:
                ml.log_event(f'deleting dict entry for \'{search_id}\' at \'{self.active_section}\'')
                section_exists = True if self.active_section in self.active_search_ids else False
                if section_exists:
                    del self.active_search_ids[self.active_section]
                return
            ml.log_event(f'creating dict entry for \'{search_id}\' at \'{self.active_section}\'')
            self.active_search_ids[self.active_section] = search_id
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def start_search(self):
        try:
            search_term = conf.read_parser_value_with_(key=s_key.TERM,
                                                       section=self.active_section,
                                                       search=True)
            # search_term = s_parser[self.active_section][s_key.TOPIC]  # TODO delete?
            search_properties = self.api.create_search_job(search_term, 'all', 'all')
            search_job, search_status, search_state, search_id, search_count = search_properties
            if search_id is None or empty_(search_id):
                ml.log_event(f'invalid API return \'{search_id}\'', level=ml.ERROR)
                raise Exception('search id from API is invalid')
            if s_key.RUNNING in search_state:  # for search sorting
                key = s_key.TIME_LAST_SEARCHED
                tls = dt.now()
                conf.write_parser_value_with_key_(parser_key=key,
                                                  value=tls,
                                                  section=self.active_section,
                                                  search=True)
                ml.log_event(f'search started for \'{self.active_section}\' with search id \'{search_id}\'',
                             event_completed=True, announce=True)
                self.active_search_ids[self.active_section] = search_id
                self.update_search_states(s_key.RUNNING)
            elif s_key.STOPPED in search_status:
                ml.log_event(f'search status is stopped immediately after starting for \'{self.active_section}\'',
                             announce=True, level=ml.WARNING)
            else:
                ml.log_event(f'search_state is not \'{s_key.RUNNING}\' or \'{s_key.STOPPED}\', there was a '
                             f'problem starting the search!', level=ml.ERROR)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def update_search_states(self, api_state_key):
        ml.log_event('updating the search state machine..')
        try:
            parser_at_active = s_parser[self.active_section]
            if api_state_key == s_key.QUEUED:
                parser_at_active[s_key.QUEUED] = s_key.YES
                parser_at_active[s_key.RUNNING] = s_key.NO
                parser_at_active[s_key.STOPPED] = s_key.NO
                parser_at_active[s_key.CONCLUDED] = s_key.NO
                s_parser.remove_section(s_key.ID)  # queued, delete any existing search id
                if self.active_section in self.active_search_ids:
                    del self.active_search_ids[self.active_section]
                ml.log_event(f'search for \'{self.active_section}\' is queued, will '
                             f'be started when search queue has vacancy')
            elif api_state_key == s_key.RUNNING:
                parser_at_active[s_key.QUEUED] = s_key.NO
                parser_at_active[s_key.RUNNING] = s_key.YES
                parser_at_active[s_key.STOPPED] = s_key.NO
                parser_at_active[s_key.CONCLUDED] = s_key.NO
                self.increment_search_attempt_count()
                ml.log_event(f'search for \'{self.active_section}\' is running.. please stand by..')
            elif api_state_key == s_key.STOPPED:
                parser_at_active[s_key.QUEUED] = s_key.NO
                parser_at_active[s_key.RUNNING] = s_key.NO
                parser_at_active[s_key.STOPPED] = s_key.YES
                parser_at_active[s_key.CONCLUDED] = s_key.NO
                ml.log_event(f'search for \'{self.active_section}\' is stopped and will '
                             f'be processed on next loop')
            elif api_state_key == s_key.CONCLUDED:
                parser_at_active[s_key.QUEUED] = s_key.NO
                parser_at_active[s_key.RUNNING] = s_key.NO
                parser_at_active[s_key.STOPPED] = s_key.NO
                parser_at_active[s_key.CONCLUDED] = s_key.YES
                ml.log_event(f'search for \'{self.active_section}\' has concluded due to '
                             f'exceeding user preferences, no further action to be taken')
            else:
                pass
            parser_at_active[s_key.TIME_LAST_WRITTEN] = str(dt.now())
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