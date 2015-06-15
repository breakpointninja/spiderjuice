from PyQt5.QtCore import QUrl
import re
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkProxyFactory, QNetworkProxy, QNetworkRequest

import logging
logger = logging.getLogger(__name__)


class ProxyManager(QNetworkProxyFactory):
    no_proxy = (QNetworkProxy(),)

    def queryProxy(self, query=None, *args, **kwargs):
        logger.debug('Proxy Query: {}'.format(query.url()))
        return ProxyManager.no_proxy

class AccessManager(QNetworkAccessManager):
    def __init__(self, parent):
        super().__init__(parent)
        self.proxy_factory = ProxyManager()
        self.setProxyFactory(self.proxy_factory)
        self.blocking_filter_list = []

    def reset(self):
        self.blocking_filter_list = []

    def createRequest(self, operation, request, device):
        logger.debug('{} : {} : {}'.format(operation, request.url(), device))

        if self.blocking_filter_list:
            for filter in self.blocking_filter_list:
                if filter.match(request.url().toString()):
                    logger.debug('Blocking {}'.format(request.url()))
                    return super().createRequest(operation, QNetworkRequest(QUrl()), device)
        return super().createRequest(operation, request, device)


    def setBlockingFilter(self, filter_str_list):
        for filter_str in filter_str_list:
            if filter_str:
                self.blocking_filter_list.append(re.compile(filter_str))