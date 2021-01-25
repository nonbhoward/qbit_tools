from datetime import datetime
from qbit_tasker import QbitTasker
from time import sleep


def mainloop():
    start_application()
    qbt = QbitTasker()
    while True:
        print('beginning new loop at {}'.format(datetime.now()))
        qbt.initiate_and_monitor_searches()
        sleep(5)


def start_application():
    pass


mainloop()
