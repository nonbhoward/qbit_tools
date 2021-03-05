# primary modules  
### main_loop.py  
main program loop, abstracted program behavior  
  
### api_comm.py  
the interface to the api  
  
### settings_wrapper.py  
module contains classes to parse configuration files  
  
### settings_io.py  
interact (read/write) with settings on disk  
  
### state_machine.py  
the state machine  
  automatically conduct & monitor searches based on user parameters  
  
### state_machine_interface.py  
interface from state machine to parsers and vice versa
  
  
# configuration  
### metadata_added.cfg & metadata_failed.cfg  
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
5. enable web ui [^1]
6. enable search plugins
7. supply web ui credentials (user, pass, host) as preferred  
8. launch with 'python main_loop.py' or via IDE  

[^1] : https://github.com/lgallard/qBittorrent-Controller/wiki/How-to-enable-the-qBittorrent-Web-UI
