import csv


def read_file(filename):
    all_data = []
    with open(filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for line in csv_reader:
            all_data.append(dict(line))
        return all_data


def get_data_header(filename):
    with open(filename, 'r') as csv_file:
        data_header = csv_file.readline()
        return data_header.strip('\n').replace('_', ' ').split(',')


def add_new_data(filename, new_story):
    """Adds new question or answer to the csv file"""

    with open(filename, 'a') as csv_file:
        fieldnames = get_data_header(filename)
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(new_story)


def update_file(filename, update_story):
    existing_submits = read_file(filename)

    with open(filename, 'w') as csv_file:
        fieldnames = get_data_header(filename)
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for submit in existing_submits:
            if update_story["id"] == submit["id"]:
                submit = update_story
            writer.writerow(row)
