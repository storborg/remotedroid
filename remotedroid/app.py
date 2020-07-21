import logging

import io
import time
import asyncio
import pkg_resources

from PIL import Image
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
        scale = 0.5
        width = int(1440 * scale)
        height = int(2960 * scale)
        cmd = [
            "adb shell screenrecord",
            "--size=%dx%d" % (width, height),
            "--output-format=raw-frames -",
        ]
        cmd = " ".join(cmd)

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE,
        )
        bytes_per_frame = width * height * 3
        last_time = time.perf_counter()
        while True:
            buf = await proc.stdout.readexactly(bytes_per_frame)
            compression_start = time.perf_counter()
            image = Image.frombytes("RGB", (width, height), buf, "raw")
            output = io.BytesIO()
            image.save(output, format="JPEG")
            outbuf = output.getvalue()
            compression_elapsed = time.perf_counter() - compression_start
            log.warn(
                "compressed image in %0.2f ms", compression_elapsed * 1000
            )
            log.debug("pushing screenshot, %d bytes" % len(outbuf))
            # push to all connected client queues
            for q in self.screenshot_queues:
                await q.put(outbuf)
            now = time.perf_counter()
            elapsed = now - last_time
            last_time = now
            log.info("perf %0.1f fps", 1 / elapsed)

    def index_route(self, request):
        return self.templates.TemplateResponse(
            "index.html",
            {"name": self.name, "serial": self.serial, "request": request},
        )

    async def screenshot_endpoint(self, ws):
        log.info("New screenshot endpoint connection: %s", ws.client.host)
        await ws.accept()
        try:
            q = asyncio.Queue()
            self.screenshot_queues.add(q)
            while True:
                img = await q.get()
                with open("/tmp/foo.png", "wb") as f:
                    f.write(img)
                await ws.send_bytes(img)
        finally:
            self.screenshot_queues.remove(q)
            await ws.close()

    async def handle_input(self, cmd):
        log.info("Handling control command: %s", cmd)
        proc = await asyncio.create_subprocess_shell(
            "adb shell input " + cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def control_endpoint(self, ws):
        log.info("New control endpoint connection: %s", ws.client.host)
        await ws.accept()
        try:
            while True:
                # accept touch commands from here
                msg = await ws.receive_json()
                if msg["type"] == "tap":
                    cmd = "tap %s %s" % (msg["x"], msg["y"])
                elif msg["type"] == "swipe":
                    cmd = "swipe %s %s %s %s %s" % (
                        msg["x1"],
                        msg["y1"],
                        msg["x2"],
                        msg["y2"],
                        msg["duration"],
                    )
                else:
                    raise Exception(
                        "unrecognized control command type: %s" % cmd["type"]
                    )
                await self.handle_input(cmd)
        finally:
            await ws.close()
