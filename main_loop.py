from configuration_reader import get_user_configuration
from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_bot import QbitTasker
ml = MinimalLog()
user_configuration = get_user_configuration()


def mainloop():
    try:
        ml.log_event('main loop has started..')
        start_application()
        qbit = QbitTasker(user_configuration=user_configuration,
                          debug=True)
        while True:
            ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
            qbit.initiate_and_monitor_searches()
            qbit.increment_loop_count()
            ml.log_event('main loop has ended, {} total loops..'.format(qbit.main_loop_count))
            wait_between_main_loops = user_configuration.hardcoded.keys.user_config_keyring.WAIT_MAIN_LOOP
            # TODO could probably embed this in something instead of accessing directly, maybe later
            ml.log_event('current connection to qbittorrent api was started at {}'.format(qbit._connection_time_start))
            ml.log_event('when in doubt, compare parsed file keys with config reader string values', level=ml.WARNING)
            ml.log_event('when in doubt, compare parsed file keys with config reader string values', level=ml.WARNING)
            qbit.pause_on_event(wait_between_main_loops)
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def start_application():
    pass


mainloop()
