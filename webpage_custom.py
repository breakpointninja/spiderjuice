# -*- coding: utf-8 -*-
import glob
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWebKit import QWebSettings
from access_manager import AccessManager
from collections import namedtuple

from PyQt5.QtCore import QSize, QObject, pyqtSlot, pyqtProperty, QUrl, pyqtSignal, QVariant, Qt
from PyQt5.QtWebKitWidgets import QWebPage

import logging
import sys
from job import Job
from settings import BASE_PROJECT_DIR

logger = logging.getLogger(__name__)


class JSControllerObject(QObject):
    class Marker(QObject):
        def __init__(self, callback_id):
            self.callback_id = callback_id
            super().__init__()

        def get_callback_id(self):
            return self.callback_id

    http_request_finished = pyqtSignal(int, int, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.network_manager = QNetworkAccessManager()

    def http_response(self, callback_id, reply):
        if reply.error() == 0:
            data_str = reply.readAll().data().decode(encoding='UTF-8')
            self.http_request_finished.emit(callback_id, reply.error(), data_str)
        else:
            self.http_request_finished.emit(callback_id, reply.error(), '')
        reply.deleteLater()

    @pyqtSlot(QVariant)
    def log_message(self, message):
        logger.info('js: {}'.format(message))

    @pyqtSlot(QVariant)
    def log_error(self, message):
        logger.error('js: {}'.format(message))

    @pyqtProperty(QVariant)
    def job(self):
        return self.parent.current_job.dict()

    @pyqtSlot(int, str)
    def http_request(self, callback_id, url):
        qnetwork_reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
        qnetwork_reply.finished.connect(lambda: self.http_response(callback_id, qnetwork_reply))

    @pyqtProperty(str)
    def current_state(self):
        if self.parent.current_job.state:
            return self.parent.current_job.state
        else:
            return 'main'

    @pyqtSlot()
    def done(self):
        self.parent.reset()

    @pyqtSlot(QVariant)
    def load(self, job_dict):
        if self.parent.current_job:
            self.parent.new_job.emit(self.parent.current_job.new_state(**job_dict))
        else:
            logger.error('Invalid State. load called when no current job')


class WebPageCustom(QWebPage):
    job_finished = pyqtSignal()
    new_job = pyqtSignal(Job)
    controller_js_file = 'controller.js'
    cache_directory_name = 'cache'
    js_lib_string_list = None
    global_settings_set = False

    @staticmethod
    def setup_global_settings():
        if not WebPageCustom.global_settings_set:
            settings = QWebSettings.globalSettings()
            settings.enablePersistentStorage('{base}/{cache}'.format(base=BASE_PROJECT_DIR, cache=WebPageCustom.cache_directory_name))
            settings.setMaximumPagesInCache(1)
            settings.setAttribute(QWebSettings.DnsPrefetchEnabled, False)
            settings.setAttribute(QWebSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebSettings.JavaEnabled, False)
            settings.setAttribute(QWebSettings.PluginsEnabled, False)
            settings.setAttribute(QWebSettings.JavascriptCanOpenWindows, False)
            settings.setAttribute(QWebSettings.JavascriptCanCloseWindows, False)
            settings.setAttribute(QWebSettings.JavascriptCanAccessClipboard, False)
            settings.setAttribute(QWebSettings.DeveloperExtrasEnabled, False)
            settings.setAttribute(QWebSettings.SpatialNavigationEnabled, False)
            settings.setAttribute(QWebSettings.OfflineStorageDatabaseEnabled, True)
            settings.setAttribute(QWebSettings.OfflineWebApplicationCacheEnabled, True)
            settings.setAttribute(QWebSettings.LocalStorageEnabled, True)
            settings.setAttribute(QWebSettings.AcceleratedCompositingEnabled, False)
            settings.setAttribute(QWebSettings.NotificationsEnabled, False)
            WebPageCustom.global_settings_set = True

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
        self.setup_global_settings()
        self.current_job = None
        self.injected = False
        self.setViewportSize(size)
        self.control = JSControllerObject(self)
        # self.mainFrame().javaScriptWindowObjectCleared.connect(lambda: logger.debug('javaScriptWindowObjectCleared in Main Frame'))
        # self.loadStarted.connect(lambda: logger.debug('Load started for {}'.format(self.current_job)))
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
        self.injected = False
        self.settings().resetAttribute(QWebSettings.AutoLoadImages)
        self.mainFrame().setHtml("<html><head><title></title></head><body></body></html>")
        self.access_manager.reset()
        self.job_finished.emit()

    def inject_job(self):
        if not self.current_job:
            return

        if self.injected:
            return

        self.injected = True

        logger.debug('Injecting Scripts')
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
            logger.warning('The load was unsuccessful. Injecting anyway: {}'.format(self.current_job))

        self.inject_job()

    def load_job(self, job):
        logger.debug('Running job request {}'.format(job))
        if not job.file:
            logger.error('No Job file specified {}'.format(job))

        self.current_job = job
        self.control.state = self.current_job.state

        if self.current_job.filter_list:
            self.access_manager.setFilter(self.current_job.filter_list)

        if self.current_job.block_images:
            self.settings().setAttribute(QWebSettings.AutoLoadImages, False)

        self.access_manager.setPageProxy(self.current_job.proxy, self.current_job.proxy_auth)

        if self.current_job.url:
            qurl = QUrl(self.current_job.url)
            if not qurl.isValid():
                logger.error('Invalid URL {}'.format(self.current_job.url))
                self.reset()
                return

            self.mainFrame().load(qurl)
        else:
            self.inject_job()
