from datetime import datetime
from minimalog.minimal_log import MinimalLog
from os import getcwd as cwd, listdir as ls
from os.path import exists
from pathlib import Path
from state_machine import QbitStateMachine
from core.interface import QConf
from core.interface import pause_on_event
from subprocess import run as launch
from sys import platform
ml = MinimalLog()
u_key = QConf.get_keyring_for_(settings=True)


def main_loop():
    ml.log('main loop has started..', announcement=True)
    qbit_state_machine = initialize_and_return_state_machine()
    while True:
        ml.log(f'new loop starting at {datetime.now()}', announcement=True)
        qbit_state_machine.initiate_and_monitor_searches()
        qbit_state_machine.increment_main_loop_count()
        pause_on_event(u_key.WAIT_FOR_MAIN_LOOP)


def initialize_and_return_state_machine():
    try:
        return QbitStateMachine()
    except Exception as e_err:
        ml.log(f'error starting application and fetching state machine')
        ml.log(e_err.args[0], level=ml.ERROR)


def supported_os() -> bool:
    try:
        supported = ['linux', 'win32']
        if platform in supported:
            return True
        return False
    except Exception as e_err:
        ml.log(f'error checking if operating system supported')
        ml.log(e_err.args[0], level=ml.ERROR)


main_loop()
