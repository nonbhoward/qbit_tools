from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_tasker import QbitTasker
from time import sleep
ml = MinimalLog()


def mainloop():
    ml.log_event('main loop has started..')
    start_application()
    qbit = QbitTasker()
    while True:
        ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
        qbit.initiate_and_monitor_searches()
        sleep(1)


def start_application():
    pass


mainloop()
