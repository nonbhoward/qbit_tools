from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_bot_states import QbitStateManager
ml = MinimalLog()


def main_loop():
    try:
        ml.log_event('main loop has started..')
        start_application()
        qsm = QbitStateManager()
        while True:
            ml.log_event(event='new loop starting at {}'.format(datetime.now(), announce=True))
            qsm.initiate_and_monitor_searches()
            qsm.increment_loop_count()
            wait_between_main_loops = qsm.config.hardcoded.keys.user_config_parser_keyring.WAIT_FOR_MAIN_LOOP
            qsm.pause_on_event(wait_between_main_loops)
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def start_application():
    pass


main_loop()
