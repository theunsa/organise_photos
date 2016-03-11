#!/usr/bin/env python
import os
import sys
import time
import logging
import hashlib
from datetime import datetime
from PIL import Image


PHOTO_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.svg']


logger = logging.getLogger()


def setup_logger():
    logfilename = time.strftime(
        'organise-photos-%Y%m%d_%Hh%Mm%S.log', time.localtime())
    logging.basicConfig(filename=logfilename, level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)


def create_year_dir(year):
    if not os.path.exists(year):
        os.mkdir(year)
        logger.info("Created year dir '%s'", year)


def create_month_dir(year, month):
    month_dir = '{}/{}'.format(year, month)
    if not os.path.exists(month_dir):
        os.chdir(year)
        os.mkdir(month)
        os.chdir('..')
        logger.info("Created month dir '%s'", month_dir)


if __name__ == "__main__":

    # TODO: Use argparser
    use_file_creation_time = False

    if len(sys.argv) != 2:
        print "Error! Please specify directory to process."
        sys.exit(1)

    photo_dir = sys.argv[1]
    if not os.path.isdir(photo_dir):
        print "Error! '{}' is not a directory.".format(photo_dir)
        sys.exit(2)

    print "---- Start ----"
    setup_logger()

    os.chdir(photo_dir)
    files = os.listdir('.')
    photos = [f.lower() for f in files
              if os.path.splitext(f.lower())[1] in PHOTO_FORMATS]
    for photo_filename in photos:
        ext = os.path.splitext(photo_filename)[1]
        img = None
        create_datetime = ''
        try:
            img = Image.open(photo_filename)
            # EXIF tag for image creation date field:
            # http://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
            if hasattr(img, '_getexif'):
                img_exif = img._getexif()
                if img_exif:
                    create_datetime = img_exif.get(36867, '')
                else:
                    logger.warn("Error reading photo file '{}'! "
                                "No EXIF content.".format(photo_filename))
            else:
                logger.warn("Error reading photo file '{}'! No EXIF method."
                            .format(photo_filename))
        except IOError:
            logger.exception("Unable to open photo file!")
        finally:
            if img:
                img.close()
        if not create_datetime:
            if use_file_creation_time:
                logger.info("Using file creation time for '%s'",
                            photo_filename)
                dt = datetime.fromtimestamp(os.path.getmtime(photo_filename))
                # Set it in same format as the EXIF tag would have been
                create_datetime = (
                    "{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}"
                    .format(dt.year, dt.month, dt.day,
                            dt.hour, dt.minute, dt.second)
                )
            else:
                continue
        year, month, day = create_datetime.split(' ')[0].split(':')
        hour, minute, second = create_datetime.split(' ')[1].split(':')
        new_photo_name = "{}{}{}_{}{}{}{}".format(
            year, month, day, hour, minute, second, ext)
        new_photo_filename = os.path.join(year, month, new_photo_name)
        # If the new filename already exists (multiple photos in 1 sec) then
        # add a hash to the end
        if os.path.isfile(new_photo_filename):
            md5 = '_' + hashlib.md5(photo_filename).hexdigest()[0:4]
            new_photo_name = "{}{}{}_{}{}{}{}{}".format(
                year, month, day, hour, minute, second, md5, ext)
            new_photo_filename = os.path.join(year, month, new_photo_name)
        # Create the dirs and move the file
        create_year_dir(year)
        create_month_dir(year, month)
        logger.info("Moving '{}' -> '{}'"
                    .format(photo_filename, new_photo_filename))
        os.rename(photo_filename, new_photo_filename)


    print "---- End ----"
