# -*- coding: utf-8 -*-
import glob
from access_manager import AccessManager
from collections import namedtuple

from PyQt5.QtCore import QSize, QObject, pyqtSlot, pyqtProperty, QUrl, pyqtSignal, QVariant
from PyQt5.QtWebKitWidgets import QWebPage

import logging
import sys
from job import Job
from settings import BASE_PROJECT_DIR

logger = logging.getLogger(__name__)


class JSControllerObject(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    @pyqtSlot(str)
    def log_message(self, message):
        logger.info('js: {}'.format(message))

    @pyqtSlot(str)
    def log_error(self, message):
        logger.error('js: {}'.format(message))

    @pyqtProperty(str)
    def py_version(self):
        logger.debug('Job {}: py_version'.format(self.parent.current_job))
        return sys.version

    @pyqtProperty(str)
    def current_state(self):
        logger.debug('Job {}: current_state'.format(self.parent.current_job))
        if self.parent.current_job.state:
            return self.parent.current_job.state
        else:
            return 'main'

    @pyqtSlot()
    def done(self):
        logger.debug('Job {}: done'.format(self.parent.current_job))
        self.parent.reset()

    @pyqtSlot(QVariant)
    def load(self, job_dict):
        logger.debug('load: {}'.format(job_dict))
        if self.parent.current_job:
            self.parent.new_job.emit(self.parent.current_job.new_state(**job_dict))
        else:
            logger.error('Invalid State. load called when no current job')


class WebPageCustom(QWebPage):
    job_finished = pyqtSignal()
    new_job = pyqtSignal(Job)
    controller_js_file = 'controller.js'
    js_lib_string_list = None

    @staticmethod
    def get_js_lib_string():
        if WebPageCustom.js_lib_string_list is None:
            WebPageCustom.js_lib_string_list = []
            with open("{base}/{ctrl}".format(base=BASE_PROJECT_DIR, ctrl=WebPageCustom.controller_js_file)) as ctrl_lib:
                WebPageCustom.js_lib_string_list.append(ctrl_lib.read())
            for file in glob.glob("{base}/js_libs/*.js".format(base=BASE_PROJECT_DIR)):
                with open(file, encoding='utf-8', mode='r') as js_lib:
                    WebPageCustom.js_lib_string_list.append(js_lib.read())
        return WebPageCustom.js_lib_string_list

    def __init__(self, parent, size=QSize(1366, 768)):
        QWebPage.__init__(self, parent)
        self.current_job = None
        self.setViewportSize(size)
        self.control = JSControllerObject(self)
        self.mainFrame().javaScriptWindowObjectCleared.connect(lambda: logger.debug('javaScriptWindowObjectCleared in Main Frame'))
        self.loadStarted.connect(lambda: logger.debug('Load started for {}'.format(self.current_job)))
        self.linkClicked.connect(lambda url: logger.debug('Link {} Clicked for {}'.format(url, self.current_job)))
        self.loadFinished.connect(self.on_load_finished)

        self.access_manager = AccessManager(self)
        self.setNetworkAccessManager(self.access_manager)

    def is_busy(self):
        return bool(self.current_job)

    def javaScriptConsoleMessage(self, message, line_number, source_id):
        print('{}\{}: {}'.format(source_id, line_number, message))

    def reset(self):
        self.current_job = None
        self.mainFrame().setHtml("<html><head><title></title></head><body></body></html>")
        self.job_finished.emit()

    def inject_job(self):
        if not self.current_job:
            return

        self.mainFrame().addToJavaScriptWindowObject("SjCtrl", self.control)

        for js_lib in self.get_js_lib_string():
            self.mainFrame().evaluateJavaScript(js_lib)

        with open(self.current_job.file, 'r') as job_file:
            self.mainFrame().evaluateJavaScript(job_file.read())

    @pyqtSlot(bool)
    def on_load_finished(self, ok):
        if not self.current_job:
            return

        if not ok:
            logger.error('Unable to load job {}'.format(self.current_job))
            self.reset()
            return
        self.inject_job()

    def load_job(self, job):
        logger.debug('New job request {}'.format(job))
        if not job.file:
            logger.error('No Job file specified {}'.format(job))

        self.current_job = job
        self.control.state = self.current_job.state

        if self.current_job.url:
            qurl = QUrl(self.current_job.url)
            if not qurl.isValid():
                logger.error('Invalid URL {}'.format(self.current_job.url))
                self.reset()
                return

            self.mainFrame().load(qurl)
        else:
            self.inject_job()
