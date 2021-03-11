from os import system
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import gethostname
from socket import socket
from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)


class NetProbe:
    def __init__(self):
        ml.log_event(f'initializing \'{self.__class__.__name__}\'')

    @staticmethod
    def get_local_ip_address(alt_method=False) -> str:
        try:
            ml.log_event(f'fetching ip address from local computer')
            if not alt_method:
                s = socket(AF_INET, SOCK_DGRAM)
                s.connect(('10.255.255.255', 1))
                return s.getsockname()[0]
            return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0],
                     s.close()) for s in [socket(AF_INET, SOCK_DGRAM)]][0][1]
        except Exception as e_err:
            print(e_err.args[0])

    @staticmethod
    def ping_response_received_from_(ip_address):
        try:
            ml.log_event(f'pinging ip address at \'{ip_address}\'')
            return system('ping -c 1 ' + ip_address + ' >/dev/null') == 0
        except Exception as e_err:
            print(e_err.args[0])

    @staticmethod
    def transfer_files_to_remote():
        try:
            pass
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)


class LocalServer:
    def __init__(self):
        self.probe = NetProbe()
        self.properties = {
            'host name':    gethostname(),
            'ip address':   self.probe.get_local_ip_address(),
        }


if __name__ == '__main__':
    l_server = LocalServer()
    pass
