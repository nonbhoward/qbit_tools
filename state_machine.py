from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from state_machine_ifs import add_results_from_
from state_machine_ifs import all_searches_concluded
from state_machine_ifs import api_if_create_search_job_for_
from state_machine_ifs import api_if_get_connection_time_start
from state_machine_ifs import api_if_get_search_status_for_
from state_machine_ifs import empty_
from state_machine_ifs import get_all_sections_from_parser_
from state_machine_ifs import get_search_id_from_
from state_machine_ifs import get_search_results_for_
from state_machine_ifs import s_key, u_key
from state_machine_ifs import s_parser, u_parser
from state_machine_ifs import pause_on_event
from state_machine_ifs import print_search_ids_from_
from state_machine_ifs import read_parser_value_with_
from state_machine_ifs import ready_to_start_
from state_machine_ifs import search_has_yielded_required_results
from state_machine_ifs import set_search_rank_using_
from state_machine_ifs import cfg_if_write_to_disk
from state_machine_ifs import cfg_if_write_parser_value_with_

u_parser_at_default = u_parser[u_key.DEFAULT]
unicode_offset = u_parser_at_default[u_key.UNI_SHIFT]


class QbitStateManager:
    def __init__(self):
        try:
            ml.log_event(f'initialize \'{self.__class__}\'', event_completed=False, announce=True)
            self.main_loop_count, self.active_section, self.active_search_ids = \
                0, '', dict()
            ml.log_event(f'initialize \'{self.__class__}\'', event_completed=True, announce=True)
            pause_on_event(u_key.WAIT_FOR_USER)
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

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
            ml.log_event(f'error getting search state', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def increment_loop_count(self):
        try:
            ml.log_event(f'current connection to client was started at \'{api_if_get_connection_time_start()}\'')
            self.main_loop_count += 1
            ml.log_event(f'main loop has ended, {self.main_loop_count} total loops..')
        except Exception as e_err:
            ml.log_event(f'error incrementing loop count', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def increment_search_attempt_count(self):
        try:
            parser_at_active = s_parser[self.active_section]
            search_attempt_count = int(parser_at_active[s_key.SEARCH_ATTEMPT_COUNT])
            ml.log_event(f'search try counter at {search_attempt_count}, incrementing..')
            parser_at_active[s_key.SEARCH_ATTEMPT_COUNT] = str(search_attempt_count + 1)
        except Exception as e_err:
            ml.log_event(f'error incrementing search attempt count', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def initiate_and_monitor_searches(self):
        try:
            search_sections = get_all_sections_from_parser_(search=True)
            set_search_rank_using_(s_key.TIME_LAST_SEARCHED)
            pause_on_event(u_key.WAIT_FOR_USER)
            for search_section in search_sections:
                self.active_section = search_section
                ml.log_event(f'monitoring search header \'{self.active_section}\'')
                search_state = self.get_search_state()
                self.manage_state_updates(search_state)
            cfg_if_write_to_disk()  # FIXME p3, consider location of this line
        except Exception as e_err:
            ml.log_event(f'error during initiating and monitoring of searches', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def manage_state_updates(self, section_search_state):
        try:
            ml.log_event('begin to manage state updates..')
            search_queued, search_running, search_stopped, search_concluded = section_search_state
            search_id = get_search_id_from_(self)
            if all_searches_concluded():
                ml.log_event(f'program completed, exiting', announce=True)
                exit()
            if ready_to_start_(search_queued, self):
                self.start_search()
            elif search_running:
                search_status = api_if_get_search_status_for_(search_id)
                if search_status is None:
                    ml.log_event(f'bad search id \'{search_id}\', ignored and re-queued', level=ml.WARNING)
                    self.update_search_states(s_key.QUEUED)  # search should be running, but status is None.. requeue
                    return
                print_search_ids_from_(self.active_search_ids)
                if s_key.RUNNING in search_status:
                    pass  # search ongoing, do nothing
                elif s_key.STOPPED in search_status:
                    self.update_search_states(s_key.STOPPED)  # mark search as stopped (finished)
                else:
                    self.update_search_states(s_key.QUEUED)  # unexpected state, re-queue
            elif search_stopped:
                results, active_kv = None, None
                if self.active_section in self.active_search_ids:
                    active_kv = (self.active_section, self.active_search_ids[self.active_section])
                    results = get_search_results_for_(active_kv=active_kv)
                if results is None or self.active_section not in self.active_search_ids:
                    ml.log_event(f'search \'{self.active_section}\' is stale, re-queued', level=ml.WARNING)
                else:
                    add_results_from_(results, active_kv)  # FIXME p0, this is the source of most bugs rn
                    self.set_search_id_as_(search_id, active=False)
                    if search_has_yielded_required_results(self.active_section):
                        self.update_search_states(s_key.CONCLUDED)
                        return
                self.update_search_states(s_key.QUEUED)
            elif search_concluded:
                pass
            else:
                ml.log_event(f'header \'{self.active_section}\' is restricted from starting by search '
                             f'rank and/or search queue, this is by design', level=ml.WARNING)
                self.update_search_states(s_key.QUEUED)
            pause_on_event(u_key.WAIT_FOR_SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(f'error managing state updates', leve=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def search_queue_full(self) -> bool:
        ml.log_event('check search queue..')
        try:
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                ml.log_event('search queue is NOT full..')
                print_search_ids_from_(self.active_search_ids)
                return False
            ml.log_event(f'search queue is FULL, cannot add header \'{self.active_section}\'', announce=True)
            return True
        except Exception as e_err:
            ml.log_event(f'error checking if search queue full', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

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
            ml.log_event(f'error setting search id \'{search_id}\' as active=\'{active}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def start_search(self):
        try:
            search_term = read_parser_value_with_(key=s_key.TERM, section=self.active_section)
            search_properties = api_if_create_search_job_for_(search_term, 'all', 'all')
            search_count, search_id, search_status = search_properties
            if search_id is None or empty_(search_id):
                ml.log_event(f'invalid API return \'{search_id}\'', level=ml.ERROR)
                raise Exception('search id from API is invalid')
            if s_key.RUNNING in search_status:  # for search sorting
                cfg_if_write_parser_value_with_(self.active_section, s_key.TIME_LAST_SEARCHED, str(dt.now()))
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
            ml.log_event(f'error starting search', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

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
                # FIXME p1, this could increment multiple times if the main_loop is too fast?
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
            ml.log_event(f'error updating search states with \'{api_state_key}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    ml.log_event('this should not be run directly, user main loop')
else:
    ml = MinimalLog(__name__)
