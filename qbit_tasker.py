from configparser import ConfigParser
from data_src.SECRETS import *
from minimalog.minimal_log import MinimalLog
from os import getcwd
from os.path import exists
from pathlib2 import Path
from re import findall
from time import sleep
import datetime
import qbittorrentapi
RESET, QUEUED, STARTING, RUNNING, STOPPED, CONCLUDED = 'Reset', 'Queued', 'Starting', 'Running', 'Stopped', 'Concluded'
RESULT_QTY_PER_SEARCH = 15
YES, NO, EMPTY = 'yes', 'no', ''


class QbitTasker:
    def __init__(self):
        ml.log_event('initialize {}'.format(self.__class__), event_completed=False)
        self.qbit_client_connected = True if self._client_is_connected() else False
        self.data_path = self._get_data_path()
        self.search_config_filename = self._get_search_config_filename()
        self.search_cp = self._get_search_cp()
        self._connection_time_start = datetime.datetime.now()
        self._qbit_reset_search_ids()
        self.active_search_ids = dict()
        ml.log_event('initialize {}'.format(self.__class__), event_completed=True)

    def initiate_and_monitor_searches(self):
        ml.log_event('check search status..')
        try:
            for section_header in self.search_cp.sections():
                _search_queued, _search_running, _search_stopped, _search_concluded = self._get_search_states(section_header)
                sleep(5)
                if _search_queued:
                    if not self._qbit_search_queue_full():
                        self._qbit_start_search(section_header)
                elif _search_running:
                    search_state = self._qbit_get_search_status(section_header)
                    if search_state is None:
                        self._update_search_states(section_header, RESET)
                    elif STOPPED in search_state:
                        self._update_search_states(section_header, STOPPED)
                elif _search_stopped:
                    filtered_results, filtered_results_count = self._qbit_filter_results(section_header)
                    if filtered_results is not None and filtered_results_count > 0:
                        self._qbit_add_results_by_popularity(section_header, filtered_results)
                    else:
                        self._update_search_states(section_header, QUEUED)
                elif _search_concluded:
                    pass
                else:
                    self._update_search_states(section_header, QUEUED)
            try:
                with open(self.search_config_filename, 'w') as search_config_file:
                    ml.log_event('writing events to file: {}'.format(search_config_file), event_completed=False)
                    self.search_cp.write(search_config_file)
                ml.log_event('writing events to file: {}'.format(search_config_file), event_completed=True)
            except OSError as o_err:
                ml.log_event(o_err)
        except KeyError as k_err:
            ml.log_event(k_err)

    def transfer_files_to_remote(self):
        pass

    def _client_is_connected(self) -> bool:
        """
        connect to the client, fetch check app version and web api version
        :return: bool, true if able to populate all data successfully
        """
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event(r_err)

    @staticmethod
    def _config_file_has_sections(config_parser) -> bool:
        try:
            config_file_section_count = len(config_parser.sections())
            if config_file_section_count > 0:
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event('{}: configuration file has no sections'.format(r_err))

    def _config_get_search_term(self, section_header):
        try:
            search_term = self.search_cp[section_header]['search_term']
            return search_term
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_increment_search_try_counter(self, section_header):
        try:
            search_try_count = int(self.search_cp[section_header]['search_attempts'])
            self.search_cp[section_header]['search_attempts'] = str(search_try_count + 1)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_set_search_id_as_active(self, section_header, search_id):
        try:
            self.search_cp[section_header]['search_id'] = search_id
            self.active_search_ids[section_header] = search_id
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_set_search_id_as_inactive(self, section_header, search_id):
        try:
            if search_id == self.active_search_ids[section_header]:
                self.search_cp[section_header]['search_id'] = str(0)
                del self.active_search_ids[section_header]
        except KeyError as k_err:
            ml.log_event(k_err)

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
            ml.log_event(o_err)

    @staticmethod
    def _get_project_path() -> Path:
        try:
            return Path(getcwd())
        except OSError as o_err:
            ml.log_event(o_err)

    def _get_search_cp(self) -> ConfigParser:
        """
        :return: ConfigParser containing configuration details
        """
        try:
            if exists(self.search_config_filename):
                cp = ConfigParser()
                cp.read(filenames=self.search_config_filename)
                if self._config_file_has_sections(cp):
                    return cp
                ml.log_event('warning, configuration file has no sections')
                return cp
            else:
                raise FileNotFoundError('search configuration does not exist')
        except FileNotFoundError as f_err:
            ml.log_event(f_err)

    def _get_search_config_filename(self) -> str:
        """
        :return: built path from hardcoded filename
        """
        try:
            search_config_filename = Path(self.data_path, 'searches.cfg')
            return search_config_filename
        except OSError as o_err:
            ml.log_event(o_err)

    def _get_search_states(self, section_header) -> tuple:
        """
        :param section_header: the section of the configuration file to read
        :return: search states
        """
        try:
            ml.log_event('get search state for section: {}'.format(section_header))
            self.search_cp[section_header]['last_read'] = str(datetime.datetime.now())
            _search_queued = self.search_cp[section_header].getboolean('search_queued')
            _search_running = self.search_cp[section_header].getboolean('search_running')
            _search_stopped = self.search_cp[section_header].getboolean('search_stopped')
            _search_concluded = self.search_cp[section_header].getboolean('search_concluded')
            ml.log_event('search state for {}: \nqueued: {}\nrunning: {}\nfinished: {}\nadded: {}'.format(
                section_header, _search_queued, _search_running, _search_stopped, _search_concluded))
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except KeyError as k_err:
            ml.log_event(k_err)

    @staticmethod
    def _pattern_matches(search_pattern, file_name) -> bool:
        try:
            pattern_match = findall(search_pattern, file_name)
            if pattern_match:
                return True
            return False
        except RuntimeError as r_err:
            event = 'error with regex, search_pattern: {} file_name: {}'.format(search_pattern, file_name)
            ml.log_event(str(r_err) + event)

    def _qbit_add_results_by_popularity(self, section_header: str, filtered_results) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        search_id = self.active_search_ids.get(section_header, '')
        if search_id == '':
            self._update_search_states(section_header, QUEUED)
            return False
        most_popular_results = self._qbit_get_most_popular_results(filtered_results)
        count_before = self._qbit_count_all_torrents()
        if most_popular_results is not None:
            for result in most_popular_results:
                result_url, result_seeds = result['fileUrl'], result['nbSeeders']
                minimum_seeds = int(self.search_cp[section_header]['minimum_seeds'])
                if result_seeds > minimum_seeds:
                    self.qbit_client.torrents_add(urls=result_url, is_paused=True)
            self._config_set_search_id_as_inactive(section_header, search_id)
            count_after = self._qbit_count_all_torrents()
            results_added = count_after - count_before
            self.search_cp[section_header]['results_added'] = str(int(
                self.search_cp[section_header]['results_added']) + results_added)
            if self._qbit_search_yielded_required_results(section_header):
                self._update_search_states(section_header, CONCLUDED)

    def _qbit_all_searches_concluded(self) -> bool:
        # TODO would be nice to exit if all jobs exceed set limits
        try:
            concluded = list()
            for section in self.search_cp.sections():
                for key in self.search_cp[section]:
                    if key == 'search_concluded':
                        search_concluded = self.search_cp[section].getboolean(key)
                        concluded.append(search_concluded)
            if all(concluded):
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err)

    def _qbit_count_all_torrents(self) -> int:
        try:
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            return local_result_count
        except RuntimeError as r_err:
            ml.log_event(r_err)

    def _qbit_create_search_job(self, pattern, plugins, category) -> tuple:
        try:
            _job = self.qbit_client.search.start(pattern, plugins, category)
            _status = _job.status()
            _state = _status.data[0]['status']
            _id = str(_status.data[0]['id'])
            _count = _status.data[0]['total']
            return _job, _status, _state, _id, _count
        except ConnectionError as c_err:
            ml.log_event(c_err)

    def _qbit_filter_results(self, section_header: str):
        filtered_results_count, filtered_results, results = 0, list(), self._qbit_get_search_results(section_header)
        if results is None:
            return None, 0
        for result in results['results']:
            file_name = result['fileName']
            search_pattern = self.search_cp[section_header]['search_filter']
            if self._pattern_matches(search_pattern, file_name):
                filtered_results.append(result)
                filtered_results_count += 1
        return filtered_results, filtered_results_count

    def _qbit_get_active_search_id(self, section_header) -> str:
        try:
            active_search_id = self.active_search_ids.get(section_header)
            return active_search_id
        except KeyError as k_err:
            ml.log_event(k_err)

    @staticmethod
    def _qbit_get_most_popular_results(filtered_results, result_count=RESULT_QTY_PER_SEARCH) -> list:
        most_popular_results = list()
        if len(filtered_results) < result_count:
            result_count = len(filtered_results)
        try:
            popularity_sorted_list = sorted(filtered_results, key=lambda k: k['nbSeeders'], reverse=True)
            for index in range(result_count):
                most_popular_results.append(popularity_sorted_list[index])
            return most_popular_results
        except IndexError as i_err:
            ml.log_event(i_err)

    def _qbit_get_search_results(self, section_header):
        try:
            search_id = self._qbit_get_active_search_id(section_header)
            if search_id is not None and search_id is not EMPTY:  #TODO 'is not' is known bad syntax, testing
                results = self.qbit_client.search_results(search_id)
                return results
            return None
        except KeyError as k_err:
            ml.log_event(k_err)

    def _qbit_get_search_status(self, section_header) -> str:
        """
        :param section_header: the section to read
        :return: the status of the search at search_id
        """
        try:
            ml.log_event('checking search status for section: {}'.format(section_header))
            search_id, search_status = self.search_cp[section_header]['search_id'], None
            if not search_id == '':
                ml.log_event('getting search status for section: {} with search_id: {}'.format(
                    section_header, search_id))
                if search_id in self.active_search_ids.values():
                    ongoing_search = self.qbit_client.search_status(search_id=search_id)
                    search_status = ongoing_search.data[0]['status']
            ml.log_event('search status for section: {} is {}'.format(section_header, search_status))
            return search_status
        except ConnectionError as c_err:
            event = 'unable to process search for section: {}'.format(section_header)
            ml.log_event(event)

    def _qbit_reset_search_ids(self):
        """
        upon initialization of new object, delete expired search_ids
        :return: None  # TODO should i return success?
        """
        try:
            for section_header in self.search_cp.sections():
                ml.log_event('reset search_id for section: {}'.format(section_header))
                self._update_search_states(section_header, RESET)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _qbit_search_queue_full(self) -> bool:
        try:
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                return False
            return True
        except RuntimeError as r_err:
            ml.log_event(r_err)

    def _qbit_search_yielded_required_results(self, section_header) -> bool:
        """
        decides if search is ready to be marked as completed (ADDED)
        :param section_header: configuration key
        :return: bool, search completed
        """
        try:
            attempted = int(self.search_cp[section_header]['search_attempts'])
            maximum_attempts = int(self.search_cp[section_header]['maximum_search_attempts'])
            added = int(self.search_cp[section_header]['results_added'])
            required = int(self.search_cp[section_header]['results_required'])
            if added > required or attempted > maximum_attempts:
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err)

    def _qbit_start_search(self, section_header: str):
        try:
            search_term = self._config_get_search_term(section_header)
            search_job, search_status, search_state, search_id, search_count = \
                self._qbit_create_search_job(search_term, 'all', 'all')
            if RUNNING in search_state:  # search started successfully
                self._config_set_search_id_as_active(section_header, search_id)
                self._update_search_states(section_header, STARTING)
        except KeyError as k_err:
            ml.log_event('{}: unable to process search job'.format(k_err))

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
            ml.log_event(r_err)

    def _update_search_states(self, section_header, job_state):
        try:
            if job_state == RESET or job_state == QUEUED:
                self.search_cp.remove_section('search_id')
                self.search_cp[section_header]['search_queued'] = YES
                self.search_cp[section_header]['search_running'] = NO
                self.search_cp[section_header]['search_stopped'] = NO
                self.search_cp[section_header]['search_concluded'] = NO
            elif job_state == STARTING:
                self.search_cp[section_header]['search_queued'] = NO
                self.search_cp[section_header]['search_running'] = YES
                self.search_cp[section_header]['search_stopped'] = NO
                self.search_cp[section_header]['search_concluded'] = NO
                self._config_increment_search_try_counter(section_header)
            elif job_state == STOPPED:
                self.search_cp[section_header]['search_queued'] = NO
                self.search_cp[section_header]['search_running'] = NO
                self.search_cp[section_header]['search_stopped'] = YES
                self.search_cp[section_header]['search_concluded'] = NO
            elif job_state == CONCLUDED:
                self.search_cp[section_header]['search_queued'] = NO
                self.search_cp[section_header]['search_running'] = NO
                self.search_cp[section_header]['search_stopped'] = NO
                self.search_cp[section_header]['search_concluded'] = YES
            else:
                pass
            self.search_cp[section_header]['last_write'] = str(datetime.datetime.now())
        except KeyError as k_err:
            ml.log_event(k_err)


if __name__ == '__main__':
    ml = MinimalLog()
else:
    ml = MinimalLog(__name__)
