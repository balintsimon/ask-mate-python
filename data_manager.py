import csv
import os

from psycopg2 import sql, errorcodes, errors

import connection
import psycopg2
import connection
from datetime import datetime


@connection.connection_handler
def get_author_by_question_id(cursor, question_id):
    cursor.execute("""
        SELECT user_name FROM question
        WHERE id = %(q_id)s
    """,
                   {"q_id": question_id})
    return cursor.fetchone()


@connection.connection_handler
def get_author_by_answer_id(cursor, answer_id):
    cursor.execute("""
        SELECT user_name FROM answer
        WHERE id = %(answer_id)s;
    """,
                   {"answer_id": answer_id})

    return cursor.fetchone()


def calculate_reputation(type, direction, original):
    repchart_up = {"question": 5, "answer": 10, "accepted": 15}
    repchart_down = {"question": -2, "answer": -2, "accepted": 0}
    if direction == "vote_up":
        rep = repchart_up
    else:
        rep = repchart_down
    original = original['reputation'] + int(rep[type])
    return original


def annul_calc_reputation(type, direction, original):
    repchart_up = {"question": -5, "answer": -10, "accepted": -15}
    repchart_down = {"question": 2, "answer": 2, "accepted": 0}
    if direction == "vote_up":
        rep = repchart_down
    else:
        rep = repchart_up
    original = original['reputation'] + rep[type]
    return original

@connection.connection_handler
def get_reputation(cursor, username):
    cursor.execute("""
        SELECT reputation FROM users
        WHERE name = %(user)s;
        """,
        {"user": username})
    return cursor.fetchone()


@connection.connection_handler
def update_user_reputation(cursor, username, value):
    cursor.execute("""
        UPDATE users
        SET reputation = %(reputation)s
        WHERE name = %(user)s
        """,
        {"user": username, "reputation": value})


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
        UPDATE question
        SET accepted_answer = NULL
        WHERE accepted_answer = %(answer_id)s""",
       {"answer_id": answer_id});

    cursor.execute("""
        DELETE FROM votes
        WHERE answer_id = %(answer_id)s""",
        {'answer_id': answer_id})

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
                    UPDATE question
                    SET accepted_answer = NULL
                    WHERE id = %(question_id)s""",
                   {"question_id": question_id});

    cursor.execute("""
                    DELETE FROM votes
                    WHERE question_id = %(question_id)s
                    """,
                   {'question_id': question_id})

    answers = get_answers_by_question_id(question_id)
    print(answers)
    for answer in answers:
        delete_answer(answer['id'])

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
                    SELECT question.id,
                     question.submission_time,
                     question.view_number,
                     question.vote_number,
                     question.title,
                     question.message,
                     question.image,
                     question.user_name,
                     question.accepted_answer,
                     users.id as user_id
                     FROM question
                    LEFT JOIN users ON question.user_name = users.name
                    WHERE question.id = %(question_id)s;
                    """,
                   {'question_id': question_id})

    question = cursor.fetchone()
    return question


@connection.connection_handler
def get_answers_by_question_id(cursor, question_id):
    cursor.execute("""
                    SELECT 
                        CASE
                        WHEN question.accepted_answer = answer.id THEN 1 ELSE 0 
                        END as accepted,
                    answer.id,
                    answer.user_name,
                    users.reputation,
                    answer.submission_time, 
                    answer.vote_number, 
                    answer.message, 
                    answer.question_id, 
                    answer.image,
                        CASE
                        when votes.vote_method = -1 THEN -1 
                        when votes.vote_method = 1 then 1 ELSE 0
                        END as vote_method
                    FROM answer
                    LEFT JOIN question ON answer.question_id = question.id
                    LEFT JOIN users ON answer.user_name = users.name
                    LEFT JOIN votes ON answer.id = votes.answer_id
                    WHERE answer.question_id = %(question_id)s
                    ORDER BY accepted DESC, vote_number DESC, submission_time ASC;
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
def check_if_user_voted_on_question(cursor, user, question):
    cursor.execute("""
                SELECT * FROM votes
                WHERE user_name = %(user)s AND question_id = %(question)s;
                """,
                   {
                       "user": user,
                       "question": question
                   })

    result = cursor.fetchone()
    return result


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
                        WHERE id = %(question_id)s
                        """, {'question_id': question_id});


@connection.connection_handler
def create_vote_on_question_in_votes_db(cursor, question_id, user):
    vote = -1 if user["vote_method"] == "vote_down" else 1

    cursor.execute("""
                    INSERT INTO votes (user_id, user_name, question_id, vote_method)
                    VALUES (%(user_id)s, %(user_name)s, %(question_id)s, %(vote_method)s);
                    """,{
                       "question_id": question_id,
                       "user_id": user['id'],
                       "user_name": user['user_name'],
                       "vote_method": vote
                   })

@connection.connection_handler
def delete_vote_on_question_from_votes_db(cursor, vote_data, vote_method):
    vote_value = -1 if vote_method == "vote_down" else 1
    result_vote = vote_data['vote_method'] + vote_value

    if result_vote == 0:
        cursor.execute("""
            DELETE FROM votes
            WHERE question_id = %(question_id)s
        """, {'question_id': vote_data['question_id']})

        return True
    else:
        return False


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
def check_if_user_voted_on_answer(cursor, user, answer):
    cursor.execute("""
                SELECT * FROM votes
                WHERE user_name = %(user)s AND answer_id = %(answer)s;
                """,
                   {
                   "user": user,
                   "answer": answer
                   })

    result = cursor.fetchone()
    return result


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
                        WHERE id = %(answer_id)s
                        """, {'answer_id': answer_id});


