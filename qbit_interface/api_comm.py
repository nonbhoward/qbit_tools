from datetime import datetime
from minimalog.minimal_log import MinimalLog
from qbit_interface.config_helper import QbitConfig
from user_configuration.WEB_API_CREDENTIALS import *
import qbittorrentapi
ml = MinimalLog(__name__)


class QbitApiCaller:
    def __init__(self):
        self.qbit_client_connected = True if self.client_is_connected() else False
        if self.qbit_client_connected:
            self.connection_time_start = datetime.now()

    def add_result(self, result):
        try:
            search_parser_keys, user_config_parser_keys, metadata_parser_keys = \
                self.config.hardcoded.keys.search_parser_keyring, \
                self.config.hardcoded.keys.user_config_parser_keyring, \
                self.config.hardcoded.keys.metadata_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            count_before = self.count_all_local_results()
            ml.log_event('local machine has {} stored results before add attempt..'.format(count_before))
            # TODO why does this api call sometimes not add? bad result? not long enough wait?
            # self.qbit_client.torrents_add(urls=result['fileUrl'], is_paused=True)  # TODO delete
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
        """
        connect to the client, fetch check app version and web api version
        :return: bool, true if able to populate all data successfully
        """
        ml.log_event('connect to client', event_completed=False)
        try:
            self.qbit_client = qbittorrentapi.Client(host=HOST, username=USER, password=PASS)
            app_version = self.qbit_client.app_version
            web_api_version = self.qbit_client.app_web_api_version
            if app_version is not None and web_api_version is not None:
                # TODO could unpack more details here just for readability
                ml.log_event('connect to client with.. \n\n\tclient app version {} \n\tweb api version {}\n\n'.format(
                    app_version, web_api_version), event_completed=True)
                return True
            return False
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def count_all_local_results(self) -> int:
        try:
            local_result_count = 0
            if self.qbit_client.torrents.info().data:
                local_result_count = len(self.qbit_client.torrents.info().data)
            return local_result_count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def create_search_job(self, pattern, plugins, category) -> tuple:
        try:
            _job = self.qbit_client.search.start(pattern, plugins, category)
            _status = _job.status()
            _state = _status.data[0]['status']
            _id = str(_status.data[0]['id'])
            _count = _status.data[0]['total']
            ml.log_event('qbit client created search job for \'{}\''.format(pattern))
            return _job, _status, _state, _id, _count
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_search_results(self):
        try:
            # FIXME this needs to handle invalid search id values.. such as values from previous runs
            search_id = self._get_active_search_id()
            if search_id:
                results = self.qbit_client.search_results(search_id)
                if results is None:
                    ml.log_event(f'results for header \'{self.active_header}\' with '
                                 f'search id \'{search_id}\' is None', level=ml.WARNING)
                ml.log_event('qbit client get search results', event_completed=True)
                return results
            return None
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)

    def get_search_status(self) -> str:
        """
        :return: the status of the search at search_id
        """
        try:
            ml.log_event(f'check search status for section \'{self.active_header}\'')
            search_parser_keys = self.config.hardcoded.keys.search_parser_keyring
            search_detail_parser_at_active_header = self._get_search_detail_parser_at_active_header()
            search_id, search_status = search_detail_parser_at_active_header[search_parser_keys.SEARCH_ID], None
            # TODO did this line below add any value? delete this line after decision
            # search_id_valid = self._active_header_search_id_is_valid()  # FIXME, i think i deleted this function?
            # TODO PRIORITY BUG, this section of code was double logging, fixed?
            ml.log_event(f'getting search status for header \'{self.active_header}\' with search id \'{search_id}\'')
            if search_id in self.active_search_ids.values():
                ongoing_search = self.qbit_client.search_status(search_id=search_id)
                if ongoing_search is None:
                    ml.log_event(f'are you sure that search id \'{search_id}\' is valid?')
                    ml.log_event(f'known valid search ids are..')
                    for search_header, search_id in self.active_search_ids:
                        ml.log_event(f'\t header \'{search_id}\' with id \'{search_id}\'')
                    pass  # FIXME
                # FIXME ASAP line above is causing a NoneType return, soft-freezing the state-machine
                search_status = ongoing_search.data[0]['status']
            if search_status is None:  # TODO fyi new line, monitor, delete comment after
                ml.log_event(f'search status is \'{search_status}\' for section \'{self.active_header}\'',
                             level=ml.WARNING)
                return search_status
            ml.log_event(f'search status is \'{search_status}\' for section \'{self.active_header}\'')
            return search_status
        except Exception as e_err:
            ml.log_event(e_err, level=ml.ERROR)


if __name__ == '__main__':
    qba = QbitApiCaller()
    pass
