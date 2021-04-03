from datetime import datetime as dt
from minimalog.minimal_log import MinimalLog
from qbittorrentapi.search import SearchStatusesList
from re import findall
from time import sleep
from user_configuration.WEB_API_CREDENTIALS import *
import qbittorrentapi
ml = MinimalLog(__name__)


class QbitApiCaller:
    def __init__(self):
        event = f'initializing \'{self.__class__.__name__}\''
        try:
            ml.log(event, announcement=True, event_completed=False)
            self.concurrent_searches_allowed = 5
            self.qbit_client = qbittorrentapi.Client('', None, None, None)
            self.qbit_client_connected = True if self.client_is_connected() else False
            if self.qbit_client_connected:
                self.dump_surface_client()
                self.connection_time_start = dt.now()
            ml.log(event, announcement=True, event_completed=True)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def add_result_from_(self, url: str, is_paused: bool):
        event = f'adding result as paused from \'{url}\'' if is_paused else f'adding result from \'{url}\''
        try:
            self.qbit_client.torrents.add(urls=url, is_paused=is_paused)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def client_is_connected(self) -> bool:
        event = f'checking if connected to client'
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                ml.log(f'success connecting to client!')
                return True
            return False
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def create_search_job(self, pattern, plugins, category) -> tuple:
        event = f'creating search job for pattern \'{pattern}\''
        try:
            job = self.qbit_client.search.start(pattern, plugins, category)
            if job is None:
                ex_event = f'fatal, search job for \'{pattern}\' is None'
                ml.log(ex_event, level=ml.ERROR)
                raise ValueError(ex_event)
            count, sid, status = QbitApiCaller.get_search_info_from_(job)
            ml.log(f'qbit client created search job for \'{pattern}\'')
            return count, sid, status
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def dump_surface_client(self):
        event = f'dumping surface client details'
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
                ml.log(f'\'{surface_key}\' : \'{surface_attr}\'')
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def get_connection_time_start(self) -> dt:
        try:
            return self.connection_time_start
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)

    def get_count_of_local_results(self) -> int:
        try:  # TODO move log statements to core interface?
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            ml.log(f'counted {local_result_count} existing local results')
            return local_result_count
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error getting local result count')

    def get_result_object_at_(self, search_id) -> list:
        event = f'getting result object at \'{search_id}\''
        try:
            return self.qbit_client.search_results(search_id)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    @classmethod
    def get_search_info_from_(cls, job) -> tuple:
        event = f'getting search info from \'{job}\''
        try:
            status = job.status()
            search_status = status.data[0]['status']
            search_id = str(status.data[0]['id'])
            search_found_count = status.data[0]['total']
            return search_found_count, search_id, search_status
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def get_search_properties_for_(self, search_id) -> tuple:
        event = f'getting search status for \'{search_id}\''
        search_count, search_status = 0, ''
        try:  # TODO i'd like to clean this up
            search_statuses_list = self.qbit_client.search_status(search_id=search_id)
            if not isinstance(search_statuses_list, SearchStatusesList):
                ex_event = f'bad type for api search status for \'{search_id}\''
                ml.log(ex_event)
                raise ValueError(ex_event)
            search_statuses_list_data = search_statuses_list.data
            for search_status_list_data in search_statuses_list_data:
                if search_id == str(search_status_list_data.id):
                    search_count = str(search_status_list_data.total)
                    search_id = str(search_status_list_data.id)
                    search_status = search_status_list_data.status
                    break
            search_properties = search_count, search_id, search_status
            if search_properties is None:
                ex_event = f'bad search properties for search id \'{search_id}\''
                ml.log(ex_event)
                raise ValueError(ex_event)
            return search_properties
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    def get_search_results(self, search_id, filename_regex,
                           metadata_filename_key, use_filename_regex_filter=False) -> list:
        event = f'getting search results for \'{search_id}\''
        try:
            ml.log(f'getting search results for search id \'{search_id}\'')
            results = self.qbit_client.search_results(search_id)
            assert results is not None, 'bad results, fix it or handle it'
            results = results['results']  # TODO do this? or no?
            filtered_results = list()
            if use_filename_regex_filter:
                ml.log(f'filtering results using filename regex \'{filename_regex}\'')
                for result in results:
                    filename = result[metadata_filename_key]
                    if self.regex_matches(filename_regex, filename):
                        filtered_results.append(result)
                assert filtered_results is not None, 'bad filtered results, fix it or handle it'
                results = filtered_results
            return results
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    @classmethod
    def pause_for_(cls, delay):
        event = f'pausing for seconds : \'{delay}\''
        try:  # FIXME p3, it makes no sense that this is in the qbit api, legacy junk
            sleep(delay)
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')

    @staticmethod
    def regex_matches(filename_regex, filename) -> bool:
        event = f'checking if regex \'{filename_regex}\' matches filename \'{filename}\''
        try:
            regex_match = findall(filename_regex, filename)
            if regex_match:
                ml.log(f'pattern \'{filename_regex}\' matched against filename \'{filename}\'')
                QbitApiCaller.pause_for_(0)  # FIXME this shouldn't be hardcoded
                return True
            return False
        except Exception as e_err:
            ml.log(e_err.args[0], level=ml.ERROR)
            ml.log(f'error {event}')


if __name__ == '__main__':
    qba = QbitApiCaller()
    pass
