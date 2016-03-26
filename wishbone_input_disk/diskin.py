#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  diskin.py
#
#  Copyright 2016 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from wishbone import Actor
from gevent import sleep, event
from gevent.os import make_nonblocking
from time import time
import glob
import os
import cPickle as pickle


class DiskIn(Actor):

    '''**Reads messages from a disk buffer.**


    Parameters:

        - directory(str)
           |  The directory to write data to.

        - idle_trigger(bool)(False)
           |  When True, only reads events when no new events
           |  have been written to disk for at least <idle_time>.


        - idle_time(int)(10)
           |  The time in seconds required that no new events
           |  have been written to disk prior to start to consume
           |  the buffered data.


    Queues:

        - outbox
           |  Incoming events.
    '''

    def __init__(self, actor_config, directory="./", idle_trigger=False, idle_time=10):
        Actor.__init__(self, actor_config)
        self.reading = event.Event()
        self.reading.set()
        self.pool.createQueue("outbox")

    def preHook(self):
        self.createDir()
        self.sendToBackground(self.monitorDirectory)
        self.sendToBackground(self.diskMonitor)

    def createDir(self):

        if os.path.exists(self.kwargs.directory):
            if not os.path.isdir(self.kwargs.directory):
                raise Exception("%s exists but is not a directory" % (self.kwargs.directory))
            else:
                self.logging.info("Directory %s exists so I'm using it." % (self.kwargs.directory))
        else:
            self.logging.info("Directory %s does not exist so I'm creating it." % (self.kwargs.directory))
            os.makedirs(self.kwargs.directory)

    def monitorDirectory(self):
        while self.loop:
            self.processDirectory()
            sleep(0.5)

    def processDirectory(self):
        for filename in glob.glob("%s/*.ready" % (self.kwargs.directory)):
            self.reading.wait()
            self.readFile(filename)

    def readFile(self, filename):
        try:
            if filename.endswith("ready") and self.loop():
                with open(filename, "rb") as output_file:
                    make_nonblocking(output_file)
                    self.logging.info("Read file %s" % filename)
                    for e in self.__pickleReader(output_file):
                        self.submit(e, self.pool.queue.outbox)
                os.remove(filename)
        except Exception as err:
            self.logging.error("Failed to read file %s.  Reason: %s" % (filename, str(err)))

    def diskMonitor(self):
        '''Primitive monitor which checks whether new data is added to disk.'''

        while self.loop():
            try:
                newest = max(glob.iglob("%s/*" % (self.kwargs.directory)), key=os.path.getmtime)
            except Exception:
                pass
            else:
                if time() - os.path.getctime(newest) >= self.kwargs.idle_time:
                    self.reading.set()
                else:
                    self.reading.clear()
            sleep(1)

    def __pickleReader(self, p):

        try:
            while self.loop():
                yield pickle.load(p)
        except EOFError:
            pass