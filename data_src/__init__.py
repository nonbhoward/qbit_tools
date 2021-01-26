from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)
event = 'importing {}'.format(__name__)
ml.log_event(event)
