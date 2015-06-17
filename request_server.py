import asyncio
import threading
from aiohttp import web
from PyQt5.QtCore import QObject, pyqtSignal


class RequestServer(QObject):
    job_request = pyqtSignal(dict)

    def __init__(self, parent=None, port=8080):
        super().__init__(parent)
        self.port = port

        self.server_thread = None
        self.loop = None
        self.handler = None
        self.app = None
        self.server = None
        self.started = False

    @asyncio.coroutine
    def handle(self, request):
        data = yield from request.json()
        self.job_request.emit(data)
        return web.Response()

    @asyncio.coroutine
    def init(self, loop):
        self.app = web.Application(loop=loop)
        self.app.router.add_route('POST', '/get_html', self.handle)
        self.handler = self.app.make_handler()
        srv = yield from loop.create_server(self.handler, '127.0.0.1', self.port)
        print("Server started at http://127.0.0.1:8080")
        return srv

    def stop(self):
        self.loop.run_until_complete(self.handler.finish_connections(1.0))
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.run_until_complete(self.app.finish())

    def start_loop(self):
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def start(self):
        if not self.started:
            self.loop = asyncio.get_event_loop()
            self.server = self.loop.run_until_complete(self.init(self.loop))
            self.server_thread = threading.Thread(target=self.start_loop)
            self.server_thread.start()
            self.started = True
