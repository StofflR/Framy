import sys
import os
import time
import argparse
import threading
import datetime
from ImageConverter import Device, Converter
import random
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEVICES = [Device.WS7in, Device.Inky, Device.Unknown]


def isObexRunning():
    return os.popen("pgrep obexpushd").read() != ""

def restricted_float(x):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError("%r not a floating-point literal" % (x,))

    if x < 0.0 or x > 1.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
    return x
    
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

def getRandomImagePath(dir_path, valid_extensions=('jpg', 'jpeg', 'png')):
    """
    Get a random image file in the given directory
    """

    # get filepaths of all files and dirs in the given dir
    valid_files = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]
    # filter out directories, no-extension, and wrong extension files
    valid_files = [f for f in valid_files if '.' in f and \
                   f.rsplit('.', 1)[-1] in valid_extensions and os.path.isfile(f)]
    if not valid_files:
        return None

    return random.choice(valid_files)

def updateImage(device, saturation, image_path):
    if image_path is None:
        print("No image found to update")
        return
    print(f"Updating image: {image_path}")
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

                inky = InkyUC8159(resolution=(640, 400))
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

def updateRandomImage(device, folder):
    print("Updating random image...")
    if not os.path.exists(folder):
        print(f"Folder does not exist: {folder}")
        return
    image_path = getRandomImagePath(folder)
    if image_path is None:
        print("No random image found to update")
        return
    print(f"Updating random image: {image_path}")
    try:
        Himage = Image.open(image_path)
        if device == Device.WS7in or device == DEVICES[-1]:
            try:
                from waveshare_epd import epd7in3f
                print("epd7in3f Demo")
                epd = epd7in3f.EPD()
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
                inky.set_image(Himage)
                inky.show()
                exit(0)
            except Exception as e:
                raise (e)
    except IOError as e:
        print(e)

def wait_for_file_complete(file_path, stable_time=7, timer=None):
    """
    Wait until the file size remains stable for stable_time seconds
    to ensure the transfer is complete
    """
    if not os.path.exists(file_path):
        return False
    
    # Pause the timer if provided
    if timer is not None:
        timer.cancel()
    
    previous_size = -1
    stable_duration = 0
    
    while stable_duration < stable_time:
        try:
            current_size = os.path.getsize(file_path)
            if current_size == previous_size:
                time.sleep(2)
                stable_duration += 2
            else:
                previous_size = current_size
                stable_duration = 0
                time.sleep(2)
        except OSError:
            return False
    
    return True

class ImageFileHandler(FileSystemEventHandler):
    """Handles file system events for new image files"""
    
    def __init__(self, device, saturation, bluetooth_folder, wifi_folder, timer=None):
        self.device = device
        self.saturation = saturation
        self.bluetooth_folder = bluetooth_folder
        self.wifi_folder = wifi_folder
        self.valid_extensions = ('jpg', 'jpeg', 'png')
        self.timer = timer
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if it's a valid image file
        if '.' in file_path and file_path.rsplit('.', 1)[-1].lower() in self.valid_extensions:
            print(f"New file detected: {file_path}")
            
            # Wait for file transfer to complete
            print("Waiting for file transfer to complete...")
            if wait_for_file_complete(file_path, timer=self.timer):
                print("File transfer complete. Updating image...")
                
                # Add time to file name to avoid caching issues
                base, ext = os.path.splitext(file_path)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                new_file_path = f"{base}_{timestamp}{ext}"
                os.rename(file_path, new_file_path)
                file_path = new_file_path
                
                # Update the image
                updateImage(self.device, self.saturation, file_path)
                
                # Restart the program
                print("Restarting program...")
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                print(f"Failed to confirm file transfer completion for {file_path}")

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

    # Start timer for random image update
    timer = threading.Timer(60.0, updateRandomImage, args=(args.device, "output"))
    timer.start()

    # Create event handler and observer
    event_handler = ImageFileHandler(args.device, args.saturation, args.bluetooth, args.wifi, timer)
    observer = Observer()
    print(" Device: ", "Inky" if args.device == Device.Inky else "WS7in", "\nSaturation: ", args.saturation)
    # Watch both bluetooth and wifi folders
    if os.path.exists(args.bluetooth):
        observer.schedule(event_handler, args.bluetooth, recursive=False)
        print(f"Watching bluetooth folder: {args.bluetooth}")
    else:
        print(f"Bluetooth folder does not exist: {args.bluetooth}")
    
    if os.path.exists(args.wifi):
        observer.schedule(event_handler, args.wifi, recursive=False)
        print(f"Watching wifi folder: {args.wifi}")
    else:
        print(f"Wifi folder does not exist: {args.wifi}")
    
    observer.start()
   
    try:
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped Watching!")
        observer.stop()
        observer.join()
        timer.cancel()
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    observer.stop()
    observer.join()
    print("Stopped Watching!")
    os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == "__main__":
    main()
