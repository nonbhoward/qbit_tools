from data_src.CONSTANTS import *
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_tasker import QbitTasker
ml = MinimalLog()


def mainloop():
    ml.log_event('main loop has started..')
    start_application()
    qbit = QbitTasker()
    while True:
        ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
        qbit.initiate_and_monitor_searches()
        # if qbit._config_file_has_sections(qbit.result_parser):
        #     result_dict = qbit._results_fetch_all_data()
        qbit.pause_on_event(LOOPS)


def start_application():
    pass


mainloop()
