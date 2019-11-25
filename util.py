from datetime import datetime
import calendar
import csv
import connection
import data_manager

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
    return(calendar.timegm(date_time.utctimetuple()))


def generate_id(filename):
    """
    with open(filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data_id = sum(1 for row in csv_reader)
        return data_id
    """
    actual_stories = data_manager.read_file(filename)
    if len(actual_stories) == 1:
        return LIST_START

    return int(actual_stories[-1]["id"]) + 1
