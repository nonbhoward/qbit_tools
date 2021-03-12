from minimalog.minimal_log import MinimalLog
ml = MinimalLog()


class LogManager:
    def __init__(self):
        try:
            pass
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'', level=ml.ERROR)
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def todo():
        try:
            pass
        except Exception as e_err:
            ml.log_event(f'error TODO')
            ml.log_event(e_err.args[0], level=ml.ERROR)
