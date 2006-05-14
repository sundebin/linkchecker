# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""Aggregate needed object instances for checker threads."""
import threading
import time
import logger
import status
import linkcheck
import linkcheck.log
import linkcheck.director


def check_target (target):
    try:
        target()
    except (KeyboardInterrupt, SystemExit):
        linkcheck.log.warn(linkcheck.LOG_CHECK,
            "interrupt did not reach the main thread")
    except:
        linkcheck.director.internal_error()


def start_thread (target):
    t = threading.Thread(target=lambda: check_target(target))
    t.setDaemon(True)
    t.start()


class Aggregate (object):

    def __init__ (self, config, urlqueue, connections, cookies, robots_txt):
        self.config = config
        self.urlqueue = urlqueue
        self.connections = connections
        self.cookies = cookies
        self.robots_txt = robots_txt
        self.logger = logger.Logger(config)

    def start_threads (self):
        if self.config["status"]:
            start_thread(self.status)
        for i in range(self.config["threads"]):
            start_thread(self.worker)
        else:
            self.worker()

    def worker (self):
        while True:
            self.check_url()
            if self.urlqueue.empty():
                break

    def check_url (self):
        url_data = self.urlqueue.get()
        if url_data is not None:
            try:
                if not url_data.has_result:
                    url_data.check()
                self.logger.log_url(url_data)
            finally:
                self.urlqueue.task_done(url_data)

    def status (self):
        start_time = time.time()
        while status.status_is_active():
            time.sleep(5)
            status.print_status(self.urlqueue, start_time)

    def abort (self):
        self.urlqueue.do_shutdown()
        self.urlqueue.join(timeout=10)
        self.logger.end_log_output()

