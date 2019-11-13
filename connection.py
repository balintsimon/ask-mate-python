import csv

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]


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


def update_file(filename, new_dataset, adding=True):
    existing_submits = read_file(filename)
    open_option = "a" if adding is True else "w"

    with open(filename, open_option) as csv_file:
        fieldnames = QUESTION_HEADERS if "question" in filename else ANSWER_HEADERS
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if adding is True:
            writer.writerow(new_dataset)

        else:
            writer.writeheader()
            for submit in existing_submits:
                if new_dataset["id"] == submit["id"]:
                    submit = new_dataset
                writer.writerow(submit)

def delete_question(filename, q_id):
    """rewrites the entire csv excluding the given ids"""
    content = read_file(filename)

    with open(filename, "w+") as f:
        writer = csv.DictWriter(f, fieldnames=QUESTION_HEADERS, delimiter=',')
        writer.writeheader()
        for question in content:
            if question['id'] != q_id:
                writer.writerow(question)


def delete_answers(filename, q_id):
    content = read_file(filename)

    with open(filename, "w+") as f:
        writer = csv.DictWriter(f, fieldnames=ANSWER_HEADERS, delimiter=',')
        writer.writeheader()
        for answer in content:
            if answer['question_id'] != q_id:
                writer.writerow(answer)