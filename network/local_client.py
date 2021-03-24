from minimalog.minimal_log import MinimalLog
ml = MinimalLog()


class LocalClient:
    def __init__(self):
        self.todo = 'todo'

    def request_queue_from_(self):
        try:
            print(f'request queue \'{self.todo}\'')
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    lc = LocalClient()
    pass
