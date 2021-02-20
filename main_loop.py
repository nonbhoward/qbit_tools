from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_bot_states import QbitStateManager
ml = MinimalLog()


def main_loop():
    qsm = start_application()
    while True:
        ml.log_event(event=f'new loop starting at {datetime.now()}', announce=True)
        qsm.initiate_and_monitor_searches()
        qsm.increment_loop_count()
        qsm.pause_on_event(qsm.cfg.settings.WAIT_FOR_MAIN_LOOP)


def start_application():
    try:
        ml.log_event('\n\nmain loop has started..')
        ml.log_event(f'TODO, start qbittorrent programatically', level=ml.WARNING)
        return QbitStateManager()
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


main_loop()
