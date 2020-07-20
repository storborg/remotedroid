import logging

import asyncio
import pkg_resources

from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles

log = logging.getLogger(__name__)


templates_dir = pkg_resources.resource_filename(__name__, "templates")
static_dir = pkg_resources.resource_filename(__name__, "static")


class RemoteDroidApp(Starlette):
    def __init__(self, name, serial=None, debug=False):
        self.name = name
        self.serial = serial
        self.templates = Jinja2Templates(directory=templates_dir)
        self.screenshot_queues = set()

        routes = [
            Route("/", self.index_route),
            WebSocketRoute("/ws/screenshots", self.screenshot_endpoint),
            WebSocketRoute("/ws/control", self.control_endpoint),
            Mount("/static", StaticFiles(directory=static_dir), name="static"),
        ]

        Starlette.__init__(self, debug=debug, routes=routes)

        async def startup_handler():
            asyncio.ensure_future(self.screenshot_task())

        self.add_event_handler("startup", startup_handler)

    async def screenshot_task(self):
        while True:
            proc = await asyncio.create_subprocess_shell(
                "adb shell screencap -p",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            log.warn("got %d bytes to stdout" % len(stdout))
            # push to all connected client queues
            for q in self.screenshot_queues:
                await q.put(stdout)

    def index_route(self, request):
        return self.templates.TemplateResponse(
            "index.html",
            {"name": self.name, "serial": self.serial, "request": request,},
        )

    async def screenshot_endpoint(self, ws):
        await ws.accept()
        try:
            q = asyncio.Queue()
            self.screenshot_queues.add(q)
            while True:
                img = await q.get()
                log.warn("sending %d bytes to %s" % (len(img), ws))
                with open("/tmp/foo.png", "wb") as f:
                    f.write(img)
                await ws.send_bytes(img)
        finally:
            self.screenshot_queues.remove(q)
            await ws.close()

    async def control_endpoint(self, ws):
        await ws.accept()
        try:
            # accept touch commands from here
            cmd = await ws.receive_json()
            log.warn("got a command from %s: %s", ws, cmd)
        finally:
            await ws.close()
