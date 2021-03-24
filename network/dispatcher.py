from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)


class Operator:
    def __init__(self):
        try:
            pass
        except Exception as e_err:
            ml.log(f'error initializing \'{self.__class__.__name__}\'')
            ml.log(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def transfer_files_to_remote():
        try:
            pass
        except Exception as e_err:
            ml.log(f'error transferring files to remote')
            ml.log(e_err.args[0], level=ml.ERROR)
