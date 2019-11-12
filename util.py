

def sort_array(array, key, reverse):
    """sorts a dictionary by given keyname

    ARGS:
        array(dictionary)
        key(string): key of dictionary, you want to sort by
        reverse(boolean): sorting is reversed (True) or not (False)
    """

    array = sorted(array, key=lambda x: x[key], reverse=reverse)
    return array
