from minimalog.minimal_log import MinimalLog
from pathlib import Path
ml = MinimalLog(__name__)


class MediaBox:
    def __init__(self):
        try:
            self.contents = {}
        except Exception as e_err:
            ml.log_event(f'error initializing \'{self.__class__.__name__}\'')
            ml.log_event(e_err.args[0], level=ml.ERROR)

    @staticmethod
    def get_content_from_sender():
        try:
            pass
        except Exception as e_err:
            ml.log_event(f'error getting content from sender')
            ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    b = MediaBox()
    pass
