from minimalog.minimal_log import MinimalLog
from network.scanner import NetworkScanner
from socket import gethostname
ml = MinimalLog()


class LocalServer:
    def __init__(self):
        ml.log_event(f'initializing \'{self.__class__.__name__}\'')
        self.todo = 'todo'
        self.probe = NetworkScanner()
        self.properties = {
            'host name':    gethostname(),
            'ip address':   self.probe.get_local_ip_address(),
        }

    def transfer_files_to_remote(self):
        try:
            print(f'transfer files to remote \'{self.todo}\'')
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    ls = LocalServer()
    pass
