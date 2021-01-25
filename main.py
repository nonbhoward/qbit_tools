from datetime import datetime
from qbit_tasker import QbitTasker
from time import sleep


def mainloop():
    start_application()
    qbt = QbitTasker()
    while True:
        print('beginning new loop at {}'.format(datetime.now()))
        qbt.begin_queued_searches()
        qbt.parse_completed_searches()
        qbt.check_watched_downloads()
        qbt.transfer_files_to_remote()
        sleep(2)


def start_application():
    pass


mainloop()
