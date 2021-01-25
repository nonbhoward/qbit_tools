from configparser import ConfigParser
from data_src.SECRETS import *
from os import getcwd
from pathlib2 import Path
from re import findall
from time import sleep
import datetime
import qbittorrentapi
RUNNING, STOPPED = 'Running', 'Stopped'


class QbitTasker:
    def __init__(self):
        self.qbit_client_connected = True if self._client_is_connected() else False
        self.data_path = self._get_data_path()
        self.search_config_filename = self._get_search_config_filename()
        self.search_config = self._get_search_config()
        self._connection_time_start = datetime.datetime.now()
        self._qbit_reset_search_ids()
        self.active_search_ids = dict()

    def initiate_and_monitor_searches(self):
        try:
            sleep(15)
            for section_header in self.search_config.sections():
                self.search_config[section_header]['last_accessed'] = str(datetime.datetime.now())
                _search_queued = self.search_config[section_header].getboolean('search_queued')
                _search_running = self.search_config[section_header].getboolean('search_running')
                _search_finished = self.search_config[section_header].getboolean('search_finished')
                _result_added = self.search_config[section_header].getboolean('result_added')
                if _search_queued:
                    queue_full = self._qbit_search_queue_full()
                    if not queue_full:
                        self._qbit_start_search(section_header)
                        continue
                if _search_running:
                    search_status = self._qbit_get_search_status(section_header)
                    if search_status is None:
                        self.search_config[section_header]['search_running'] = 'no'
                    elif STOPPED in search_status:
                        self.search_config[section_header]['search_running'] = 'no'
                        self.search_config[section_header]['search_finished'] = 'yes'
                    continue
                if _result_added:
                    continue
                if _search_finished:
                    filtered_results = self._qbit_filter_results(section_header)
                    if filtered_results is not None:
                        if len(filtered_results) > 0:
                            if self._qbit_added_result_by_popularity(section_header, filtered_results):
                                self.search_config[section_header]['result_added'] = 'yes'
                    else:
                        self.search_config[section_header]['search_finished'] = 'no'
                        self.search_config[section_header]['search_queued'] = 'yes'
                    continue
                else:
                    self.search_config[section_header]['search_queued'] = 'yes'
            try:
                with open(self.search_config_filename, 'w') as search_config_file:
                    self.search_config.write(search_config_file)
            except OSError as o_err:
                print(o_err)
        except KeyError as k_err:
            print(k_err)
            pass

    def check_watched_downloads(self):
        pass

    def parse_completed_searches(self):
        pass

    def transfer_files_to_remote(self):
        pass

    def _client_is_connected(self) -> bool:
        """
        connect to the client, fetch check app version and web api version
        :return: bool, true if able to populate all data successfully
        """
        try:
            self.qbt_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbt_client.app_version
            web_api_version = self.qbt_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                return True
            return False
        except RuntimeError as r_err:
            print(r_err)
            pass

    @staticmethod
    def _get_data_directory_name() -> str:
        return 'data_src'

    def _get_data_path(self) -> Path:
        """
        :return: data path as path object
        """
        try:
            project_path = self._get_project_path()
            data_path = Path(project_path, self._get_data_directory_name())
            return data_path
        except OSError as o_err:
            print(o_err)
            pass

    @staticmethod
    def _get_project_path() -> Path:
        try:
            return Path(getcwd())
        except OSError as o_err:
            print(o_err)
            pass

    def _get_search_config(self) -> ConfigParser:
        """
        :return: ConfigParser containing configuration details
        """
        try:
            cp = ConfigParser()
            cp.read(filenames=self.search_config_filename)
            return cp
        except FileNotFoundError as f_err:
            print(f_err)
            pass

    def _get_search_config_filename(self) -> str:
        """
        :return: built path from hardcoded filename
        """
        try:
            search_config_filename = Path(self.data_path, 'searches.cfg')
            return search_config_filename
        except OSError as o_err:
            print(o_err)
            pass

    def _qbit_added_result_by_popularity(self, section_header: str, filtered_results) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        search_id = self.active_search_ids.get(section_header, '')
        if search_id == '':
            self.search_config[section_header]['search_queued'] = 'yes'
            self.search_config[section_header]['search_finished'] = 'no'
            return False
        most_popular_results = self._qbit_get_most_popular_results(filtered_results)
        if most_popular_results is not None:
            for result in most_popular_results:
                result_url = result['fileUrl']
                self.qbt_client.torrents_add(urls=result_url, is_paused=True)
            return True
        return False

    def _qbit_filter_results(self, section_header: str):
        filtered_results = list()
        search_id = self._qbit_get_active_search_id(section_header)
        if search_id is not None and not search_id == '':
            results = self.qbt_client.search_results(search_id=search_id)
            for result in results['results']:
                file_name = result['fileName']
                search_pattern = self.search_config[section_header]['search_filter']
                pattern_match = findall(search_pattern, file_name)
                if pattern_match:
                    filtered_results.append(result)
            for result in results:
                search_filter = self.search_config[section_header]['search_filter']
                # re.search with search_filter onto result name, delete non-matches
            return filtered_results
        return None

    def _qbit_get_active_search_id(self, section_header) -> str:
        try:
            active_search_id = self.active_search_ids.get(section_header)
            return active_search_id
        except KeyError as k_err:
            print(k_err)

    @staticmethod
    def _qbit_get_most_popular_results(filtered_results, result_count=3) -> list:
        most_popular_results = list()
        if len(filtered_results) < result_count:
            result_count = len(filtered_results)
        try:
            popularity_sorted_list = sorted(filtered_results, key=lambda k: k['nbSeeders'], reverse=True)
            for index in range(result_count):
                most_popular_results.append(popularity_sorted_list[index])
            return most_popular_results
        except IndexError as i_err:
            print(i_err)

    def _qbit_get_search_status(self, section_header) -> str:
        try:
            search_id = self._strip_outside(self.search_config[section_header]['search_id'])
            job_state = None
            if not search_id == '':
                job_status = self.qbt_client.search_status(search_id=search_id)
                job_state = job_status.data[0]['status']
            return job_state
        except ConnectionError as c_err:
            print('unable to process search status')
            print(c_err)

    def _qbit_reset_search_ids(self):
        try:
            for section_header in self.search_config.sections():
                self.search_config[section_header]['search_id'] = ''
        except KeyError as k_err:
            print(k_err)

    def _qbit_search_queue_full(self) -> bool:
        try:
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                return False
            return True
        except RuntimeError as r_err:
            print(r_err)

    def _qbit_start_search(self, section_header: str):
        try:
            search_term = self._strip_outside(self.search_config[section_header]['search_term'])
            search_job = self.qbt_client.search.start(pattern=search_term, plugins='all', category='all')
            job_status = search_job.status()
            job_id = str(job_status.data[0]['id'])
            self.search_config[section_header]['search_id'] = job_id
            self.active_search_ids[section_header] = job_id
            job_state = job_status.data[0]['status']
            # job_results_count = job_status.data[0]['total']
            if RUNNING in job_state:  # search started successfully
                search_try_count = int(self.search_config[section_header]['search_attempts'])
                self.search_config[section_header]['search_attempts'] = str(search_try_count + 1)
                self.search_config[section_header]['search_queued'] = 'no'
                self.search_config[section_header]['search_running'] = 'yes'
                self.search_config[section_header]['search_finished'] = 'no'
                self.search_config[section_header]['result_added'] = 'no'
                self.active_search_ids[section_header] = job_id
        except KeyError as k_err:
            print('unable to process search job')
            print(k_err)

    @staticmethod
    def _strip_outside(str_to_strip: str) -> str:
        """
        :param str_to_strip: raw string with quotes
        :return: string with quotes stripped
        """
        try:
            stripped_string = str_to_strip.replace('\'', '')
            return stripped_string
        except RuntimeError as r_err:
            print(r_err)
            pass
