#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse

import sys
import logging.config
import os
import settings
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from page_coordinator import PageCoordinator
from request_server import RequestServer

if __name__ == '__main__':
    logging.config.dictConfig(settings.LOGGING)

    parser = argparse.ArgumentParser(description='SpiderJuice Service')
    parser.add_argument('-d', '--scriptdebug', nargs='?', help='Debug the script given on path')
    args = parser.parse_args()

    rq = RequestServer()
    rq.start()
    a = QApplication(sys.argv)

    pc = PageCoordinator(10, debug_file=os.path.abspath(args.scriptdebug))

    # We don't need to specify QueuedConnection because that will happen by default when
    # the request comes from another thread. We are just making it explicit to the reader that this will happen.
    rq.job_request.connect(pc.add_job_to_queue, type=Qt.QueuedConnection | Qt.UniqueConnection)

    sys.exit(a.exec_())