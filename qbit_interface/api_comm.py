from datetime import datetime
from minimalog.minimal_log import MinimalLog
from state_machine_interface import regex_matches
from qbittorrentapi.search import SearchStatusesList
from user_configuration.WEB_API_CREDENTIALS import *
import qbittorrentapi
ml = MinimalLog(__name__)


class QbitApiCaller:
    def __init__(self):
        self.qbit_client = qbittorrentapi.Client('', None, None, None)
        self.qbit_client_connected = True if self.client_is_connected() else False
        if self.qbit_client_connected:
            self.dump_surface_client()
            self.connection_time_start = datetime.now()

    def add_result(self):
        pass  # TODO write into this function?

    def client_is_connected(self) -> bool:
        ml.log_event('connect to client', event_completed=False)
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                ml.log_event('connect to client', event_completed=True)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def count_all_local_results(self) -> int:
        try:
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            ml.log_event(f'counted {local_result_count} existing local results')
            return local_result_count
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def create_search_job(self, pattern, plugins, category) -> tuple:
        try:
            job = self.qbit_client.search.start(pattern, plugins, category)
            assert job is not None, 'bad search job, fix it or handle it'
            status = job.status()
            state = status.data[0]['status']
            sid = str(status.data[0]['id'])
            count = status.data[0]['total']
            ml.log_event(f'qbit client created search job for \'{pattern}\'')
            return job, status, state, sid, count
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def dump_surface_client(self):
        try:
            core = self.qbit_client
            dump = {
                'app':                  core.app,
                'application':          core.application,
                'host':                 core.host,
                'is_logged_in':         core.is_logged_in,
                'log':                  core.log,
                'port':                 core.port,
                'rss':                  core.rss,
                'search':               core.search,
                'sync':                 core.sync,
                'torrent_categories':   core.torrent_categories,
                'torrent_tags':         core.torrent_tags,
                'torrents':             core.torrents,
                'transfer':             core.transfer,
                'username':             core.username
            }
            for surface_key, surface_attr in dump.items():
                ml.log_event(f'\'{surface_key}\' : \'{surface_attr}\'')
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def get_result_object_from_(self, search_id) -> list:
        try:
            ml.log_event(f'getting search results for search id \'{search_id}\'')
            results = self.qbit_client.search_results(search_id)
            return results
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def get_search_results(self, search_id, filename_regex,
                           metadata_filename_key, use_filename_regex_filter=False) -> list:
        try:
            ml.log_event(f'getting search results for search id \'{search_id}\'')
            results = self.qbit_client.search_results(search_id)
            assert results is not None, 'bad results, fix it or handle it'
            results = results['results']  # TODO do this? or no?
            filtered_results = list()
            if use_filename_regex_filter:
                ml.log_event(f'filtering results using filename regex \'{filename_regex}\'')
                for result in results:
                    filename = result[metadata_filename_key]
                    if regex_matches(filename_regex, filename):
                        filtered_results.append(result)
                assert filtered_results is not None, 'bad filtered results, fix it or handle it'
                results = filtered_results
            return results
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)

    def get_search_status(self, search_id) -> str:
        try:
            ml.log_event(f'check search status for search id \'{search_id}\'')
            search_status = self.qbit_client.search_status(search_id=search_id)
            assert isinstance(search_status, SearchStatusesList), 'bad search status, fix it or handle it'
            # TODO note that search_status.data[n] has attribute 'id', this could be useful for validation
            if len(search_status.data) == 0:
                ml.log_event('search status yielded from expired or null search id, discarding', level=ml.WARNING)
                return None
            search_status = search_status.data[0]['status']
            assert search_status is not None, 'bad search status attribute, fix it or handle it'
            return search_status
        except Exception as e_err:
            ml.log_event(e_err.args[0], level=ml.ERROR)


if __name__ == '__main__':
    qba = QbitApiCaller()
    pass
