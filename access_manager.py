from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkProxyFactory, QNetworkProxy

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

    def createRequest(self, operation, request, device):
        logger.debug('{} : {} : {}'.format(operation, request.url(), device))
        return super().createRequest(operation, request, device)