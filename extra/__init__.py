from minimalog.minimal_log import MinimalLog
ml = MinimalLog(__name__)
event = f'importing {__name__}'
ml.log(event)
