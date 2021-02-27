# primary modules  
### main_loop.py  
main program loop, abstracted program behavior  
  
### qbit_bot_states.py  
the state machine  
	automatically..  
		..conduct searches..  
		..filter results..  
		..and acquire..  
		..the latest linux images via bittorrent using qbittorrent's web api  
  
### api_comm.py  
the interface to the api  
  
### qbit_bot_helper.py  
helper functions for state machine & api comm  
  
### settings_wrapper.py  
module contains classes to parse configuration files  
  
### settings_io.py  
interact (read/write) with settings on disk  
  
  
# configuration  
### metadata_history.cfg  
search results information  
  
### search.cfg  
dictates search behavior  
  
### user_configuration.cfg  
dictates program behavior  


# requirements & setup
### requirements
1. a python installation  
2. a pip installation, or some other manner of installing packages  
3. the qbittorrent-api package : https://qbittorrent-api.readthedocs.io/en/latest/  


### setup  
0. install qbittorrent  
1. clone project  
2. create virtual environment  
3. activate virtual environment  
4. pip install dependencies per requirements.txt  
5. launch with 'python main_loop.py'  
6. supply web ui credentials (user, pass, host) as preferred  
