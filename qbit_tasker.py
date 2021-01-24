from configparser import ConfigParser
from os import getcwd
from os.path import exists
from pathlib2 import Path
from data_src.SECRETS import *
import datetime
import qbittorrentapi


class QbitTasker:
    def __init__(self):
        self.qbt_client = qbittorrentapi.Client(host='127.0.0.1:8080',
                                                username=USER,
                                                password=PASS)
        self.data_path = self._get_data_path()
        self.search_config_filename = self._get_search_config_filename()
        self.search_config = self._get_search_config()
        self._connect_to_web_ui()
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
                _search_queued = self.search_config[section_header].getboolean('search_queued')
                if _added:
                    continue
                if _search_finished:
                    if self._qbit_added_result_by_popularity():
                        self.search_config[section_header]['torrent_added'] = 'yes'
            with open(self.search_config_filename, 'w') as search_config_file:
                self.search_config.write(search_config_file)
        except KeyError as k_err:
            print(k_err)
            pass

    def _connect_to_web_ui(self):
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

    def _qbit_added_result_by_popularity(self) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """


    def _qbit_get_search_status_by_id(self, search_id) -> str:
        self.qbi

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
