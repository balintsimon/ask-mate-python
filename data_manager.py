import csv
import os
import connection
import psycopg2
import connection
import util
from datetime import datetime

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]


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


@connection.connection_handler
def modify_view_number(cursor, question_id):
    cursor.execute("""
                    UPDATE question
                    SET view_number = view_number + 1
                    WHERE id = %(question_id)s
                    """, {'question_id': question_id});


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
    new_answer = answer["message"]
    new_image = answer["image"]
    cursor.execute("""
                    INSERT INTO answer (submission_time, vote_number, question_id, message, image)
                    VALUES (%(time)s, %(vote_number)s, %(question_id)s, %(message)s, %(image)s)
                    """,
                        {
                            "time": dt,
                            "vote_number": 0,
                            "question_id": question_id,
                            "message": new_answer,
                            "image": new_image
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
                    'question_id':question_id});

@connection.connection_handler
def vote_question(cursor, direction, question_id):
    if direction == "vote_up":
        cursor.execute("""
                        UPDATE question
                        SET vote_number = vote_number + 1
                        WHERE id = %(question_id)s
                        """, {'question_id': question_id});
    else:
        cursor.execute("""
                        UPDATE question
                        SET vote_number = vote_number - 1
                        WHERE id = %(question_id)s and vote_number > 0
                        """, {'question_id': question_id});


@connection.connection_handler
def vote_answer(cursor, direction, answer_id):
    if direction == "vote_up":
        cursor.execute("""
                        UPDATE answer
                        SET vote_number = vote_number + 1
                        WHERE id = %(answer_id)s
                        """, {'answer_id': answer_id});
    else:
        cursor.execute("""
                        UPDATE answer
                        SET vote_number = vote_number - 1
                        WHERE id = %(answer_id)s AND vote_number > 0
                        """, {'answer_id': answer_id});



        

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