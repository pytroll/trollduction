#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Martin Raspaud

# Author(s):

#   Martin Raspaud <martin.raspaud@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The Mighty Dungeon Keeper!
"""

from posttroll.subscriber import Subscribe
from posttroll import context
from threading import Timer
import zmq
import logging
import logging.config
from ConfigParser import ConfigParser
from subprocess import Popen
import argparse
import os
import sys
logger = logging.getLogger(__name__)

def read_config(filename):
    """Read the config file called *filename*.
    """
    cp_ = ConfigParser()
    cp_.read(filename)

    res = {}

    for section in cp_.sections():
        if section == "default":
            continue
        res[section] = dict(cp_.items(section))

    return res

def spawn_daemon(func, *args, **kwargs):
    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    r, w = os.pipe()
    try:
        pid = os.fork()
        if pid > 0:
            # parent process, return and keep running
            os.close(w)
            r = os.fdopen(r)
            chpid = int(r.read())
            os.waitpid(pid, 0)
            return int(chpid)
    except OSError as err:
        print >>sys.stderr, "fork #1 failed: %d (%s)"%(err.errno, err.strerror)
        sys.exit(1)

    os.setsid()

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent
            os.close(w)
            os.close(r)
            sys.exit(0)
    except OSError as err:
        print >>sys.stderr, "fork #2 failed: %d (%s)"%(err.errno, err.strerror)
        sys.exit(1)

    # do stuff
    os.close(r)
    w = os.fdopen(w, 'w')
    chpid = func(*args, **kwargs).pid
    w.write(str(chpid))
    w.close()

    # all done
    os._exit(os.EX_OK)

class ProcessWatcher(object):
    def __init__(self, action):
        self.procs = {}
        self.action = action

    def reset_timer(self, pid):
        try:
            self.procs[pid].cancel()
        except KeyError:
            pass
        self.procs[pid] = Timer(2, self.alert, [pid])
        self.procs[pid].start()

    def stop(self):
        for val in self.procs.itervalues():
            val.cancel()

    def alert(self, pid):
        logger.critical("Didn't get a beat for %d !!!!", pid)
        self.action(pid)

class DungeonKeeper(object):
    """This is the manager class.
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.procs_config = {}
        self.procs = {}
        self.pid_url = {}
        # self.watcher = ProcessWatcher(self.respawn)
        self.watcher = ProcessWatcher(self.poke)

    def respawn(self, pid):
        """Respawn a process that died.
        """
        for proc, ppid in self.procs.iteritems():
            if ppid == pid:
                break
        logger.warning("Restarting %s", proc)
        new_pid = self.spawn(proc, self.procs_config[proc])
        logger.info("%s now has pid %d", proc, new_pid)

    def reload_config(self):
        logger.debug("Reloading config from " + str(self.config_file))
        config = read_config(self.config_file)
        for key, val in config.iteritems():
            # checking for new options in proc
            if key in self.procs_config:
                identical = True
                for key_item, val_item in config[key].iteritems():
                    if(key_item not in self.procs_config[key] or \
                           (self.procs_config[key][key_item] != val_item)):
                        identical = False
                        break
                # checking from deletion of options in proc
                for key_item in self.procs_config[key]:
                    if key_item not in config[key]:
                        identical = False
                        break
                if not identical:
                    # FIXME: a reload might suffice…
                    self.kill(key)
                    pid = self.spawn(key, val)
                    if pid:
                        logger.debug("Updated %s as pid %d", str(key), pid)
                    else:
                        logger.error("Couldn't update " + str(key))
            else:
                pid = self.spawn(key, val)
                if pid:
                    logger.debug("Added %s as pid %d", str(key), pid)

        for key in set(self.procs_config.keys()) - set(config.keys()):
            self.kill(key)
            del self.procs_config[key]
            logger.debug("Removed " + str(key))
        self. procs_config = config

    def kill(self, proc_name):
        """Kill the process
        """
        os.kill(self.procs[proc_name])
        del self.procs[proc_name]

    def spawn(self, proc_name, options):
        """Spawn the process
        """
        try:
            self.procs[proc_name] = spawn_daemon(Popen, [options["script"],
                                                         self.config_file,
                                                         proc_name],
                                                 close_fds=True)
        except Exception:
            logger.exception("Couldn't spawn " + str(proc_name))
            return False
        else:
            return self.procs[proc_name]

    def loop(self):
        with Subscribe(services=[""],
                       addr_listener=True,
                       topics=["pytroll://heart/minion"]) as sub:
            for msg in sub.recv(1):
                if msg:
                    print msg.data
                    self.pid_url[msg.data["pid"]] = msg.data["url"]
                    self.watcher.reset_timer(msg.data["pid"])
                    # self.reload_minion(**msg.data)

    def stop(self):
        self.watcher.stop()

    def poke(self, pid):
        resp = self.send_and_recv("poke", self.pid_url[pid])
        logger.debug("poke %s", resp)

    def reload_minion(self, **kwargs):
        """Reload a minion
        """
        resp = self.send_and_recv("reload", kwargs["url"])
        logger.debug("reload %s", resp)

    def send_and_recv(self, msg, url):
        """Connect to url, send *msg*, wait for response and close. Return the
        response.
        """
        client = context.socket(zmq.REQ)
        client.connect(url)
        client.send(msg)
        resp = client.recv()
        client.close()
        return resp


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file",
                        help="The file containing configuration parameters.")

    args = parser.parse_args()

    logging.config.fileConfig("../etc/logging.cfg")
    logger = logging.getLogger("minion")
    dk = DungeonKeeper(args.config_file)
    dk.reload_config()
    try:
        dk.loop()
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
    finally:
        dk.stop()
        logging.shutdown()
        print "Thanks for using pytroll/duke! See you soon on pytroll.org."

