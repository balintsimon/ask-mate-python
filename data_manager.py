import csv
import os

from psycopg2 import sql, errorcodes, errors

import connection
import psycopg2
import connection
from datetime import datetime


@connection.connection_handler
def get_all_questions(cursor, sortby, order):
    order = 'DESC' if order == 'DESC' else 'ASC'
    cursor.execute(sql.SQL("""
                    SELECT * from question
                    ORDER BY {0} {1}""").format(sql.Identifier(sortby),
                                               sql.SQL(order)))  # careful with this, no userinput allowed to go into here
    data = cursor.fetchall()
    return data


@connection.connection_handler
def get_latest_questions(cursor):
    cursor.execute("""
                    SELECT * from question
                    ORDER BY submission_time DESC
                    LIMIT 5;
                    """)
    data = cursor.fetchall()
    return data


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


@connection.connection_handler
def upload_image_to_question(cursor, question_id, image_name):
    """ appends the image_name to the 'image' column at the question_id
    ARGS:
        question_id(string): this is the ID that the image_name appends to
        image_name(string): validation is not happening here
    """
    cursor.execute("""
                    UPDATE question
                    SET image = %(image_name)s
                    WHERE id = %(question_id)s;
                    """,
                   {'image_name': image_name,
                    'question_id': question_id});


@connection.connection_handler
def write_new_question_to_database(cursor, new_question):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
                INSERT INTO question (submission_time, view_number, vote_number, title, message, image, user_name)
                VALUES (%(time)s, %(view_number)s, %(vote_number)s, %(title)s, %(message)s, %(image)s, %(user_name)s); 
                """,
                   {"time": dt,
                    "view_number": 0,
                    "vote_number": 0,
                    "title": new_question['title'],
                    "message": new_question['message'],
                    "image": new_question["image"],
                    "user_name": new_question["user_name"]
                    })


@connection.connection_handler
def write_new_answer_to_database(cursor, question_id, answer):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_answer = answer["message"]
    new_image = answer["image"]
    user_name = answer["user_name"]
    cursor.execute("""
                    INSERT INTO answer (submission_time, vote_number, question_id, message, image, user_name)
                    VALUES (%(time)s, %(vote_number)s, %(question_id)s, %(message)s, %(image)s, %(user_name)s)
                    """,
                   {
                       "time": dt,
                       "vote_number": 0,
                       "question_id": question_id,
                       "message": new_answer,
                       "image": new_image,
                       "user_name": user_name
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
                    INSERT INTO comment (question_id, answer_id, message, submission_time, edited_count, user_name)
                    VALUES (%(question_id)s, %(answer_id)s, %(message)s, %(time)s, %(edit)s, %(user_name)s);
                    """,
                   {"question_id": data["question_id"],
                    "answer_id": data["answer_id"],
                    "message": data["message"],
                    "time": dt,
                    "edit": 0,
                    "user_name": data["user_name"]})


@connection.connection_handler
def edit_comment(cursor, comment_id, message):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
                    UPDATE comment
                    SET message = %(message)s, edited_count = edited_count + 1, submission_time = %(submission_time)s
                    WHERE id = %(comment_id)s;
                    """,
                   {'comment_id': comment_id,
                    'submission_time': dt,
                    'message': message})


@connection.connection_handler
def delete_comment(cursor, comment_id):
    cursor.execute("""
                    DELETE from comment
                    WHERE id = %(comment_id)s;
                    """,
                   {'comment_id': comment_id})


@connection.connection_handler
def get_question_by_id(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM question
                    WHERE id = %(question_id)s;
                    """,
                   {'question_id': question_id})

    question = cursor.fetchone()
    return question


@connection.connection_handler
def get_answers_by_question_id(cursor, question_id):
    cursor.execute("""
                    SELECT * FROM answer
                    WHERE question_id = %(question_id)s
                    ORDER BY vote_number DESC, submission_time ASC;
                    """,
                   {'question_id': question_id})

    answers = cursor.fetchall()
    return answers


@connection.connection_handler
def update_question(cursor, question_id, updated_question):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
                    UPDATE question
                    SET submission_time = %(time)s, title = %(title)s, message = %(message)s, image = %(new_image)s
                    WHERE id = %(question_id)s;
                    """,
                   {'time': dt,
                    'title': updated_question['title'],
                    'message': updated_question['message'],
                    'new_image': updated_question['image'],
                    'question_id': question_id});


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
def search_question(cursor, search_phrase):
    cursor.execute("""
                    SELECT * FROM question
                    WHERE LOWER(title) LIKE %(search_phrase)s OR LOWER(message) LIKE %(search_phrase)s
                    """,
                   {'search_phrase': '%' + search_phrase + '%'})

    question_result = cursor.fetchall()

    cursor.execute("""
                    SELECT * FROM answer
                    WHERE LOWER(message) LIKE %(search_phrase)s
                    """,
                   {'search_phrase': '%' + search_phrase + '%'})
    answer_result = cursor.fetchall()

    for result in answer_result:
        result["title"] = "Answer to question"
        result["id"] = result["question_id"]

    search_result = question_result + answer_result
    if not search_result:
        return None
    return search_result


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
def get_comment_by_comment_id(cursor, comment_id):
    cursor.execute("""
                    SELECT * FROM comment
                    WHERE id = %(comment_id)s
                    """,
                   {'comment_id': comment_id})
    data = cursor.fetchone()
    return data


@connection.connection_handler
def update_answer(cursor, answer_id, update_answer):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = update_answer['message']
    cursor.execute("""
                    UPDATE answer
                    SET submission_time = %(time)s, message = %(message)s, image=%(new_image)s
                    WHERE id = %(answer_id)s;
                    """,
                   {'time': dt,
                    'message': message,
                    'new_image': update_answer['image'],
                    'answer_id': answer_id})

@connection.connection_handler
def find_comments(cursor, question_id):
    cursor.execute("""
                     SELECT * FROM comment
                     WHERE question_id = %(question_id)s
                     ORDER BY id;""",
                    {'question_id': question_id})

    comments = cursor.fetchall()
    return comments


@connection.connection_handler
def create_user(cursor, username, password):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
        INSERT INTO users
        VALUES (DEFAULT , %(username)s, %(password)s, %(registration_time)s, DEFAULT);
        """, {'username': username,
              'password': password,
              'registration_time': dt})
    except psycopg2.errors.UniqueViolation:
        return False
    return True


@connection.connection_handler
def get_user_password(cursor, username):
    cursor.execute("""
                    SELECT password FROM users
                    WHERE name = %(username)s;
                    """, {'username': username})
    password = cursor.fetchone()
    return password

@connection.connection_handler
def get_user(cursor, username):
    cursor.execute("""
    SELECT name, password FROM users
    WHERE name = %(username)s
    """,
    {'username': username})

    user = cursor.fetchone()
    return user
