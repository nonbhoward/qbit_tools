from configuration_reader import get_user_configuration
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_bot import QbitTasker
ml = MinimalLog()
user_configuration = get_user_configuration()


def mainloop():
    ml.log_event('main loop has started..')
    start_application()
    qbit = QbitTasker(user_configuration)
    while True:
        ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
        qbit.initiate_and_monitor_searches()
        qbit.increment_loop_count()
        ml.log_event('main loop has ended, {} total loops..'.format(qbit.main_loop_count))
        main_loop_wait = user_configuration.hardcoded.keys.pause_keys.MAIN_LOOP
        qbit.pause_on_event(main_loop_wait)


def start_application():
    pass


mainloop()
