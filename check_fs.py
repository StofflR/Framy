import sys
import os
import time
import argparse
import threading
from Handler import Handler, FileModified
import datetime


def isObexRunning():
    return os.popen("pgrep obexpushd").read() != ''


def startObex(bluetooth_folder):
    os.system("sudo obexpushd -B23 -o "+bluetooth_folder+" -n &")


def replug(timeoutStart, timeout):
    while abs(timeoutStart.timedelta(datetime.datetime.now()).seconds) < timeout:
        pass
    os.execl(sys.executable, sys.executable, *sys.argv)


def plug(target, mount):
    mount()
    command = "sudo modprobe g_mass_storage file="+target+" stall=0 removable=1"
    print("Executing: " + command)
    os.system(command)


def unplug(unmount):
    command = "sudo modprobe -r g_mass_storage"
    print("Executing: " + command)
    os.system(command)
    if unmount is not None:
        unmount()


def main():
    parser = argparse.ArgumentParser(
        prog='CatroZero file  watchdog',
        description='Moves incomming files to different folders!',
        epilog='Text at the bottom of help')

    parser.add_argument(
        '-t', '--timeout', metavar="(0s-600s)", help="Timeout until next replug is possible", type=int, choices=range(1, 600), default=10)
    parser.add_argument(
        '-r', '--retries', metavar="(0-1000)", help="Retries starting obex server", type=int, choices=range(1, 1000), default=100)
    parser.add_argument('-b', '--bluetooth', metavar="path",
                        help="Path to bluetooth storage folder", default=os.getcwd()+"/bluetooth")
    parser.add_argument('-w', '--wifi', metavar="path",
                        help="Path to wifi storage folder", default=os.getcwd()+"/wifi")
    parser.add_argument('-o', '--output', metavar="path",
                        help="Path for file target folder", required=True)
    parser.add_argument(
        '-u', '--usb', metavar="USB mass storage target", required=True)
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
    print("Bluetooth source: ", args.bluetooth, "\nWifi source: ",
          args.wifi, "\nTimeout: ",  args.timeout, "\nTarget folder: ", args.output)

    def mount():
        command = "mount "+args.usb+" "+args.output
        print("Executing: " + command)
        os.system(command)

    def unmount():
        command = "umount "+args.output
        print("Executing: " + command)
        os.system(command)

    replugLock = threading.Lock()
    largeFileLock = threading.Lock()
    wifiFiles = FileModified(storeop=True)
    blFiles = FileModified()

    blHandler = Handler(source=args.bluetooth, target=args.wifi,
                        actionLock=replugLock,  addTimeTag=True, changed=blFiles)
    wifiHandler = Handler(source=args.wifi, target=args.output,
                          actionLock=replugLock,  addTimeTag=False, changed=wifiFiles, largeFileLock=largeFileLock)
    blHandler.start()
    wifiHandler.start()
    print("Initializing file system!")
    # TODO: handle files modified from usb side
    plug(args.usb, mount)
    unplug(None)
    time.sleep(args.timeout)
    plug(args.usb, mount)
    print("Started Watching!")
    try:
        previousState = False
        while wifiHandler.alive and blHandler.alive:
            if previousState != wifiFiles.modified:
                previousState = wifiFiles.modified
                print("Files modified!")
            wifiHandler.timeout_lock.acquire()
            if ((datetime.datetime.now() - wifiHandler.timeout_start).total_seconds() > args.timeout) and wifiFiles.modified:
                print("Restarting watchdog!")
                # blHandler.stop()
                # wifiHandler.stop()
                print("Stopped Watching!")
                while not len(wifiFiles.operations) == 0:
                    op = wifiFiles.operations.pop(0)
                    print("Executing: " + op)
                    os.system(op)
                unplug(unmount)
                os.execl(sys.executable, sys.executable, *sys.argv)
            elif wifiFiles.modified:
                print("Replug in: " + str(round(args.timeout -
                      (datetime.datetime.now() - wifiHandler.timeout_start).total_seconds())))
            wifiHandler.timeout_lock.release()
            time.sleep(args.timeout / 10)

    except KeyboardInterrupt:
        # blHandler.stop()
        # wifiHandler.stop()
        pass
    blHandler.join()
    wifiHandler.join()

    print("Stopped Watching!")
    # replug(now, args.timeout)


if __name__ == '__main__':
    main()
