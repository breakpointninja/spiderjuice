# -*- coding: utf-8 -*-
import glob
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWebKit import QWebSettings
from access_manager import AccessManager

from PyQt5.QtCore import QSize, QObject, pyqtSlot, pyqtProperty, QUrl, pyqtSignal, QVariant, Qt, QTimer
from PyQt5.QtWebKitWidgets import QWebPage

import logging
from job import Job
from settings import BASE_PROJECT_DIR, DEFAULT_JOB_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class JSControllerObject(QObject):
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
        logger.info(self.prepend_id('js: {}'.format(message)))

    @pyqtSlot(QVariant)
    def log_error(self, message):
        logger.error(self.prepend_id('js: {}'.format(message)))

    @pyqtProperty(QVariant)
    def job_dict(self):
        return self.parent.current_job.dict()

    def job(self):
        return self.parent.current_job

    @pyqtSlot(int, str)
    def http_request(self, callback_id, url):
        if not self.parent.current_job:
            logger.error(self.prepend_id('Invalid State. http_request called when no current job'))
            return

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
        if not self.parent.current_job:
            logger.error(self.prepend_id('Invalid State. done called when no current job'))
            return

        logger.info(self.prepend_id('Done Job {}'.format(self.job())))

        self.parent.reset()

    @pyqtSlot()
    def abort(self):
        if not self.parent.current_job:
            logger.error(self.prepend_id('Invalid State. abort called when no current job'))
            return

        logger.error(self.prepend_id('Job aborted {}'.format(self.job())))
        self.parent.reset()

    def prepend_id(self, message):
        return '[{}] {}'.format(self.parent.id, message)

    @pyqtSlot(QVariant)
    def load(self, job_dict):
        if not self.parent.current_job:
            logger.error(self.prepend_id('Invalid State. load called when no current job'))
            return

        self.parent.new_job_received.emit(self.parent.current_job.new_state(**job_dict))


class WebPageCustom(QWebPage):
    job_finished = pyqtSignal()
    new_job_received = pyqtSignal(Job)
    controller_js_file = 'controller.js'
    cache_directory_name = 'cache'
    js_lib_string_list = None
    global_settings_set = False
    id_gen = 0

    @staticmethod
    def setup_global_settings():
        if not WebPageCustom.global_settings_set:
            settings = QWebSettings.globalSettings()
            settings.enablePersistentStorage('{base}/{cache}'.format(base=BASE_PROJECT_DIR, cache=WebPageCustom.cache_directory_name))
            settings.setMaximumPagesInCache(0)
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
        WebPageCustom.id_gen += 1
        self.id = WebPageCustom.id_gen
        self.setup_global_settings()
        self.current_job = None
        self.injected = False
        self.setViewportSize(size)
        self.control = JSControllerObject(self)

        self.timeout_timer = QTimer(self)
        self.timeout_timer.setTimerType(Qt.VeryCoarseTimer)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.setInterval(DEFAULT_JOB_TIMEOUT_SECONDS * 1000)
        self.timeout_timer.timeout.connect(self.timeout)

        self.loadFinished.connect(self.on_load_finished)
        self.access_manager = AccessManager(self)
        self.setNetworkAccessManager(self.access_manager)

    def is_busy(self):
        return bool(self.current_job)

    def javaScriptConsoleMessage(self, message, line_number, source_id):
        logger.debug(self.control.prepend_id('console:{}:{}:{}'.format(source_id, line_number, message)))

    def timeout(self):
        logger.error(self.control.prepend_id('Job timed out in {}sec - {}'.format(DEFAULT_JOB_TIMEOUT_SECONDS, self.current_job)))
        self.reset()

    def reset(self):
        self.timeout_timer.stop()
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

        logger.debug(self.control.prepend_id('Injecting Scripts'))
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
            logger.warning(self.control.prepend_id('The load was unsuccessful. Injecting anyway: {}'.format(self.current_job)))

        self.inject_job()

    def load_job(self, job):
        logger.info(self.control.prepend_id('Job Request {}'.format(job)))
        if not job.file:
            logger.error(self.control.prepend_id('No Job file specified {}'.format(job)))

        self.timeout_timer.start()

        self.current_job = job

        if self.current_job.filter_list:
            self.access_manager.set_filter(self.current_job.filter_list)

        if self.current_job.block_images:
            self.settings().setAttribute(QWebSettings.AutoLoadImages, False)

        self.access_manager.set_page_proxy(self.current_job.proxy, self.current_job.proxy_auth)

        if self.current_job.url:
            qurl = QUrl(self.current_job.url)
            if not qurl.isValid():
                logger.error(self.control.prepend_id('Invalid URL {}'.format(self.current_job.url)))
                self.reset()
                return

            self.mainFrame().load(qurl)
        else:
            self.inject_job()
