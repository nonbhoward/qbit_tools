from qbit_tasker import QbitTasker
from time import sleep


def mainloop():
    qbt = QbitTasker()
    while True:
        qbt.begin_queued_searches()
        qbt.parse_completed_searches()
        qbt.check_watched_downloads()
        qbt.transfer_files_to_remote()
        exit()
        sleep(60)
        pass


mainloop()
