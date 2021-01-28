from data_src.configuration_file_reader import UserSettings as bKey
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_tasker import QbitTasker
ml = MinimalLog()
behavior_keys = bKey()


def mainloop():
    ml.log_event('main loop has started..', announce=True)
    start_application()
    qbit = QbitTasker()
    while True:
        ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
        qbit.initiate_and_monitor_searches()
        qbit.pause_on_event(behavior_keys.wait_between_main_loops)


def start_application():
    while not _application_started():


mainloop()
