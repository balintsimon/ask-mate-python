import connection
from datetime import datetime

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]

question_file = "./sample_data/question.csv"
answer_file = "./sample_data/answer.csv"


def get_single_line_by_id(story_id, filename):
    all_stories = connection.read_file(filename)

    for story in all_stories:
        if int(story["id"]) == story_id:
            story["submission_time"] = datetime.fromtimestamp(int(story["submission_time"]))
            return story


def get_csv_file(filename):
    return connection.read_file(filename)


def get_answers_to_question(question_id, answers_file):
    all_answers = connection.read_file(answers_file)
    answers_to_question = []

    for answer in all_answers:
        if answer["question_id"] == question_id:
            answer["submission_time"] = datetime.fromtimestamp(int(answer["submission_time"]))
            answers_to_question.append(answer)

    return answers_to_question


def vote(story_id, filename, vote_method):
    story = get_single_line_by_id(story_id,filename)
    vote_number = int(story["vote_number"])
    if vote_method == "up":
        vote_number += 1
    elif vote_number == "down":
        vote_number -= 1

    pass

