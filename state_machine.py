from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from state_machine_ifs import add_results_from_
from state_machine_ifs import all_searches_concluded
from state_machine_ifs import api_if_create_search_job_for_
from state_machine_ifs import api_if_get_connection_time_start
from state_machine_ifs import api_if_get_search_status_for_
from state_machine_ifs import cfg_if_read_parser_value_at_
from state_machine_ifs import cfg_if_write_parser_value_with_
from state_machine_ifs import cfg_if_write_to_disk
from state_machine_ifs import empty_
from state_machine_ifs import get_all_sections_from_parser_
from state_machine_ifs import get_search_id_from_
from state_machine_ifs import get_search_results_for_
from state_machine_ifs import get_search_state
from state_machine_ifs import pause_on_event
from state_machine_ifs import print_search_ids_from_
from state_machine_ifs import ready_to_start_
from state_machine_ifs import search_has_yielded_required_results
from state_machine_ifs import sort_and_prioritize_searches
from state_machine_ifs import increment_search_state
from state_machine_ifs import u_key


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

    def increment_loop_count(self):
        try:
            ml.log_event(f'current connection to client was started at \'{api_if_get_connection_time_start()}\'')
            self.main_loop_count += 1
            ml.log_event(f'main loop has ended, {self.main_loop_count} total loops..')
        except Exception as e_err:
            ml.log_event(f'error incrementing loop count', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def initiate_and_monitor_searches(self):
        try:
            search_sections = get_all_sections_from_parser_(search=True)
            sort_and_prioritize_searches()
            pause_on_event(u_key.WAIT_FOR_USER)
            for search_section in search_sections:
                self.active_section = search_section
                ml.log_event(f'monitoring search header \'{self.active_section}\'')
                search_state = get_search_state()
                self.manage_state_updates(search_state)
            cfg_if_write_to_disk()  # FIXME p3, consider location of this line
        except Exception as e_err:
            ml.log_event(f'error during initiating and monitoring of searches', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def manage_state_updates(self, search_state):
        try:
            ml.log_event('begin to manage state updates..')
            search_queued, search_running, search_stopped, search_concluded = search_state
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
                    increment_search_state(self.active_section)  # search should be running, but status is None.. requeue
                    return
                print_search_ids_from_(self.active_search_ids)
                if s_key.RUNNING in search_status:
                    pass  # search ongoing, do nothing
                elif s_key.STOPPED in search_status:
                    increment_search_state(self.active_section)  # mark search as stopped (finished)
                else:
                    increment_search_state(self.active_section)  # unexpected state, re-queue
            elif search_stopped:
                results, section_and_id = None, None
                if self.active_section in self.active_search_ids:
                    section_and_id = (self.active_section, self.active_search_ids[self.active_section])
                    results = get_search_results_for_(active_kv=section_and_id)
                if results is None or self.active_section not in self.active_search_ids:
                    ml.log_event(f'search \'{self.active_section}\' is stale, re-queued', level=ml.WARNING)
                else:
                    add_results_from_(section_and_id, results)  # FIXME p0, this is the source of most bugs rn
                    self.set_search_id_as_(search_id, active=False)
                    if search_has_yielded_required_results(self.active_section):
                        increment_search_state(self.active_section)
                        return
                increment_search_state(self.active_section)
            elif search_concluded:
                pass
            else:
                ml.log_event(f'header \'{self.active_section}\' is restricted from starting by search '
                             f'rank and/or search queue, this is by design', level=ml.WARNING)
                increment_search_state(self.active_section)
            pause_on_event(u_key.WAIT_FOR_SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(f'error managing state updates', level=ml.ERROR)
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
            search_term = cfg_if_read_parser_value_at_(section=self.active_section, key=s_key.TERM)
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
                increment_search_state(self.active_section)  # search is confirmed to be running
            elif s_key.STOPPED in search_status:
                ml.log_event(f'search status is stopped immediately after starting for \'{self.active_section}\'',
                             announce=True, level=ml.WARNING)
            else:
                ml.log_event(f'search_state is not \'{s_key.RUNNING}\' or \'{s_key.STOPPED}\', there was a '
                             f'problem starting the search!', level=ml.ERROR)
        except Exception as e_err:
            ml.log_event(f'error starting search', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    ml = MinimalLog()
    ml.log_event('this should not be run directly, user main loop')
else:
    ml = MinimalLog(__name__)
