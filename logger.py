#!/usr/bin/env python

# IRC user logger
# Author: Adria Lopez <adria@prealfa.com>
#
# Requires: python3

# IRC Settings
SERVER = "irc.anonops.ru"
PORT = 6667
CHANNELS = ["#OperationPayback", "#ophbgary", "#opegypt", "#opTunisia", "#OpIran", "#hackers"]
NICK = "alog"
IDENT = "Alog"
REALNAME = "a log"

import sys
import socket
import pickle
import time
import re

# Configuration
VERBOSE = ("-v" in sys.argv)
DEBUG = ("-d" in sys.argv)
FOREGROUND = ("-f" in sys.argv)
LOG_FILE = "log.pickle"
CLEANUP_TIMER = 60

# Connection class
class Connection(object):
    def __init__(self, server, port, nick, ident, realname):
        self.server = server
        self.port = port
        self.nick = nick
        self.ident = ident
        self.realname = realname
        
        print("||| Opening socket")
        self.s = socket.socket()
        print("||| Connecting... ", end="")
        try:
            self.s.connect((server, port))
        except socket.error as e:
            print(e)
            sys.exit(1)
        else:
            print("DONE")
        self.s.setblocking(0)
        print("||| Identifying... ", end="")
        self.s.send(bytes("NICK {0}\r\n".format(nick), "utf-8"))
        self.s.send(bytes("USER {0} {1} NULL {2}\r\n".format(ident, server, realname), "utf-8"))
        print("DONE")
    def join(self, channel):
        self.s.send(bytes("JOIN {0}\r\n".format(channel), "utf-8"))
    def close(self):
        self.s.send(bytes("QUIT\r\n", "utf-8"))

# User classes
class UList(list):
    def nick(self, n):
        for user in self:
            if user.nick == n:
                return user
        return None

class User(object):
    def __init__(self, nick):
        self.nick = nick
        self.conversation = []
        self.seen = []

# Log class
class Log(object):
    def __init__(self, fname):
        self.fname = fname
        self.load()
    def load(self):
        raise NotImplementedError

class PickleLogger(Log):
    def load(self):
        try:
            f = open(self.fname, 'rb')
            self.userlist = pickle.load(f)
            f.close()
        except IOError:
            print ("||| Logfile doesn't exist. Creating")
            self.userlist = UList()
        except ValueError:
            print ("!!! Failed to load logfile. Overwriting")
            self.userlist = UList()

    def save(self):
        try:
            f = open(self.fname, 'wb')
            pickle.dump(self.userlist, f)
            f.close()
        except IOError as e:
            print("!!! Failed to save: " + e)
        except ValueError:
            print("!!! FAIL MAN")
    def log(self, server, nick, host, action, channel):
        u = self.userlist.nick(nick)
        if not u:
            u = User(nick)
            self.userlist.append(u)
        if action == "JOIN" or action == "PART" or action == "QUIT" or action == "NAME":
            u.seen.append((time.time(), server, host, channel, action))
        elif action == "PRIVMSG":
            u.conversation.append((time.time(), host, server, channel))

# IRC Command handlers
class Handler:
    """Class that groups all the different methods that are called when a message is
    received"""
    con = None
    log = None
    @classmethod
    def ping(cls, server):
        cls.con.s.send(bytes("PONG {0}\r\n".format(server), "utf-8"))
    @classmethod
    def join(cls, nick, ident, host, channel):
        cls.log.log(cls.con.server, nick, host, "JOIN", channel)
    @classmethod
    def part(cls, nick, ident, host, channel):
        cls.log.log(cls.con.server, nick, host, "PART", channel)
    @classmethod
    def quit(cls, nick, ident, host):
        cls.log.log(cls.con.server, nick, host, "QUIT", None)
    @classmethod
    def privmsg(cls, nick, ident, host, channel):
        cls.log.log(cls.con.server, nick, host, "PRIVMSG", channel)
    @classmethod
    def name(cls, channel, namelist):
        for name in namelist.split(" "):
            cls.log.log(cls.con.server, name, None, "NAME", channel)
    @classmethod
    def connected(cls, server, welcome):
        print("||| Connected to " + server)

# Regexp assignement
msg_filter = {
    re.compile(":(.+?)!(.*)@(.+) JOIN :(.+)") : Handler.join,
    re.compile(":(.+?)!(.*)@(.+) PART :(.+)") : Handler.part,
    re.compile(":(.+?)!(.*)@(.+) QUIT.*") : Handler.quit,
    re.compile(":(.+?)!(.*)@(.+) PRIVMSG (.+) :.+") : Handler.privmsg,
    re.compile(".+ 353 {0} = (#.+) :(.*)".format(NICK)) : Handler.name,
    re.compile("PING (:.+)") : Handler.ping,
    re.compile(":(.+) 001 .+ :(.+)") : Handler.connected
}

if __name__ == "__main__":
   
    Handler.con = Connection(SERVER, PORT, NICK, IDENT, REALNAME)
    Handler.log = PickleLogger(SERVER + ".log")
    
    for channel in CHANNELS:
        print("||| Joining " + channel)
        Handler.con.join(channel)

    print("||| Saving every {0} seconds".format(CLEANUP_TIMER))
    rbuf = ""
    try:
        now = time.time()
        while 1:
            if time.time() - now > CLEANUP_TIMER:
                print("### {0} users logged. Saving... ".format(len(Handler.log.userlist)), end="")
                Handler.log.save()
                print ("DONE")
                now = time.time()

            time.sleep(.1)
            try:
                rbuf += Handler.con.s.recv(1024).decode("utf-8")
            except socket.error:
                pass
            except UnicodeDecodeError:
                print("!!! Unicode error")
            tmp = rbuf.split("\n")
            rbuf = tmp.pop()
            
            for line in tmp:
                line = line.rstrip()
                if VERBOSE:
                    print(">>> " + line)
                for expression, handler in msg_filter.items():
                    m = expression.match(line)
                    if m:
                        g = m.groups()
                        if FOREGROUND:
                            print("@@@ Log: " + str(g) + " >> " + str(handler)) 
                        handler(*g)
    
    except KeyboardInterrupt:
        Handler.con.close()
        Handler.log.save()
        print("Connection closed")
    except socket.error:
        Handler.log.save()
        Handler.con.close()
        print("Finished with connection error")
        sys.exit(1)
