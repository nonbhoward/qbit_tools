from minimalog.minimal_log import MinimalLog
from core.interface import active_section_is_in_memory_of_
from core.interface import add_results_stored_in_
from core.interface import all_searches_concluded
from core.interface import empty_
from core.interface import exit_program
from core.interface import get_all_sections_from_search_parser
from core.interface import get_connection_time_start
from core.interface import get_search_id_from_active_section_in_
from core.interface import get_search_properties_from_
from core.interface import get_search_states_for_
from core.interface import increment_search_state_at_active_section_for_
from core.interface import pause_on_event
from core.interface import print_search_ids_from_
from core.interface import ready_to_start_at_
from core.interface import reset_search_state_at_active_section_for_
from core.interface import save_results_to_
from core.interface import search_has_yielded_required_results_for_
from core.interface import search_is_running_in_
from core.interface import search_is_stopped_in_
from core.interface import set_active_section_to_
from core.interface import set_search_ranks
from core.interface import start_search_with_
from core.interface import u_key  # FIXME refactor this out, no keys belong in the state machine
from core.interface import write_parsers_to_disk


class QbitStateManager:
    def __init__(self, verbose=True):
        event = f'initializing \'{self.__class__.__name__}\''
        try:
            ml.log_event(event, announce=True, event_completed=False)
            self.main_loop_count, self.active_section = 0, ''
            self.active_sections = dict()
            self.verbose = verbose  # FIXME p3, this is not used
            ml.log_event(event, announce=True, event_completed=True)
            pause_on_event(u_key.WAIT_FOR_USER)
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)
            ml.log_event(f'error {event}')

    def increment_main_loop_count(self) -> None:
        event = f'incrementing main loop count'
        try:  # FIXME is this a better place to put a pause vs main_loop?
            self.main_loop_count += 1
            ml.log_event(f'main loop has ended, {self.main_loop_count} total loops..')
            ml.log_event(f'connection to client was started at \'{get_connection_time_start()}\'')
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)
            ml.log_event(f'error {event}')

    def initiate_and_monitor_searches(self) -> None:
        event = f'initiating and monitoring searches'
        try:  # note, this is the entry point for state machine
            search_parser_sections = get_all_sections_from_search_parser()
            set_search_ranks()
            pause_on_event(u_key.WAIT_FOR_USER)
            for section in search_parser_sections:
                set_active_section_to_(section, self)
                search_state = get_search_states_for_(section)
                self.manage_state_updates(search_state)
            if all_searches_concluded():
                exit_program()
            write_parsers_to_disk()  # FIXME p3, consider location of this line
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)
            ml.log_event(f'error {event}')

    def manage_state_updates(self, search_state) -> None:
        event = f'managing state updates'
        try:
            search_queued, search_running, search_stopped, search_concluded = search_state
            search_id = get_search_id_from_active_section_in_(self)
            section = self.active_section
            if ready_to_start_at_(section, self):
                start_search_with_(self)
            elif search_running:
                if empty_(search_id):
                    reset_search_state_at_active_section_for_(self)
                    return
                search_properties = get_search_properties_from_(self)
                if search_properties is None:
                    ml.log_event(f'bad search id \'{search_id}\', ignored and re-queued', level=ml.WARNING)
                    increment_search_state_at_active_section_for_(self)  # search should be running, status is None.. requeue
                    return
                print_search_ids_from_(self.active_sections)
                if search_is_running_in_(self):  # FIXME might want to wrapper this
                    pass  # search ongoing, do nothing
                elif search_is_stopped_in_(self):
                    increment_search_state_at_active_section_for_(self)  # mark search as stopped (finished)
                else:
                    increment_search_state_at_active_section_for_(self)  # unexpected state, re-queue
            elif search_stopped:
                # FIXME move this to interface
                if active_section_is_in_memory_of_(self):
                    save_results_to_(self)
                add_results_stored_in_(self)  # FIXME p0, bad args, fixing in rework
                increment_search_state_at_active_section_for_(self)
            elif search_concluded:
                pass
            else:
                ml.log_event(f'header \'{self.active_section}\' is restricted from starting by search '
                             f'rank and/or search queue, this is by design', level=ml.WARNING)
                increment_search_state_at_active_section_for_(self)
            pause_on_event(u_key.WAIT_FOR_SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)
            ml.log_event(f'error {event}')


if __name__ == '__main__':
    ml = MinimalLog()
    this_module = __file__.split('/')[-1]
    ml.log_event(f'do not run \'{this_module}\' directly, use main loop', level=ml.WARNING)
else:
    ml = MinimalLog(__name__)
