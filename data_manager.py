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
def modify_view_number(cursor, question_id, modify_view=False):
    if modify_view:
        cursor.execute("""
                        UPDATE question
                        SET view_number = view_number + 1
                        WHERE id = %(question_id)s
                        """, {'question_id': question_id});
@connection.connection_handler
def modify_view_number(cursor, question_id):
    cursor.execute("""
                    UPDATE question
                    SET view_number = view_number + 1
                    WHERE id = %(question_id)s
                    """, {'question_id': question_id});


@connection.connection_handler
def delete_answer(cursor, answer_id):
    cursor.execute("""
                    DELETE FROM comment
                    WHERE answer_id = %(answer_id)s""",
                   {'answer_id': answer_id});

    cursor.execute("""
                    DELETE FROM answer
                    WHERE id = %(answer_id)s""",
                    {'answer_id': answer_id});


@connection.connection_handler
def delete_question(cursor, question_id):
    cursor.execute("""
                    DELETE FROM comment
                    WHERE question_id = %(question_id)s
                    """,
                   {'question_id': question_id}
                   );

    cursor.execute("""
                        DELETE FROM answer
                        WHERE question_id = %(question_id)s
                        """,
                   {'question_id': question_id}
                   );

    cursor.execute("""
                        DELETE FROM question
                        WHERE id = %(question_id)s
                        """,
                   {'question_id': question_id}
                   );



def allowed_image(filename, extensions):
    """checks if filename falls within the restrictions"""
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in extensions:
        return True
    else:
        return False

'''
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
'''

@connection.connection_handler
def write_new_question_to_database(cursor, title, message):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
def write_new_comment_to_database(cursor, data):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if data["answer_id"]:
            pass
    except KeyError:
        data.update({"answer_id": None})

    cursor.execute("""
                    INSERT INTO comment (question_id, answer_id, message, submission_time, edited_count)
                    VALUES (%(question_id)s, %(answer_id)s, %(message)s, %(time)s, %(edit)s);
                    """,
                   {"question_id": data["question_id"],
                    "answer_id": data["answer_id"],
                    "message": data["message"],
                    "time": dt,
                    "edit": 0})


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
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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




'''
def write_changes_to_csv_file(filename, new_dataset, adding=True):
    """Adds new or update existing question or answer to the csv file"""
    existing_submits = read_file(filename)
    open_option = "a" if adding is True elsanswer_ide "w"

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
'''

def read_file(filename):
    all_data = []
    with open(filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for line in csv_reader:
            all_data.append(dict(line))
        return all_data


@connection.connection_handler
def get_answer_by_answer_id(cursor, answer_id):
    cursor.execute("""
                     SELECT * from answer
                     WHERE id = %(answer_id)s""",
                   {'answer_id': answer_id}
                   )
    data = cursor.fetchone()
    return data


@connection.connection_handler
def update_answer(cursor, answer_id, update_answer):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = update_answer['message']
    cursor.execute("""
                    UPDATE answer
                    SET submission_time = %(time)s, message = %(message)s
                    WHERE id = %(answer_id)s;
                    """,
                   {'time': dt,
                    'message': message,
                    'answer_id': answer_id});