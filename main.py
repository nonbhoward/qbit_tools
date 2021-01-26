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
        event = 'new loop starting at {}'.format(datetime.now())
        ml.log_event(event=event, announce=True)
        qbit.initiate_and_monitor_searches()
        sleep(5)


def start_application():
    pass


mainloop()
