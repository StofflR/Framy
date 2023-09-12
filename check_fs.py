import sys
import os
import time
import argparse
import threading
from Handler import Handler, FileModified


def isObexRunning():
    return os.popen("pgrep obexpushd").read() != ""


def startObex(bluetooth_folder):
    os.system("sudo obexpushd -B23 -o " + bluetooth_folder + " -n &")


def main():
    parser = argparse.ArgumentParser(
        prog="CatroZero file  watchdog",
        description="Moves incomming files to different folders!",
        epilog="Text at the bottom of help",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        metavar="(0s-600)",
        help="Timeout until next replug is possible",
        type=int,
        choices=range(1, 600),
        default=10,
    )
    parser.add_argument(
        "-r",
        "--retries",
        metavar="(0-1000)",
        help="Retries starting obex server",
        type=int,
        choices=range(1, 1000),
        default=100,
    )
    parser.add_argument(
        "-b",
        "--bluetooth",
        metavar="path",
        help="Path to bluetooth storage folder",
        default=os.getcwd() + "/wifi/static",
    )
    parser.add_argument(
        "-w",
        "--wifi",
        metavar="path",
        help="Path to wifi storage folder",
        default=os.getcwd() + "/wifi",
    )
    args = parser.parse_args()

    print("Checking Obex")
    retry = 0
    while not isObexRunning() and retry < args.retries:
        print("Starting Obex")
        if retry != 0:
            time.sleep(args.timeout)
        startObex(args.bluetooth)
        retry += 1
    print("Obex started")
    print("Starting Watching")
    print(
        "Bluetooth source: ",
        args.bluetooth,
        "\nWifi source: ",
        args.wifi,
        "\nTimeout: ",
        args.timeout,
        "\nTarget folder: ",
        args.wifi + "/static",
    )

    replugLock = threading.Lock()
    blFiles = FileModified()

    blHandler = Handler(
        source=args.wifi, target=args.bluetooth, actionLock=replugLock, changed=blFiles
    )
    blHandler.start()
    print("Initializing file system!")
    print("Started Watching!")
    try:
        blHandler.join()
    except KeyboardInterrupt:
        print("Stopped Watching!")
        os.execl(sys.executable, sys.executable, *sys.argv)
        pass
    print("Stopped Watching!")
    os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == "__main__":
    main()
