import connection
import util

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]


def get_single_line_by_id_and_convert_time(story_id, filename):
    """Reads single answer or question from file by the given ID. Returns dictionary."""
    story = get_single_line_by_key(story_id, filename, "id")
    story["submission_time"] = util.convert_unix_time_to_readable(story["submission_time"])
    story['answers'] = get_answers_to_question(question_id, ANSWERS_FILE_PATH)

    return story


def get_single_line_by_key(value_to_find, filename, key):
    """Reads single answer or question from file by the given ID and cell name. Returns dictionary."""
    all_stories = connection.read_file(filename)

    for story in all_stories:
        if story[key] == value_to_find:
            return story


"""decorator function, sorts data by given key and order"""


def sort_dict(func):
    def wrapper(*args, reverse=True, key="submission_time"):
        data = func(*args)
        array = sorted(data, key=lambda x: x[key], reverse=reverse)
        return array

    return wrapper


@sort_dict
def get_all_questions(filename):
    """ returns a dictionary, has sorting decorator function.
    ARGS:
        filename (string),
        reverse=False (boolean): decorator keyname parameter with default value,
        key="submission_time" (string): decorator keyname paramtere with default value,
    """
    all_questions = connection.read_file(filename)
    modded_questions = []

    for question in all_questions:
        question["submission_time"] = util.convert_unix_time_to_readable(question["submission_time"])
        question["view_number"] = int(question["view_number"])
        question["vote_number"] = int(question["vote_number"])
        modded_questions.append(question)

    return modded_questions


def get_csv_file(filename):
    return connection.read_file(filename)


def get_answers_to_question(question_id, answers_file):
    """Reads 'answer_file' to find any answers that have the 'question_id'."""
    all_answers = connection.read_file(answers_file)
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

    connection.write_changes_to_csv_file(filename, new_dataset=vote_to_modify, adding=False)


def modify_view_number(filename, story_id):
    view_to_modify = get_single_line_by_key(story_id, filename, "id")
    view_number = int(view_to_modify["view_number"])
    view_number += 1

    view_to_modify["view_number"] = str(view_number)

    connection.write_changes_to_csv_file(filename, view_to_modify, adding=False)


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
    line_to_delete = get_single_line_by_key(id, question_file, "id")
    if line_to_delete["image"] is not "":
        connection.delete_file(line_to_delete["image"])
    connection.delete_answers(answer_file, q_id=id)
    connection.delete_question(question_file, id)


def delete_answer(answer_file, id):
    connection.delete_answers(answer_file, a_id=id)



def upload_image_path(filename, question_id, image_name):
    content = get_single_line_by_key(question_id, filename, "id")

    content["image"] = image_name
    connection.write_changes_to_csv_file(filename, content, adding=False)
