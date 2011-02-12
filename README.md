ircuserlog
----------

Logs JOINs, PARTs, PRIVMSGs and other of all the users in the selected channels.


##Logger
###Usage

    $ ./logger.py [options]

###Options
    -v : Outputs the raw IRC session
    -f : Outputs log handling commands
    -d : Debugging mode
##Reader
###Usage
    
    $ ./read.py [options] LOG_FILE

###Options

    -w : Starts the reader in web mode, outputting to localhost:8000
