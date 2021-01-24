from configparser import ConfigParser
from json import dumps, loads
from os import getcwd
from os.path import exists
from pathlib2 import Path
from data_src.SECRETS import *
import datetime
import qbittorrentapi


class QbitTasker:
    def __init__(self):
        self.qbit_client_connected = True if self._client_is_connected() else False
        self.data_path = self._get_data_path()
        self.search_config_filename = self._get_search_config_filename()
        self.search_config = self._get_search_config()
        self._connection_time_start = datetime.datetime.now()
        pass

    def begin_queued_searches(self):
        """
        use the data returned from the configuration file to begin searches
        :return:
        """
        searches_to_queue = self._build_search_queue_from_config()

    def check_watched_downloads(self):
        pass

    def parse_completed_searches(self):
        pass

    def transfer_files_to_remote(self):
        pass

    def _build_search_queue_from_config(self) -> dict:
        """
        :return: dict containing search configuration details
        """
        searches_to_queue = dict()
        try:
            for section_header in self.search_config.sections():
                _added = self.search_config[section_header].getboolean('torrent_added')
                _search_finished = self.search_config[section_header].getboolean('search_finished')
                _search_started = self.search_config[section_header].getboolean('search_started')
                _search_timed_out = self.search_config[section_header].getboolean('search_timeout')
                _search_in_progress = self.search_config[section_header].getboolean('search_in_progress')
                _search_queued = self.search_config[section_header].getboolean('search_queued')
                if _added:
                    continue
                if _search_finished:
                    if self._qbit_added_result_by_popularity():
                        self.search_config[section_header]['torrent_added'] = 'yes'
                    continue
                if _search_started and not _search_timed_out:
                    self.search_config[section_header]['search_in_progress'] = 'no'
                    if section_header in self.active_search_ids[section_header]:
                        self.search_config[section_header]['search_in_progress'] = 'yes'
                    continue
                if _search_queued:
                    if isinstance(self._qbit_started_search(section_header), qbittorrentapi.Search):
                        self.search_config[section_header]['search_started'] = 'yes'
                    continue
            with open(self.search_config_filename, 'w') as search_config_file:
                self.search_config.write(search_config_file)
        except KeyError as k_err:
            print(k_err)
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

    def _qbit_added_result_by_popularity(self, section_header: str) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        for result in self.qbt_client.search_results():
            return True
        self._qbit_started_search(section_header)
        return False

    def _qbit_get_search_status_by_id(self, search_id) -> str:
        pass

    def _qbit_started_search(self, section_header: str) -> qbittorrentapi.Search:
        self.active_search_ids = dict()
        try:
            search_term = self._strip_outside(self.search_config[section_header]['search_term'])
            search_job = self.qbt_client.search.start(pattern=section_header,
                                                      plugins='all',
                                                      category='all')
            job_status = search_job.status()
            job_id = job_status.data[0]['id']
            job_state = job_status.data[0]['status']
            job_results_count = job_status.data[0]['total']
        except ConnectionError as c_err:
            print('unable to communicate request to client')
            print(c_err)
        try:
            if job_status == 200:  # search started successfully
                self.search_config[section_header]['search_started'] = 'yes'
                search_id = loads(search_job)
                self.active_search_ids[section_header] = search_id
                return search_job
            elif job_status == 409:  # maximum searches reached
                self.search_config[section_header]['search_started'] = 'no'
                return False
            else:
                raise Exception('unknown reponse from client')
        except KeyError as k_err:
            print('unable to decode json')
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
