# RemoteDroid

Offers a web interface to remotely control an Android GUI. Uses adb for screenshots and control commands.

## Quick Start

Connect your device, verify that it works:

    adb devices

Also works with adb-over-TCP.

Start server:

    remotedroid

Access http://localhost:8080 in a browser.

For more options:

    remotedroid --help
