# -*- coding: utf-8 -*-
from collections import namedtuple
import glob

from PyQt5.QtCore import QObject, pyqtSlot, QTimer, Qt
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWidgets import QMainWindow
from croniter import croniter
from job import Job
from webpage_custom import WebPageCustom
import queue
from queue import Queue
from datetime import datetime
from settings import BASE_PROJECT_DIR

import logging
logger = logging.getLogger(__name__)


class PageCoordinator(QObject):
    marker = '//!>'
    schedule_key = 'schedule'
    job_recalculate_minutes = 15
    job_limit = 100

    def __init__(self, instances, parent=None, debug_file=None, queue_size=1000):
        super().__init__(parent)
        self.instances = instances
        self.web_views = []
        self.job_list = []
        self.job_queue = Queue(maxsize=queue_size)

        if debug_file:
            # When in debugging mode we only load and single instance and show it to the user
            self.instances = 1
            self.main_window = QMainWindow()
            self.webview = QWebView(self.main_window)
            self.main_window.setCentralWidget(self.webview)
            self.main_window.showFullScreen()
            self.main_window.setWindowTitle("SpiderJuice Debug Window")
        else:
            self.parse_local_jobs()
            self.recalculate_timer = QTimer(self)
            self.recalculate_timer.timeout.connect(self.shedule_for_next_15_min)
            self.recalculate_timer.setTimerType(Qt.VeryCoarseTimer)
            self.recalculate_timer.start(self.job_recalculate_minutes * 60 * 1000)
            self.shedule_for_next_15_min()

        for _ in range(self.instances):
            wp = WebPageCustom(self)
            wp.job_finished.connect(self.distribute_jobs)
            wp.new_job.connect(self.queue_new_job)
            self.web_views.append(wp)

        if debug_file:
            custom_webpage = self.web_views[0]
            self.webview.setPage(custom_webpage)
            self.main_window.show()
            self.queue_new_job(Job(file=debug_file))

    def parse_local_jobs(self):
        logger.debug('Parsing Local Jobs')
        for file in glob.glob("{base}/jobs/*.js".format(base=BASE_PROJECT_DIR)):
            with open(file, encoding='utf-8', mode='r') as job_file:
                job_conf = {}
                while True:
                    line = job_file.readline().strip()
                    if not line.startswith(self.marker):
                        break

                    line = line.split(self.marker, 1)[1]
                    if ':' not in line:
                        break

                    key, value = line.split(':', 1)
                    job_conf[key.strip()] = value.strip()

                if self.schedule_key in job_conf:
                    job_conf['file'] = file
                    self.job_list.append(Job(**job_conf))

    @pyqtSlot(Job)
    def queue_new_job(self, job):
        logger.debug('Got file {job} at {time}'.format(job=job, time=datetime.now()))
        try:
            self.job_queue.put(job, block=False)
            self.distribute_jobs()
        except queue.Full as e:
            logger.exception('The queue is full. Ignored Job {}, {}'.format(job, e))

    @pyqtSlot()
    def distribute_jobs(self):
        logger.debug('Distribute Jobs requests')
        if self.job_queue.empty():
            return

        for web_view in self.web_views:
            if not web_view.is_busy():
                job = self.job_queue.get(block=False)
                web_view.load_job(job)

    @pyqtSlot()
    def shedule_for_next_15_min(self):
        logger.debug('Setting up schedule for next 15 min')
        now = datetime.now()
        for job in self.job_list:
            cron_iter = croniter(job.schedule, datetime.now())
            for _ in range(self.job_limit):
                next_job_time = cron_iter.get_next(datetime)
                second_till_next_job = (next_job_time - now).total_seconds()
                job_recalculate_seconds = self.job_recalculate_minutes * 60
                if second_till_next_job <= job_recalculate_seconds:
                    milliseconds = second_till_next_job * 1000
                    logger.debug('Starting QTimer in {}'.format(milliseconds))
                    QTimer.singleShot(milliseconds, Qt.VeryCoarseTimer, lambda: self.queue_new_job_file(job))
                    QTimer.singleShot(milliseconds, Qt.VeryCoarseTimer, lambda: self.queue_new_job(job))
                else:
                    break

    @pyqtSlot(dict)
    def add_job_to_queue(self, data):
        """Safe to call from another thread"""
        logger.debug('Recieved data: {}'.format(data))
        # job_queue.
        # url = data.get('start_url')
        # if url:
