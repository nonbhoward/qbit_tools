# source  
### main_loop.py
main program loop, abstracted program behavior described here  

### configuration_reader.py
module contains classes to parse configuration files  

### qbit_bot.py
automatically..  
	..conduct searches..  
	..filter results..  
	..and acquire..  
	..the latest linux images via bittorrent using qbittorrent's web api  



# configuration
### metadata.cfg  
search results information  

### search_details.cfg
dictates search behavior  

### user_configuration.cfg
dictates program behavior  



# requirements & setup
### requirements
1. a python installation  
2. a pip installation, or some other manner of installing packages  
3. the qbittorrent-api package : https://qbittorrent-api.readthedocs.io/en/latest/  


### setup  
1. clone project  
2. create virtual environment  
3. activate virtual environment  
4. launch with 'python main_loop.py'  
5. supply web ui credentials (user, pass, host) as preferred  