@connection.connection_handler
def create_vote_on_answer_in_votes_db(cursor, answer_id, user):
    vote = -1 if user["vote_method"] == "vote_down" else 1

    cursor.execute("""
                    INSERT INTO votes (user_id, user_name, answer_id, vote_method)
                    VALUES (%(user_id)s, %(user_name)s, %(answer_id)s, %(vote_method)s);
                    """,{
                       "answer_id": answer_id,
                       "user_id": user['id'],
                       "user_name": user['user_name'],
                       "vote_method": vote
                   })


@connection.connection_handler
def delete_vote_on_answer_from_votes_db(cursor, vote_data, vote_method):
    vote_value = -1 if vote_method == "vote_down" else 1
    result_vote = vote_data['vote_method'] + vote_value

    if result_vote == 0:
        cursor.execute("""
            DELETE FROM votes
            WHERE answer_id = %(answer_id)s
        """, {'answer_id': vote_data['answer_id']})
        # van-e itt egyáltalán answer_id???
        return True
    else:
        return False


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
                     SELECT comment.id,
                        comment.question_id,
                        comment.answer_id,
                        comment.message,
                        comment.submission_time,
                        comment.edited_count,
                        comment.user_name,
                        users.reputation FROM comment
                     LEFT JOIN users ON comment.user_name = users.name
                     WHERE comment.question_id = %(question_id)s
                     ORDER BY comment.id;""",
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
def sort_questions(cursor, order_by, order_direction):
    cursor.execute(sql.SQL("""
                    SELECT * FROM question
                    ORDER BY {0} {1};""").format(sql.Identifier(order_by), sql.SQL(order_direction)))

    data = cursor.fetchall()
    return data


@connection.connection_handler
def get_user(cursor, username):
    cursor.execute("""
    SELECT name, password FROM users
    WHERE name = %(username)s
    """,
    {'username': username})

    user = cursor.fetchone()
    return user


@connection.connection_handler
def get_user_list(cursor):
    cursor.execute("""
SELECT u.id, u.reputation, u.name, date(u.registration_date) as member_since,
       count(DISTINCT q.id) as question,
