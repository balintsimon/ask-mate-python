import os
from datetime import datetime
import calendar
import csv

from werkzeug.utils import secure_filename

import connection

LIST_START = 0


def sort_array(array, key, reverse):
    """sorts a dictionary by given keyname

    ARGS:
        array(dictionary)
        key(string): key of dictionary, you want to sort by
        reverse(boolean): sorting is reversed (True) or not (False)
    """

    array = sorted(array, key=lambda x: x[key], reverse=reverse)
    return array


def convert_unix_time_to_readable(input_time):
    return datetime.fromtimestamp(int(input_time))


def get_unix_time():
    date_time = datetime.utcnow()
    return (calendar.timegm(date_time.utctimetuple()))


def generate_id(filename):
    """
    with open(filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data_id = sum(1 for row in csv_reader)
        return data_id
    """
    actual_stories = connection.read_file(filename)
    if len(actual_stories) == 1:
        return LIST_START

    return int(actual_stories[-1]["id"]) + 1


def handle_file_upload(files, path):
    if files:
        image = files["image"]

        if image.filename != "":
            # return redirect(referrer) # error

            if allowed_image(image.filename, app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                filename = secure_filename(image.filename)
                image.save(os.path.join(path, filename))
                print("Image saved")
                return filename
            else:
                print("not allowed image")

    return False


def allowed_image(filename, extensions):
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1]
    return ext.upper() in extensions

