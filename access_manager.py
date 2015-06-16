from PyQt5.QtCore import QUrl
from collections import namedtuple
import re
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkProxyFactory, QNetworkProxy, QNetworkRequest

import logging
logger = logging.getLogger(__name__)


class ProxyManager(QNetworkProxyFactory):
    no_proxy = (QNetworkProxy(),)

    def __init__(self, access_manager):
        super().__init__()
        self.access_manager = access_manager

    def queryProxy(self, query=None, *args, **kwargs):
        if self.access_manager.proxy is not None:
            return self.access_manager.proxy
        return ProxyManager.no_proxy


class AccessManager(QNetworkAccessManager):
    Rule = namedtuple('Rule', ['rule_type', 'rule'])
    _allow = 'allow'
    _reject = 'reject'

    def __init__(self, parent):
        super().__init__(parent)

        self.rule_list = []
        self.proxy = None
        self.proxy_factory = ProxyManager(self)
        self.setProxyFactory(self.proxy_factory)

    def setPageProxy(self, proxy_string, auth_string):
        if not proxy_string:
            return

        pr = proxy_string.split(':', 1)
        if len(pr) != 2:
            logger.error('Invalid proxy string {}, auth {}'.format(proxy_string, auth_string))
            return
        host = pr[0]
        port = int(pr[1])

        if not (host and port):
            logger.error('Invalid proxy string {}, auth {}'.format(proxy_string, auth_string))
            return

        if auth_string:
            aus = auth_string.split(':', 1)
            if len(aus) != 2:
                logger.error('Invalid proxy string {}, auth {}'.format(proxy_string, auth_string))
                return
            user = aus[0]
            pasw = aus[1]

            self.proxy = [QNetworkProxy(QNetworkProxy.HttpProxy, host, port, user, pasw)]
        else:
            self.proxy = [QNetworkProxy(QNetworkProxy.HttpProxy, host, port)]

    def reset(self):
        self.rule_list = []
        self.proxy = None

    def createRequest(self, operation, request, device):
        url_str = request.url().toString()

        if self.rule_list:
            for r in self.rule_list:
                if r.rule.search(url_str):
                    if r.rule_type == self._reject:
                        logger.debug('blocking {}'.format(url_str))
                        return super().createRequest(operation, QNetworkRequest(QUrl()), device)
                    else:
                        break
        return super().createRequest(operation, request, device)

    def setWhiteListFilter(self, filter_str_list):
        for filter_str in filter_str_list:
            if filter_str:
                self.whitelst_filter_list.append(re.compile(filter_str))

    def setFilter(self, filter_str_list):
        for filter_str in filter_str_list:
            filter_conf = filter_str.split(':', 1)

            if len(filter_conf) != 2:
                logger.error('Invalid filter string {}'.format(filter_str))
                return

            rule_type = filter_conf[0]
            if not (rule_type == self._allow or rule_type == self._reject):
                logger.error('Invalid filter string {}'.format(filter_str))
                return

            rule_str = filter_conf[1]
            if not rule_str:
                logger.error('Invalid filter string {}'.format(filter_str))
                return

            self.rule_list.append(self.Rule(rule_type, re.compile(rule_str)))