from configuration_reader import MAIN_LOOP
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_bot import QbitTasker
ml = MinimalLog()


def mainloop():
    ml.log_event('main loop has started..')
    start_application()
    qbit = QbitTasker()
    while True:
        ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
        qbit.initiate_and_monitor_searches()
        qbit.increment_loop_count()
        ml.log_event('main loop has ended, {} total loops..'.format(qbit.main_loop_count))
        qbit.pause_on_event(MAIN_LOOP)


def start_application():
    pass


mainloop()