count(DISTINCT a.id) as answer,
count(DISTINCT c.id) as comment
from users as u
left outer join question q on u.name = q.user_name
left outer join answer a on u.name = a.user_name
left outer join comment c on u.name = c.user_name
GROUP BY u.id""")

    all_user_attribute = cursor.fetchall()
    return all_user_attribute



@connection.connection_handler
def get_user_id(cursor, username):
    cursor.execute("""
    SELECT id from users
    WHERE name = %(username)s;
    """,
                   {'username': username})

    user = cursor.fetchone()

    return user['id']



@connection.connection_handler
def get_user_name(cursor, user_id):
    cursor.execute("""
    SELECT name from users
    WHERE id = %(user_id)s;
    """,
                   {'user_id': user_id})

    user_name = cursor.fetchone()
    return user_name


@connection.connection_handler
def get_user_attributes(cursor, user_id):
    cursor.execute("""
    SELECT q.*
    from question q
    left outer join users u on u.name = q.user_name
    left outer join answer a on u.name = a.user_name
    left outer join comment c on u.name = c.user_name
    WHERE u.id = %(user_id)s
    GROUP BY u.id, a.id, q.id, c.id;
    """,
                   {'user_id': user_id})
    user_attributes = cursor.fetchall()
    return user_attributes


@connection.connection_handler
def get_user_questions(cursor, user_id):
    cursor.execute("""
    SELECT q.*
    from question as q
    join users u on u.name = q.user_name
    WHERE u.id = %(user_id)s;
    """,
                   {'user_id': user_id})
    user_questions = cursor.fetchall()
    return user_questions


@connection.connection_handler
def get_user_answers(cursor, user_id):
    cursor.execute("""
    SELECT q.*
    from question as q
    left outer join answer a on a.question_id = q.id   
    join users u on a.user_name = u.name
    WHERE u.id = %(user_id)s;
    """,
                   {'user_id': user_id})
    user_answers = cursor.fetchall()
    return user_answers


@connection.connection_handler
def get_user_comments(cursor, user_id):
    cursor.execute("""
    SELECT q.*
    from question as q

    left outer join comment c on c.question_id = q.id
    left outer join answer a on c.answer_id = a.id
    join users u on a.user_name = u.name OR q.user_name = u.name
    WHERE u.id = %(user_id)s;
    """,
                   {'user_id': user_id})
    user_comments = cursor.fetchall()
    return user_comments


@connection.connection_handler
def get_user_id_by_name(cursor, username):
    cursor.execute("""
    SELECT id FROM users
    WHERE name = %(username)s
    """,
                   {"username": username})

    user_id = cursor.fetchone()
    return user_id


@connection.connection_handler
def set_new_accepted_answer(cursor, question_id, accepted_answer_id):
    author_id = get_accepted_author_id(question_id)
    if get_author_by_answer_id(author_id) is not None:
        author = get_author_by_answer_id(author_id)["user_name"]
        author_repu = get_reputation(author)
        new_repu = annul_calc_reputation("accepted", "vote_down", author_repu)
        update_user_reputation(author, new_repu)

    cursor.execute("""
        UPDATE question
        SET accepted_answer = %(answer)s
        WHERE id = %(qid)s;
        """,
       {"answer":accepted_answer_id, "qid": question_id}
       )

    author_id = get_accepted_author_id(question_id)
    author = get_author_by_answer_id(author_id)["user_name"]
    author_repu = get_reputation(author)
    new_repu = calculate_reputation("accepted", "vote_up", author_repu)
    update_user_reputation(author, new_repu)


@connection.connection_handler
def get_accepted_author_id(cursor, question_id):
    cursor.execute("""
        SELECT accepted_answer
        FROM question
        WHERE id = %(qid)s""",
                   {'qid': question_id})
    author_id = cursor.fetchone()

    return author_id['accepted_answer']
