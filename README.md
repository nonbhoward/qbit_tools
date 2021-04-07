### as of 2021-04-04 current status of main branch on win10 is functional after major refactor
### as of 2021-04-04 current status of main branch on linux is unknown after major refactor

# a brief project summary follows
### core.interface.py
module handling transactions between other modules such as..
1. state machine uses core.interface to fetch, save, and process data
2. settings_io uses core.interface to communicate parser data to other modules
3. qbit_api_wrapper uses core.interface to communicate api data to other modules

### data_meta
this is a data directory that contains configuration files related to result metadata
1. metadata_added.cfg is results that have been added to local results
2. metadata_failed.cfg is results that have been previously encountered and failed

### data_search
this is a data directory that contains configuration files related to search configuration
1. search.cfg  
   i. should be setup before runtime  
   ii. can be used to configure individual search headers  
   iii. comes with examples
   
### extra
TODO, nothing here, may be used for managing logs

### media
TODO, nothing here, may be used for managing local results

### minimalog (https://github.com/nonbhoward/minimalog)
logger written by myself, it's buggy but including it in this project is motivation for me to work on it  
all calls to it could be removed without affecting program function  

### network
TODO, i have started to work on a few modules, but nothing here matters yet

### qbit_api_interface.qbit_api_wrapper
the interface to the qbittorrent api via wrapper functions  
all api calls should be found or moved to here  

### user_configuration
1. EDIT_SETTINGS_HERE.cfg is program globals, right now mostly determines program delays  
2. settings_io.py is the interface to the configuration parsers and keys  
3. settings_wrapper.py is a hierarchy of classes that allows "easy" access to parsers structure

  
### DOCUMENTATION.txt is similar to README.md, usually contains more info if updated recently

### LICENSE is self explanatory

### main_loop is main program loop, minimal & abstracted program behavior

### README.md is what you are reading

### requirements.txt is the typical venv constructor helper, see pip documentation

### state_machine.py controls the high-level program flow, a traditional 'state machine' as found all throughout engineering

## +++ === +++ === +++ === +++ === +++
## === +++ === +++ === +++ === +++ ===

# requirements & setup
### requirements
1. a python installation  
2. a pip installation, or some other manner of installing packages  
3. the qbittorrent-api package : https://qbittorrent-api.readthedocs.io/en/latest/  


### setup  
00. install qbittorrent  
01. clone this project  
02. if using minimalog, clone minimalog to a parallel dir and softlink it
03. if not using minimalog, delete all calls to minimalog (sorry)  
04. create virtual environment 
05. activate virtual environment  
06. pip install dependencies per requirements.txt
07. enable qbittorrent's web ui (setup user and pass)
08. once again, check that search plugins are enabled
09. supply web ui credentials (user, pass, host) as preferred  
10. launch with 'python main_loop.py', via IDE, or however you do you  

[^1] : https://github.com/lgallard/qBittorrent-Controller/wiki/How-to-enable-the-qBittorrent-Web-UI
