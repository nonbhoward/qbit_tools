from minimalog.minimal_log import MinimalLog
from pathlib import Path
ml = MinimalLog(__name__)


class MediaBox:
    def __init__(self, root, types: list, compress=True):
        self.sender_inventory = self.get_content_from_sender(root)
        self.contents = {}

    @staticmethod
    def get_content_from_sender(root: Path):
        try:
            pass
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    b = MediaBox()
    pass
