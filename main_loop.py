from data_src.configuration_reader import UserSettings as bKey
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_bot import QbitTasker
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
        start_application()
        _wait_for_application_start()
        pass


def _application_started() -> bool:
    return False


def _wait_for_application_start():
    pass


mainloop()
