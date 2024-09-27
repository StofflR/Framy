import sys
import os
import time
import argparse
import threading
from Handler import Handler, FileModified
import datetime
from ImageConverter import Device, Converter

DEVICES = [Device.WS7in, Device.Inky, Device.Unknown]


def isObexRunning():
    return os.popen("pgrep obexpushd").read() != ""


def startObex(bluetooth_folder):
    os.system("sudo obexpushd -B23 -o " + bluetooth_folder + " -n &")

def restricted_float(x):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError("%r not a floating-point literal" % (x,))

    if x < 0.0 or x > 1.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
    return x


def getImagePath(dir_path, valid_extensions=('jpg', 'jpeg', 'png')):
    """
    Get the latest image file in the given directory
    """

    # get filepaths of all files and dirs in the given dir
    valid_files = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]
    # filter out directories, no-extension, and wrong extension files
    valid_files = [f for f in valid_files if '.' in f and \
                   f.rsplit('.', 1)[-1] in valid_extensions and os.path.isfile(f)]

    if not valid_files:
        return None

    return max(valid_files, key=os.path.getmtime)


def updateImage(device, saturation, folder):
    image_path = getImagePath(folder)
    if image_path is None:
        return
    try:
        if device == Device.WS7in or device == DEVICES[-1]:
            try:
                from waveshare_epd import epd7in3f

                print("epd7in3f Demo")
                epd = epd7in3f.EPD()
                Himage = Converter(
                    epd.width, epd.height, image_path, saturation, Device.WS7in
                ).convert()
                print("init and Clear")
                epd.init()
                epd.Clear()
                # Drawing on the image
                print("1.Drawing on the image...")
                epd.display(epd.getbuffer(Himage))
                print("Goto Sleep...")
                epd.sleep()
            except KeyboardInterrupt:
                print("ctrl + c:")
                epd7in3f.epdconfig.module_exit()
            exit(0)
        elif device == Device.Inky or device == DEVICES[-1]:
            try:
                from inky.auto import InkyUC8159  # noqa: F401

                inky = InkyUC8159(resolution=(600, 448))
                Himage = Converter(
                    inky.width, inky.height, image_path, saturation, Device.Inky
                ).convert()
                inky.set_image(Himage)
                inky.show()
                exit(0)
            except Exception as e:
                raise (e)
    except IOError as e:
        print(e)


def main():
    parser = argparse.ArgumentParser(
        prog="CatroZero file  watchdog",
        description="Moves incomming files to different folders!",
        epilog="Text at the bottom of help",
    )

    parser.add_argument(
        '-t', '--timeout', metavar="(0s-600s)", help="Timeout until next replug is possible", type=int,
        choices=range(1, 600), default=10)
    parser.add_argument(
        '-r', '--retries', metavar="(0-1000)", help="Retries starting obex server", type=int, choices=range(1, 1000),
        default=100)
    parser.add_argument('-b', '--bluetooth', metavar="path",
                        help="Path to bluetooth storage folder", default=os.getcwd() + "/bluetooth")
    parser.add_argument('-w', '--wifi', metavar="path",
                        help="Path to wifi storage folder", default=os.getcwd() + "/wifi")

    parser.add_argument(
        "-d",
        "--device",
        metavar="string",
        choices=DEVICES,
        help="Device type",
        default=Device.WS7in,
    )
    parser.add_argument(
        "-s",
        "--saturation",
        metavar="float",
        type=restricted_float,
        help="Image saturation (0.0-1.0)",
        default=0.5,
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
    print("Bluetooth source: ", args.bluetooth, "\nWifi source: ",
                 args.wifi, "\nTimeout: ", args.timeout)

    replugLock = threading.Lock()
    largeFileLock = threading.Lock()
    wifiFiles = FileModified(storeop=True)
    blFiles = FileModified()

    blHandler = Handler(source=args.bluetooth, target=args.wifi,
                        actionLock=replugLock,  changed=blFiles)
    wifiHandler = Handler(source=args.wifi, target=None,
                          actionLock=replugLock,  changed=wifiFiles, largeFileLock=largeFileLock)
    blHandler.start()
    print("Initializing file system!")
    # TODO: handle files modified from usb side
    time.sleep(args.timeout/2)
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
                updateImage(args.device, args.saturation, args.wifi)
                os.execl(sys.executable, sys.executable, *sys.argv)
            elif wifiFiles.modified:
                print("Replug in: " + str(round(args.timeout -
                      (datetime.datetime.now() - wifiHandler.timeout_start).total_seconds())))
            wifiHandler.timeout_lock.release()
            time.sleep(args.timeout / 10)

    except KeyboardInterrupt:
        print("Stopped Watching!")
        os.execl(sys.executable, sys.executable, *sys.argv)
        pass
    print("Stopped Watching!")
    os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == "__main__":
    main()
