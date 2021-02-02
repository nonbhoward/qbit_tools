# source  
### main.py
main program loop, start here to customize behavior  

### qbit_bot.py
automatically acquire the latest linux images via bittorrent using qbittorrent's web api  

### configuration_reader.py
contains classes to parse configuration files for use in main program  



# configuration
### metadata.cfg  
stored metadata from previous searches, option to scramble non-securely  

### search_details.cfg
dictates what searches are queued and how they are managed  

### user_configuration.cfg
dictates program behavior  



# requirement and setup  
### requirements
1. python installation  
2. the pip package for that python installation


### setup  
1. clone project  
2. create virtual environment  
3. activate virtual environment  
4. launch with 'python main_loop.py'  
5. supply web ui credentials (user, pass, host) as preferred  


