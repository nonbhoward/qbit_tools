from socket import AF_INET
from socket import SOCK_DGRAM
from socket import gethostbyname
from socket import gethostname
from socket import socket
from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)


class NetProbe:
    def __init__(self):
        pass

    @staticmethod
    def get_local_ip_address() -> str:
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
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
            'ip address':   self.probe.get_local_ip_address()
        }


if __name__ == '__main__':
    l_server = LocalServer()
    pass
