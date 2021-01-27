from configparser import ConfigParser
from data_src.CONSTANTS import *
from data_src.SECRETS import *
from minimalog.minimal_log import MinimalLog
from os import getcwd
from os.path import exists
from pathlib2 import Path
from re import findall
from time import sleep
import datetime
import qbittorrentapi


class QbitTasker:
    def __init__(self):
        ml.log_event('initialize {}'.format(self.__class__), event_completed=False, announce=True)
        self.qbit_client_connected = True if self._client_is_connected() else False
        self.data_path = self._get_data_path()
        self.search_config_filename, self.result_config_filename, self.behavior_config_filename = \
            self._get_config_filename(SEARCH), self._get_config_filename(RESULT), self._get_config_filename(BEHAVIOR)
        self.search_parser, self.result_parser, self.behavior_parser = \
            self._config_get_parser(SEARCH), self._config_get_parser(RESULT), self._config_get_parser(BEHAVIOR)
        self._connection_time_start = datetime.datetime.now()
        self._reset_search_ids()
        self.active_search_ids, self.active_header = dict(), ''
        ml.log_event('initialize {}'.format(self.__class__), event_completed=True, announce=True)

    def initiate_and_monitor_searches(self):
        try:
            for section_header in self.search_parser.sections():
                self.active_header = section_header
                ml.log_event('monitoring search header {}'.format(self.active_header))
                self._manage_state_updates(self._get_search_state())
            self._config_to_disk()
        except KeyError as k_err:
            ml.log_event(k_err)

    def pause_on_event(self, pause_type):
        try:
            if pause_type == LOOPS:
                sleep(int(self.behavior_parser[DEFAULT]['loop_wait']))
                ml.log_event('waiting {} seconds for loop..'.format(int(self.behavior_parser[DEFAULT]['loop_wait'])))
            elif pause_type == SEARCHES:
                sleep(int(self.behavior_parser[DEFAULT]['search_wait']))
                ml.log_event('waiting {} seconds for search..'.format(int(self.behavior_parser[DEFAULT]['search_wait'])))
            elif pause_type == ADD:
                sleep(int(self.behavior_parser[DEFAULT]['add_wait']))
                ml.log_event('waiting {} seconds for add..'.format(int(self.behavior_parser[DEFAULT]['add_wait'])))
            else:
                sleep(int(self.behavior_parser[DEFAULT]['add_wait']))
        except ValueError as v_err:
            ml.log_event(v_err)

    def transfer_files_to_remote(self):
        pass

    def _add_results_by_popularity(self, filtered_results) -> bool:
        """
        parse the results returned by the search term & filter, attempt to add new result to local stored results
        :return: bool, success or failure of adding new result to local stored results
        """
        ml.log_event('add results by popularity', event_completed=False)
        search_id = self.active_search_ids.get(self.active_header, '')
        search_id_valid = self._id_is_valid(search_id)
        if not search_id_valid:
            ml.log_event('search id for {} is invalid'.format(self.active_header))
            self._update_search_states(QUEUED)
            return False
        most_popular_results = self._get_most_popular_results(filtered_results)
        if most_popular_results is not None:
            ml.log_event('results sorted by popularity for {}'.format(self.active_header))
            for result in most_popular_results:
                minimum_seeds = int(self.search_parser[self.active_header]['minimum_seeds'])
                result_seeds = result['nbSeeders']
                if result_seeds > minimum_seeds:
                    ml.log_event('result {} has {} seeds, attempting to add'.format(result['fileName'], result_seeds))
                    self._qbit_add_result(result)
            self._config_set_search_id_as_inactive(search_id)
            if self._search_yielded_required_results():
                ml.log_event('search {} has concluded, disabling'.format(self.active_header), announce=True)
                self._update_search_states(CONCLUDED)
        ml.log_event('add results by popularity', event_completed=True)

    def _all_searches_concluded(self) -> bool:
        # TODO would be nice to exit if all jobs exceed set limits
        try:
            concluded = list()
            for section in self.search_parser.sections():
                for key in self.search_parser[section]:
                    if key == 'search_concluded':
                        search_concluded = self.search_parser[section].getboolean(key)
                        concluded.append(search_concluded)
            if all(concluded):
                return True
            return False
        except KeyError as k_err:
            ml.log_event(k_err)

    def _client_is_connected(self) -> bool:
        """
        connect to the client, fetch check app version and web api version
        :return: bool, true if able to populate all data successfully
        """
        ml.log_event('connecting to client', event_completed=False)
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                ml.log_event('connecting to client app version {} web api version {}'.format(
                    app_version, web_api_version), event_completed=True)
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event(r_err)

    @staticmethod
    def _config_file_has_sections(config_parser) -> bool:
        ml.log_event('check if config for {} has sections'.format(config_parser), False)
        try:
            config_file_section_count = len(config_parser.sections())
            if config_file_section_count > 0:
                ml.log_event('check if config for {} has sections'.format(config_parser), True)
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event('{}: configuration file has no sections'.format(r_err))

    def _config_get_parser(self, parser_type) -> ConfigParser:
        """
        :return: ConfigParser containing parsed details
        """
        ml.log_event('get parser type {}'.format(parser_type), event_completed=False)
        try:
            if exists(self._get_config_filename(parser_type)):
                cp = ConfigParser()
                cp.read(filenames=self._get_config_filename(parser_type))
                if self._config_file_has_sections(cp):
                    ml.log_event('get parser type {}'.format(parser_type), event_completed=True)
                    return cp
                ml.log_event('warning, configuration file has no sections', level=ml.WARNING)
                return cp
            else:
                raise FileNotFoundError('requested {} configuration does not exist'.format(parser_type))
        except FileNotFoundError as f_err:
            ml.log_event(f_err)

    def _config_get_search_pattern(self) -> str:
        ml.log_event('fetching search term for {}'.format(self.active_header))
        try:
            if 'search_pattern' not in self.search_parser[self.active_header].keys():
                search_pattern = '.*'
                return search_pattern
            search_pattern = self.search_parser[self.active_header]['search_pattern']
            return search_pattern
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_get_search_term(self) -> str:
        ml.log_event('fetching search term for {}'.format(self.active_header))
        try:
            if 'search_term' not in self.search_parser[self.active_header].keys():
                search_term = self.active_header
                return search_term
            search_term = self.search_parser[self.active_header]['search_term']
            return search_term
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_increment_search_try_counter(self):
        ml.log_event('incrementing search try counter')
        try:
            search_try_count = int(self.search_parser[self.active_header]['search_attempts'])
            self.search_parser[self.active_header]['search_attempts'] = str(search_try_count + 1)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_set_search_id_as_active(self, search_id):
        ml.log_event('search id {} set as active'.format(search_id))
        try:
            self.search_parser[self.active_header]['search_id'] = search_id
            self.active_search_ids[self.active_header] = search_id
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_set_search_id_as_inactive(self, search_id):
        ml.log_event('search id {} set as inactive'.format(search_id))
        try:
            if search_id == self.active_search_ids[self.active_header]:
                self.search_parser[self.active_header]['search_id'] = str(0)
                del self.active_search_ids[self.active_header]
        except KeyError as k_err:
            ml.log_event(k_err)

    def _config_to_disk(self):
        ml.log_event('writing parser configurations to disk')
        try:
            parser_data = self._get_parser_data()
            for parser in parser_data:
                ml.log_event('.. {} ..'.format(parser[0]))
                with open(parser[0], 'w') as parser_file:
                    parser[1].write(parser_file)
        except OSError as o_err:
            ml.log_event(o_err)

    def _filter_results(self):
        filtered_results_count, filtered_results, results = 0, list(), self._qbit_get_search_results()
        if results is None:
            return None, 0
        for result in results['results']:
            file_name = result['fileName']
            search_pattern = self._config_get_search_pattern()
            if self._pattern_matches(search_pattern, file_name):
                filtered_results.append(result)
                filtered_results_count += 1
        ml.log_event('{} filtered results found'.format(filtered_results_count))
        return filtered_results, filtered_results_count

    def _get_active_search_ids(self) -> str:
        try:
            active_search_id = self.active_search_ids.get(self.active_header)
            ml.log_event('get active search id {} for {}'.format(active_search_id, self.active_header))
            return active_search_id
        except KeyError as k_err:
            ml.log_event(k_err)

    def _get_config_filename(self, parser_type) -> str:
        """
        :return: built path from hardcoded filename
        """
        ml.log_event('get config file name for parser_type {}'.format(parser_type))
        try:
            if parser_type == SEARCH:
                config_filename = Path(self.data_path, 'searches.cfg')
                return config_filename
            elif parser_type == RESULT:
                config_filename = Path(self.data_path, 'results.cfg')
                return config_filename
            elif parser_type == BEHAVIOR:
                config_filename = Path(self.data_path, 'behavior.cfg')
                return config_filename
            raise FileNotFoundError
        except OSError as o_err:
            ml.log_event(o_err)

    @staticmethod
    def _get_data_directory_name() -> str:
        return 'data_src'

    def _get_data_path(self) -> Path:
        """
        :return: data path as path object
        """
        ml.log_event('get data path', event_completed=False)
        try:
            project_path = self._get_project_path()
            data_path = Path(project_path, self._get_data_directory_name())
            ml.log_event('get data path', event_completed=True)
            return data_path
        except OSError as o_err:
            ml.log_event(o_err)

    @staticmethod
    def _get_most_popular_results(filtered_results, result_count=RESULTS_RETURN_MAX) -> list:
        ml.log_event('get most popular results up to count {}'.format(result_count))
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

    def _get_parser_data(self) -> tuple:
        try:
            parser_data = (self.behavior_config_filename, self.behavior_parser), \
                          (self.result_config_filename, self.result_parser), \
                          (self.search_config_filename, self.search_parser)
            return parser_data
        except ValueError as v_err:
            ml.log_event(v_err)

    @staticmethod
    def _get_project_path() -> Path:
        try:
            return Path(getcwd())
        except OSError as o_err:
            ml.log_event(o_err)

    def _get_search_state(self) -> tuple:
        """
        :return: search states
        """
        ml.log_event('get search state for {}'.format(self.active_header))
        try:
            self.search_parser[self.active_header]['last_read'] = str(datetime.datetime.now())
            _search_queued = self.search_parser[self.active_header].getboolean('search_queued')
            _search_running = self.search_parser[self.active_header].getboolean('search_running')
            _search_stopped = self.search_parser[self.active_header].getboolean('search_stopped')
            _search_concluded = self.search_parser[self.active_header].getboolean('search_concluded')
            ml.log_event('\n\nsearch state for {}: \nqueued: {}\nrunning: {}\nfinished: {}\nadded: {}\n\n'.format(
                self.active_header, _search_queued, _search_running, _search_stopped, _search_concluded))
            return _search_queued, _search_running, _search_stopped, _search_concluded
        except KeyError as k_err:
            ml.log_event(k_err)

    def _hash(self, x, un=False):
        ml.log_event('hash from {}'.format(x), event_completed=False)
        try:
            _hash, polarity = list(), -1 if un else 1
            for ele in x:
                _hash.append(chr(ord(ele) + int(self.behavior_parser[DEFAULT]['unicode']) * polarity))
            ml.log_event('hashed to {}'.format(''.join(_hash)), event_completed=False)
            return ''.join(_hash)
        except ValueError as v_err:
            ml.log_event(v_err)

    @staticmethod
    def _id_is_valid(search_id) -> bool:
        ml.log_event('check if search id {} is valid'.format(search_id))
        try:
            if search_id is not None:
                if search_id != EMPTY:
                    return True
            return False
        except ValueError as v_err:
            ml.log_event(v_err)

    def _manage_state_updates(self, section_states):
        ml.log_event('manage state updates..')
        _search_queued, _search_running, _search_stopped, _search_concluded = section_states
        if _search_queued and not self._search_queue_full():
            self._start_search()
        elif _search_running:
            if self._qbit_get_search_status() is None:
                self._update_search_states(RESET)
            elif STOPPED in self._qbit_get_search_status():
                self._update_search_states(STOPPED)
        elif _search_stopped:
            filtered_results, filtered_results_count = self._filter_results()
            if filtered_results is not None and filtered_results_count > 0:
                self._add_results_by_popularity(filtered_results)
            else:
                self._update_search_states(QUEUED)
        elif _search_concluded:
            pass
        else:
            self._update_search_states(QUEUED)
        self.pause_on_event(SEARCH)

    @staticmethod
    def _pattern_matches(search_pattern, file_name) -> bool:
        try:
            pattern_match = findall(search_pattern, file_name)
            if pattern_match:
                ml.log_event('matched pattern {} to {}'.format(search_pattern, file_name))
                return True
            return False
        except RuntimeError as r_err:
            ml.log_event(str(r_err) + 'error with regex, search_pattern: {} file_name: {}'.format(search_pattern, file_name))

    def _results_fetch_all_data(self) -> dict:
        ml.log_event('fetching results from disk', event_completed=False)
        try:
            all_data = dict()
            for section in self.result_parser.sections():
                all_data[self._hash(section, True)] = dict()
                for key, detail in self.result_parser[section].items():
                    all_data[self._hash(section, True)][key] = self._hash(detail, True)
            ml.log_event('fetching results from disk', event_completed=True)
            return all_data
        except KeyError as k_err:
            ml.log_event(k_err)

    def _start_search(self):
        try:
            search_term = self._config_get_search_term()
            search_job, search_status, search_state, search_id, search_count = \
                self._qbit_create_search_job(search_term, 'all', 'all')
            if RUNNING in search_state:  # search started successfully
                ml.log_event('search started for {}'.format(self.active_header), event_completed=True)
                self._config_set_search_id_as_active(search_id)
                self._update_search_states(STARTING)
        except KeyError as k_err:
            ml.log_event('{}: unable to process search job'.format(k_err))

    def _qbit_add_result(self, result):
        try:
            count_before = self._qbit_count_all_torrents()
            ml.log_event('local machine has {} stored results before add attempt..'.format(count_before), announce=True)
            self.qbit_client.torrents_add(urls=result['fileUrl'], is_paused=True)
            self.pause_on_event(ADD)
            results_added = self._qbit_count_all_torrents() - count_before
            if results_added > 0:
                if not self.result_parser.has_section(self._hash(result['fileName'])):
                    ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                    self._result_parser_store(result)
                    ml.log_event('qbit client has added result {}'.format(result['fileName']), announce=True)
                    self.search_parser[self.active_header]['results_added'] = str(int(
                        self.search_parser[self.active_header]['results_added']) + results_added)
                    return
        except ConnectionError as c_err:
            ml.log_event(c_err)

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
            ml.log_event('qbit client created search job for {}'.format(pattern))
            return _job, _status, _state, _id, _count
        except ConnectionError as c_err:
            ml.log_event(c_err)

    def _qbit_get_search_results(self):
        try:
            search_id = self._get_active_search_ids()
            search_id_valid = self._id_is_valid(search_id)
            if search_id_valid:
                results = self.qbit_client.search_results(search_id)
                ml.log_event('qbit client get search results', event_completed=True)
                return results
            return None
        except KeyError as k_err:
            ml.log_event(k_err)

    def _qbit_get_search_status(self) -> str:
        """
        :return: the status of the search at search_id
        """
        try:
            ml.log_event('checking search status for section: {}'.format(self.active_header))
            search_id, search_status = self.search_parser[self.active_header]['search_id'], None
            search_id_valid = self._id_is_valid(search_id)
            if search_id_valid:
                ml.log_event('getting search status for header {} with search_id {}'.format(
                    self.active_header, search_id))
                if search_id in self.active_search_ids.values():
                    ongoing_search = self.qbit_client.search_status(search_id=search_id)
                    search_status = ongoing_search.data[0]['status']
            ml.log_event('search status for section: {} is {}'.format(self.active_header, search_status))
            ml.log_event('qbit client get search status')
            return search_status
        except ConnectionError as c_err:
            event = 'unable to process search for section: {}'.format(self.active_header)
            ml.log_event(event)

    def _reset_search_ids(self):
        """
        upon initialization of new object, delete expired search_ids
        :return: None  # TODO should i return success?
        """
        ml.log_event('reset search ids',event_completed=False)
        try:
            for section_header in self.search_parser.sections():
                self.active_header = section_header
                ml.log_event('reset search_id for section: {}'.format(self.active_header))
                self._update_search_states(RESET)
                ml.log_event('reset search ids', event_completed=True)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _result_parser_store(self, result):
        ml.log_event('store result {} in result parser'.format(result), event_completed=False)
        try:
            self.result_parser.add_section(self._hash(result['fileName']))
            header = self._hash(result['fileName'])
            for attribute, detail in result.items():
                ml.log_event('add to results ledger, attribute {} detail {}'.format(
                    self._hash(attribute), self._hash(detail)))
                self.result_parser[header][self._hash(attribute)] = self._hash(str(detail))
                self.pause_on_event(99)
        except KeyError as k_err:
            ml.log_event(k_err)

    def _search_queue_full(self) -> bool:
        ml.log_event('check search queue..')
        try:
            active_search_count = len(self.active_search_ids.keys())
            if active_search_count < 5:
                ml.log_event('search queue is not full, currently active search ids: {}'.format(self.active_search_ids.keys()))
                return False
            ml.log_event('search queue is FULL, cannot add {}.. currently active search ids: {}'.format(
                self.active_header, self.active_search_ids.keys()), announce=True)
            return True
        except RuntimeError as r_err:
            ml.log_event(r_err)

    def _search_yielded_required_results(self) -> bool:
        """
        decides if search is ready to be marked as completed (ADDED)
        :return: bool, search completed
        """
        ml.log_event('check if search can be concluded', event_completed=False)
        try:
            attempted = int(self.search_parser[self.active_header]['search_attempts'])
            maximum_attempts = int(self.search_parser[self.active_header]['maximum_search_attempts'])
            added = int(self.search_parser[self.active_header]['results_added'])
            required = int(self.search_parser[self.active_header]['results_required'])
            if added > required or attempted > maximum_attempts:
                ml.log_event('search can be concluded', event_completed=True)
                return True
            ml.log_event('search cannot be concluded', event_completed=True)
            return False
        except KeyError as k_err:
            ml.log_event(k_err)

    def _update_search_states(self, job_state):
        ml.log_event('updating the search state machine..')
        try:
            if job_state == RESET or job_state == QUEUED:
                self.search_parser.remove_section('search_id')
                self.search_parser[self.active_header]['search_queued'] = YES
                self.search_parser[self.active_header]['search_running'] = NO
                self.search_parser[self.active_header]['search_stopped'] = NO
                self.search_parser[self.active_header]['search_concluded'] = NO
            elif job_state == STARTING:
                self.search_parser[self.active_header]['search_queued'] = NO
                self.search_parser[self.active_header]['search_running'] = YES
                self.search_parser[self.active_header]['search_stopped'] = NO
                self.search_parser[self.active_header]['search_concluded'] = NO
                self._config_increment_search_try_counter()
            elif job_state == STOPPED:
                self.search_parser[self.active_header]['search_queued'] = NO
                self.search_parser[self.active_header]['search_running'] = NO
                self.search_parser[self.active_header]['search_stopped'] = YES
                self.search_parser[self.active_header]['search_concluded'] = NO
            elif job_state == CONCLUDED:
                self.search_parser[self.active_header]['search_queued'] = NO
                self.search_parser[self.active_header]['search_running'] = NO
                self.search_parser[self.active_header]['search_stopped'] = NO
                self.search_parser[self.active_header]['search_concluded'] = YES
            else:
                pass
            self.search_parser[self.active_header]['last_write'] = str(datetime.datetime.now())
        except KeyError as k_err:
            ml.log_event(k_err)


if __name__ == '__main__':
    ml = MinimalLog()
else:
    ml = MinimalLog(__name__)
