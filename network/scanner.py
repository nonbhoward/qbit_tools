from minimalog.minimal_log import MinimalLog
from os import system
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
ml = MinimalLog(__name__)


class NetworkScanner:
    def __init__(self):
        ml.log(f'initializing \'{self.__class__.__name__}\'')

    @staticmethod
    def get_local_ip_address() -> str:
        try:
            ml.log(f'fetching ip address from local computer')
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'trying fallback method')
            try:
                return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0],
                         s.close()) for s in [socket(AF_INET, SOCK_DGRAM)]][0][1]
            except Exception as e_err:
                ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def ping_response_received_from_(ip_address) -> bool:
        try:
            ml.log(f'pinging ip address at \'{ip_address}\'')
            return system('ping -c 1 ' + ip_address + ' >/dev/null') == 0
        except Exception as e_err:
            print(e_err.args[0])
