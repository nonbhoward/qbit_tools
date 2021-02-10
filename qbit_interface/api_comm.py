from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_interface.config_helper import QbitConfig  # TODO reminder, keep this grayed out
from user_configuration.WEB_API_CREDENTIALS import *
import qbittorrentapi
ml = MinimalLog(__name__)


class QbitApiCaller:
    def __init__(self):
        self.qbit_client = qbittorrentapi.Client('', None, None, None)
        self.qbit_client_connected = True if self.client_is_connected() else False
        if self.qbit_client_connected:
            self.connection_time_start = datetime.now()

    def add_result(self, result, m_key):
        try:
            count_before = self.count_all_local_results()
            ml.log_event(f'local machine has {count_before} stored results before add attempt..')
            self.qbit_client.torrents_add(urls=result[metadata_parser_keys.URL], is_paused=True)
            self.pause_on_event(user_config_parser_keys.WAIT_FOR_SEARCH_RESULT_ADD)
            results_added = self.count_all_local_results() - count_before
            # TODO why does client fail to add so much? async opportunity? bad results? dig into api code perhaps
            if results_added > 0:  # successful add
                self._metadata_parser_write_to_metadata_config_file(result)
                search_detail_parser_at_active_header[search_parser_keys.RESULTS_ADDED_COUNT] = \
                    str(int(search_detail_parser_at_active_header[search_parser_keys.RESULTS_ADDED_COUNT]))
                return
            ml.log_event('client failed to add \'{}\''.format(result[metadata_parser_keys.NAME]), level=ml.WARNING)
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def client_is_connected(self) -> bool:
        ml.log_event('connect to client', event_completed=False)
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                ml.log_event(f'connect to client with.. \n\n\tclient app version {app_version} \n\t'
                             f'web api version {web_api_version}\n\n', event_completed=True)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def count_all_local_results(self) -> int:
        try:
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            ml.log_event(f'counted {local_result_count} existing local results')
            return local_result_count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def create_search_job(self, pattern, plugins, category) -> tuple:
        try:
            job = self.qbit_client.search.start(pattern, plugins, category)
            assert job is not None, 'bad search job, fix it or handle it'
            status = job.status()
            state = status.data[0]['status']
            sid = str(status.data[0]['id'])
            count = status.data[0]['total']
            ml.log_event('qbit client created search job for \'{}\''.format(pattern))
            return job, status, state, sid, count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_search_results(self, search_id):
        try:
            results = self.qbit_client.search_results(search_id)
            assert results is not None, 'bad results, fix it or handle it'
            return results
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_search_status(self, search_id) -> str:
        try:
            ml.log_event(f'check search status for search id \'{search_id}\'')
            search_status = self.qbit_client.search_status(search_id=search_id)
            assert search_status is not None, 'bad search status, fix it or handle it'
            search_status = search_status.data[0]['status']
            assert search_status is not None, 'bad search status attribute, fix it or handle it'
            return search_status
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    qba = QbitApiCaller()
    pass
