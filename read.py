#!/usr/bin/env python

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
        
import pickle
import sys
from time import ctime
from operator import attrgetter
import readline
import re

lfi = sys.argv[-1] if len(sys.argv) > 1 else input("Log file> ")
userlist = pickle.load(open(lfi, 'rb'))
WEB = ("-w" in sys.argv) if len(sys.argv) > 2 else False

if WEB:
    import http.server
    # Web-based viewer
    class Handler(http.server.BaseHTTPRequestHandler):
        list_re = re.compile("/list(/.*)?")
        user_re = re.compile("/user/(.+)")
        def do_GET(self):
            userlist = pickle.load(open(lfi, 'rb'))
            m = self.list_re.match(self.path)
            if m:
                if m.groups()[0] == "/messages":
                    key = lambda x: len(x.conversation)
                elif m.groups()[0] == "/seen":
                    key = lambda x: len(x.seen)
                else:
                    key = lambda x: x.nick
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes("<h2>User list</h2>\n<ul>", "utf-8"))
                for user in sorted(userlist, reverse=True, key=key):
                    self.wfile.write(bytes("<li><a href=\"/user/{0}\">{0}</a>, seen {1} times, {2} messages</li>".format(user.nick, len(user.seen), len(user.conversation)), "utf-8"))
                self.wfile.write(bytes("</ul>", "utf-8"))
                return
            m = self.user_re.match(self.path)
            if m:
                nick = m.groups()[0]
                user = userlist.nick(nick)
                if user:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes("<h2>Summary of {0}</h2><h3>Logged connections</h3><ul>".format(nick), "utf-8"))
                    for connection in user.seen:
                        self.wfile.write(bytes("<li>{0} {4} {3} from {2}</li>".format(*connection), "utf-8"))
                    self.wfile.write(bytes("</ul>", "utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()
                return
            self.send_response(404)
            self.end_headers()
    httpd = http.server.HTTPServer(('', 8000), Handler)
    httpd.serve_forever()

else:
    # CLI
    def e(cmd):
        print("Unknown command", cmd)
    def l(args):
        if len(args) > 0:
            if args[0] == "messages":
                key = lambda x: len(x.conversation)
            elif args[0] == "seen":
                key = lambda x: len(x.seen)
            else:
                print("Unknown ordering method")
                key = lambda x: x.nick
        else:
            key = lambda x: x.nick

        print([u.nick for u in sorted(userlist, reverse=True, key=key )])
    def u(args):
        if len(args) < 1:
            print("USAGE: user NICK")
            return
        user = userlist.nick(args[0])
        if user:
            print("User", user.nick)
            print("Logged", len(user.conversation), "messages sent.")
            for connection in user.seen:
                print(ctime(connection[0]), ":",str(connection[4]), str(connection[3]), "from", str(connection[2]))
        else:
            print("User %s not found" % args[0])
    cmds = {}
    def h(args):
        print(",".join(list(cmds.keys())))

    def r(args):
        global userlist
        userlist = pickle.load(open(lfi, 'rb'))
        print("Imported <%s>, %d users." % (lfi, len(userlist)))
    def py(args):
        try:
            exec(" ".join(args))
        except Exception as e:
            print("Command returned exception:", e)
    cmds = {"list":l, "user":u, "help":h, "refresh":r, "py":py}
    print("Imported <%s>, %d users." % (lfi, len(userlist)))
    while 1:
        try:
            cmd = input("> ").split()
        except EOFError:
            cmd = None
            print()
        except KeyboardInterrupt:
            sys.exit(0)
        if cmd:
            cmds[cmd[0]](cmd[1:]) if cmd[0] in list(cmds.keys()) else e(cmd[0])
        
