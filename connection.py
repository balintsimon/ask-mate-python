import csv
import data_manager

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


def add_new_data(filename, new_story, list_of_headers):
    """Adds new question or answer to the csv file"""

    with open(filename, 'a') as csv_file:
        fieldnames = list_of_headers
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(new_story)

# def edit_data(filename, list_of_headers):
#     with open(filename, 'w') as csv_file:
#         csv_writer = csv.DictWriter(file_to_update, fieldnames=list_of_headers)
#         csv_writer.writeheader()
#         for line in :
#             if updated_story['id'] in story['id']:
#                 story['acceptance_criteria'] = story['acceptance_criteria'].replace('\n', '<br>')
#                 story['user_story'] = story['user_story'].replace('\n', '<br>')
#             csv_writer.writerow(story)