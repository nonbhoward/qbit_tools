from minimalog.minimal_log import MinimalLog
from core.interface import active_section_is_in_memory_of_
from core.interface import add_filtered_results_stored_in_
from core.interface import all_searches_concluded
from core.interface import conclude_search_for_active_section_in_
from core.interface import exit_program
from core.interface import get_all_sections_from_search_parser
from core.interface import get_connection_time_start
from core.interface import get_search_state_for_active_section_in_
from core.interface import increment_search_state_at_active_section_for_
from core.interface import pause_on_event
from core.interface import ready_to_start_at_active_section_in_
from core.interface import reset_search_state_at_active_section_for_
from core.interface import save_results_to_
from core.interface import search_at_active_section_has_completed_in_
from core.interface import search_is_running_at_active_section_in_
from core.interface import search_is_stopped_at_active_section_in_
from core.interface import set_active_section_to_
from core.interface import set_search_ranks
from core.interface import start_search_with_
from core.interface import u_key  # FIXME refactor this out, no keys belong in the state machine
from core.interface import write_parsers_to_disk


class QbitStateManager:
    def __init__(self, verbose=True):
        event = f'initializing \'{self.__class__.__name__}\''
        try:
            ml.log(event, announcement=True, event_completed=False)
            self.main_loop_count, self.active_section = 0, ''
            self.active_sections = dict()
            self.verbose = verbose  # FIXME p3, this is not used
            ml.log(event, announcement=True, event_completed=True)
            pause_on_event(u_key.WAIT_FOR_USER)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def increment_main_loop_count(self) -> None:
        event = f'incrementing main loop count'
        try:  # FIXME is this a better place to put a pause vs main_loop?
            self.main_loop_count += 1
            ml.log(f'main loop has ended, {self.main_loop_count} total loops..')
            ml.log(f'connection to client was started at \'{get_connection_time_start()}\'')
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def initiate_and_monitor_searches(self) -> None:
        event = f'initiating and monitoring searches'
        try:  # note, this is the entry point for state machine
            set_search_ranks()
            search_parser_sections = get_all_sections_from_search_parser()
            for section in search_parser_sections:
                set_active_section_to_(section, self)
                self.manage_state_updates_at_active_section()
            if all_searches_concluded():
                exit_program()
            write_parsers_to_disk()
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def manage_state_updates_at_active_section(self) -> None:
        event = f'managing state updates at active section : \'{self.active_section}\''
        try:
            search_queued, search_running, search_stopped, search_concluded = \
                get_search_state_for_active_section_in_(self)
            if ready_to_start_at_active_section_in_(self):
                start_search_with_(self)
            elif search_is_running_at_active_section_in_(self):
                pass  # if running, do nothing til stopped
            elif search_is_stopped_at_active_section_in_(self):
                if active_section_is_in_memory_of_(self):
                    save_results_to_(self)
                    add_filtered_results_stored_in_(self)
                if search_at_active_section_has_completed_in_(self):
                    conclude_search_for_active_section_in_(self)
                reset_search_state_at_active_section_for_(self)
            elif search_concluded:
                pass  # if concluded, do nothing forever
            else:
                ml.log(f'header \'{self.active_section}\' is restricted from starting by search '
                             f'rank and/or search queue, this is by design', level=ml.WARNING)
                increment_search_state_at_active_section_for_(self)
            pause_on_event(u_key.WAIT_FOR_SEARCH_STATUS_CHECK)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')


if __name__ == '__main__':
    ml = MinimalLog()
    this_module = __file__.split('/')[-1]
    ml.log(f'do not run \'{this_module}\' directly, use main loop', level=ml.WARNING)
else:
    ml = MinimalLog(__name__)
