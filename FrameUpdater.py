#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import argparse
from ImageConverter import Converter, Device
import os
from os.path import join, isfile
import shutil
import filetype
import sys
import numpy as np


def restricted_float(x):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError("%r not a floating-point literal" % (x,))

    if x < 0.0 or x > 1.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]" % (x,))
    return x


DEVICES = [Device.WS7in, Device.Inky, "unknown"]
logging.basicConfig(level=logging.DEBUG)
parser = argparse.ArgumentParser(
    prog="Framy Updater",
    description="Display provided image!",
    epilog="Text at the bottom of help",
)
parser.add_argument(
    "-f", "--files", metavar="path", help="Path to image files", required=True
)
parser.add_argument(
    "-d",
    "--device",
    metavar="string",
    choices=DEVICES,
    help="Device type",
    default=DEVICES[-1],
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


def clearStatic():
    for filename in os.listdir(args.files + "/static"):
        file_path = os.path.join(args.files + "/static", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


def updateImage(img):
    try:
        if args.device == Device.WS7in or args.device == DEVICES[-1]:
            try:
                from waveshare_epd import epd7in3f

                logging.info("epd7in3f Demo")
                epd = epd7in3f.EPD()
                Himage = Converter(
                    epd.width, epd.height, img, args.saturation, Device.WS7in
                ).convert()
                logging.info("init and Clear")
                epd.init()
                epd.Clear()
                # Drawing on the image
                logging.info("1.Drawing on the image...")
                epd.display(epd.getbuffer(Himage))
                logging.info("Goto Sleep...")
                epd.sleep()
            except KeyboardInterrupt:
                logging.info("ctrl + c:")
                epd7in3f.epdconfig.module_exit()
            exit(0)
        elif args.device == Device.Inky or args.device == DEVICES[-1]:
            try:
                from .inky_uc8159 import Inky as InkyUC8159  # noqa: F401

                inky = InkyUC8159(resolution=(600, 448))
                Himage = Converter(
                    inky.width, inky.height, img, args.saturation, Device.Inky
                ).convert()
                inky.set_image(Himage)
                inky.show()
                exit(0)
            except Exception as e:
                raise (e)
    except IOError as e:
        logging.info(e)


def getFirstImage(folder, random=False):
    first_img = next(
        (
            f
            for f in os.listdir(folder)
            if isfile(join(folder, f)) and filetype.is_image(join(folder, f))
        ),
        None,
    )
    random_file = None
    if random:
        file_count = len(
            [
                name
                for name in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, name))
            ]
        )
        random_file = next(
            (
                f
                for f in os.listdir(folder)
                if isfile(join(folder, f))
                and filetype.is_image(join(folder, f))
                and np.random.rand() < 1.0 / file_count
            ),
            None,
        )
    return random_file if random_file else first_img


def updateImageFolder(folder, random=False):
    first_file = getFirstImage(folder, random)
    if first_file:
        print(f"Found {first_file} in {folder}")
        if join(folder, first_file) != join(args.files, first_file):
            shutil.copyfile(join(folder, first_file), join(args.files, first_file))
        updateImage(join(folder, first_file))
        return True
    return False


if isfile(".update_static"):
    print("Trying to update static!")
    if updateImageFolder(args.files + "/static") or updateImageFolder(args.files):
        if os.path.exists(".update_static"):
            os.remove(".update_static")
        if os.path.exists(".update"):
            os.remove(".update")
        exit(0)
if isfile(".update") and updateImageFolder(args.files, random=True):
    print("Updated image!")
    exit(0)
