from minimalog.minimal_log import MinimalLog
ml = MinimalLog()


class LogManager:
    def __init__(self):
        pass

    @staticmethod
    def todo():
        try:
            pass
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)