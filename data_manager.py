import csv
import os
import connection
import psycopg2
import connection
import util
from datetime import datetime

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]


def get_single_line_by_id_and_convert_time(story_id, filename):
    """Reads single answer or question from file by the given ID. Returns dictionary."""
    story = get_single_line_by_key(story_id, filename, "id")
    story["submission_time"] = util.convert_unix_time_to_readable(story["submission_time"])
    return story


def get_single_line_by_key(value_to_find, filename, key):
    """Reads single answer or question from file by the given ID and cell name. Returns dictionary."""
    all_stories = read_file(filename)

    for story in all_stories:
        if story[key] == value_to_find:
            return story


def sort_dict(func):
    """decorator function, sorts data by given key and order"""
    def wrapper(*args, reverse=True, key="submission_time"):
        data = func(*args)
        array = sorted(data, key=lambda x: x[key], reverse=reverse)
        return array

    return wrapper

@sort_dict
@connection.connection_handler
def get_all_questions(cursor):
   cursor.execute("""
                    SELECT * from question""")
   data = cursor.fetchall()
   return data


@sort_dict
def get_all_questions2(filename):
    """ returns a dictionary, has sorting decorator function.
    ARGS:
        filename (string),
        reverse=False (boolean): decorator keyname parameter with default value,
        key="submission_time" (string): decorator keyname parameter with default value,
    """
    all_questions = read_file(filename)
    modded_questions = []

    for question in all_questions:
        question["submission_time"] = util.convert_unix_time_to_readable(question["submission_time"])
        question["view_number"] = int(question["view_number"])
        question["vote_number"] = int(question["vote_number"])
        modded_questions.append(question)

    return modded_questions


def get_csv_file(filename):
    return read_file(filename)


def get_answers_to_question(question_id, answers_file):
    """Reads 'answer_file' to find any answers that have the 'question_id'."""
    all_answers = read_file(answers_file)
    answers_to_question = []

    for answer in all_answers:
        if answer["question_id"] == question_id:
            answer["submission_time"] = util.convert_unix_time_to_readable(answer["submission_time"])
            answers_to_question.append(answer)

    return answers_to_question


def modify_vote_story(filename, vote_method, story_id):
    vote_to_modify = get_single_line_by_key(story_id, filename, "id")
    vote_number = int(vote_to_modify["vote_number"])

    if vote_number == 0 and vote_method != "vote_up":
        pass
    elif vote_method == "vote_up":
        vote_number += 1
    elif vote_method == "vote_down":
        vote_number -= 1

    vote_to_modify["vote_number"] = str(vote_number)

    write_changes_to_csv_file(filename, new_dataset=vote_to_modify, adding=False)


def modify_view_number(filename, story_id):
    view_to_modify = get_single_line_by_key(story_id, filename, "id")
    view_number = int(view_to_modify["view_number"])
    view_number += 1

    view_to_modify["view_number"] = str(view_number)

    write_changes_to_csv_file(filename, view_to_modify, adding=False)


def fill_out_missing_question(new_data, filename):
    """Fills out the missing question data in the new question/answer(id, date, view number, vote number)"""
    new_data['submission_time'] = util.get_unix_time()
    new_data['id'] = util.generate_id(filename)
    new_data['view_number'] = 0
    new_data['vote_number'] = 0
    return new_data


def fill_out_missing_answer(new_data, question_id, filename):
    """Fills out the missing answer data in the new question/answer(id, date, view number, vote number)"""
    new_data['submission_time'] = util.get_unix_time()
    new_data['id'] = util.generate_id(filename)
    new_data['vote_number'] = 0
    new_data['question_id'] = question_id
    return new_data


def delete_records(answer_file=None, question_file=None, id=None):
    """ delete question by its ID from question_file and the answers attached to that ID from answer_file"""
    line_to_delete = get_single_line_by_key(id, question_file, "id")
    if line_to_delete["image"] is not "":
        delete_file(line_to_delete["image"])

    delete_answers(answer_file, q_id=id)
    delete_question(question_file, id)


def delete_answer(answer_file, id):
    delete_answers(answer_file, a_id=id)


def allowed_image(filename, extensions):
    """checks if filename falls within the restrictions"""
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in extensions:
        return True
    else:
        return False


def upload_image_path(filename, question_id, image_name):
    """ appends the image_name to the 'imgage' column at the question_id" in given file
    ARGS:
        filename(string)
        question_id(string): this is the ID that the image_name appends to
        image_name(string): validation is not happening here
    """
    content = get_single_line_by_key(question_id, filename, "id")

    content["image"] = image_name
    write_changes_to_csv_file(filename, content, adding=False)

@connection.connection_handler
def write_new_question_to_database(cursor, title, message):
    dt = datetime.now()
    cursor.execute("""
                INSERT INTO question (submission_time, view_number, vote_number, title, message, image)
                VALUES (%(time)s, %(view_number)s, %(vote_number)s, %(title)s, %(message)s, %(image)s); 
                """,
                   {"time": dt,
                    "view_number": 0,
                    "vote_number": 0,
                    "title": title,
                    "message": message,
                    "image": ""
                    })


@connection.connection_handler
def write_new_answer_to_database(cursor, question_id, answer):
    dt = datetime.now()
    cursor.execute("""
                    INSERT INTO answer (id, submission_time, vote_number, question_id, message, image)
                    VALUES (%(time)s, %(vote_number)s, %(question_id)s, %(message)s, %(image)s)
                    """,
                        {
                            "time": dt,
                            "vote_number": 0,
                            "question_id": question_id,
                            "message": answer["message"],
                            "image": answer["image"]
                        })


@connection.connection_handler
def get_question_by_id(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM question
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id':question_id})

    question = cursor.fetchone()
    return question


@connection.connection_handler
def get_answers_by_question_id(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM answer
                    WHERE question_id = %(question_id)s
                    """,
                   {'question_id':question_id})

    answers = cursor.fetchall()
    return answers


@connection.connection_handler
def update_question(cursor, question_id, updated_question):
    dt = datetime.now()
    cursor.execute("""
                    UPDATE question
                    SET submission_time = %(time)s, title = %(title)s, message = %(message)s
                    WHERE id = %(question_id)s;
                    """,
                   {'time':dt,
                    'title':updated_question['title'],
                    'message':updated_question['message'],
                    'question_id':question_id})


def write_changes_to_csv_file(filename, new_dataset, adding=True):
    """Adds new or update existing question or answer to the csv file"""
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


def delete_answers(filename, q_id=None, a_id=None):
    content = read_file(filename)

    with open(filename, "w+") as f:
        writer = csv.DictWriter(f, fieldnames=ANSWER_HEADERS, delimiter=',')
        writer.writeheader()
        for answer in content:
            if q_id:
                if answer['question_id'] != q_id:
                    writer.writerow(answer)
            if a_id:
                if answer['id'] != a_id:
                    writer.writerow(answer)


def delete_file(filename):
    if os.path.exists(f"./static/images/{filename}"):
        os.remove(f"./static/images/{filename}")
    else:
        print("The file does not exist")
        pass


def get_data_header_with_convert_format(filename):
    with open(filename, 'r') as csv_file:
        data_header = csv_file.readline()
        return data_header.strip('\n').replace('_', ' ').split(',')


def read_file(filename):
    all_data = []
    with open(filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for line in csv_reader:
            all_data.append(dict(line))
        return all_data