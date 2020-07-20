import logging

import sys
import argparse

import uvicorn

from .app import RemoteDroidApp

log = logging.getLogger(__name__)


def main(argv=sys.argv):
    p = argparse.ArgumentParser(
        description="Webapp to remotely control Android device via adb."
    )
    p.add_argument(
        "--name", help="Optional name to show to users",
    )
    p.add_argument(
        "-s",
        "--serial",
        help="Android serial to pass to adb (if multiple devices connected)",
    )
    p.add_argument(
        "--host", default="0.0.0.0", help="Host/address that webserver will bind to",
    )
    p.add_argument(
        "--port", type=int, default=8080, help="Port that webserver will listen on",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="Enable more verbose logging (can be repeated)",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Run with Python debugging enabled (dangerous)",
    )

    opts = p.parse_args(argv[1:])

    if opts.verbose:
        if opts.verbose > 1:
            level = logging.DEBUG
        else:
            level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(level=level)

    app = RemoteDroidApp(
        name=opts.name or "Anonymous", serial=opts.serial, debug=opts.debug,
    )

    uvicorn.run(app, host=opts.host, port=opts.port)
