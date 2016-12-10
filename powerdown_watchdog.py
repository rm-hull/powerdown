#!/usr/bin/env python
#
# Script to ping a known host every X seconds, and on Y consecutive
# failed pings will institute an ordered shutdown

import os
import syslog
import ping
import socket
import sys
import time


class PingTest(ping.Ping):
    def __init__(self, *args, **kwargs):
        self.failed_call_count = 0
        super(PingTest, self).__init__(*args, **kwargs)

    def print_success(self, delay, ip, packet_size, ip_header, icmp_header):
        if (self.failed_call_count > 0):
            self.failed_call_count = 0
            syslog.syslog("Ping successful: {0} - reset failed count".format(ip))

    def print_failed(self):
        self.failed_call_count += 1
        syslog.syslog(syslog.LOG_WARNING, "Ping unsuccessful - failed count incremented: {0}".format(self.failed_call_count))

    def print_unknown_host(self):
        self.failed_call_count += 1
        syslog.syslog(syslog.LOG_WARNING, "Unknown host - failed count incremented: {0}".format(self.failed_call_count))


def child(host, max_fails=5, startup_delay=600, interval=60):
    try:
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_SYSLOG)
        syslog.syslog('Powerdown watchdog started...')
        syslog.syslog('Sleeping for 10 minutes while systems stabilizing.')
        time.sleep(startup_delay)

        ping = PingTest(host)

        while True:
            ping.run(count=1)
            if ping.failed_call_count >= max_fails:
                syslog.syslog(syslog.LOG_ALERT, "{0} or more successive pings failed... shutting down".format(max_fails))
                os.system('shutdown -h now')

            time.sleep(interval)

    except socket.error as e:
        print("Ping Error: {0}".format(e))


newpid = os.fork()
if newpid == 0:
    child(sys.argv[1])
