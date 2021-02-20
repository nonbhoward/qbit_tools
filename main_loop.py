from datetime import datetime
from minimalog.minimal_log import MinimalLog
from os import getcwd as cwd, listdir as ls
from os.path import exists
from pathlib import Path
from qbit_bot_states import QbitStateManager
from subprocess import run as launch
from sys import platform
ml = MinimalLog()


def main_loop():
    ml.log_event('\n\nmain loop has started..', announce=True)
    qsm = start_application_and_return_state_machine()
    while True:
        ml.log_event(event=f'new loop starting at {datetime.now()}', announce=True)
        qsm.initiate_and_monitor_searches()
        qsm.increment_loop_count()
        qsm.pause_on_event(qsm.cfg.settings.WAIT_FOR_MAIN_LOOP)


def application_is_running(app_path: Path) -> bool:
    try:
        # FIXME
        return False
        ps_path = '/proc'
        app_name, ps = str(app_path).split('/')[-1], ls(ps_path)
        if app_name in ps:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def start_application_and_return_state_machine():
    try:
        # TODO qbit could be in other locations.. /opt etc
        std_path, app_name = ['usr', 'bin'], 'qbittorrent'
        app = Path(Path(cwd()).root).joinpath(*std_path, app_name)
        if not supported_os():
            ml.log_event('unsupported OS', level=ml.ERROR)
            exit()
        if application_is_running(app):
            return QbitStateManager()
        if not exists(app):
            ml.log_event('install qbittorrent', level=ml.ERROR)
            exit()
        launch(app)
        return QbitStateManager()
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


def supported_os() -> bool:
    try:
        nightmare_hellscape = 'win32'
        if nightmare_hellscape in platform:
            print('self-harm detected, program ending')
            exit()
        supported = ['linux']
        if platform in supported:
            return True
        return False
    except Exception as e_err:
        ml.log_event(e_err, level=ml.ERROR)


main_loop()
