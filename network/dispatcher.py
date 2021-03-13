from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)


class Operator:
    def __init__(self):
        try:
            pass
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'')
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def transfer_files_to_remote():
        try:
            pass
        except Exception as e_err:
            ml.log_event(f'error transferring files to remote')
            ml.log_event(e_err.args[0], level=ml.ERROR)
