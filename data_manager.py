import connection

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]

def get_single_line_by_id(story_id, filename):
    all_stories = connection.read_file(filename)

    for story in all_stories:
        if story["id"] == story_id:
            return story


def get_csv_file(filename):
    return connection.read_file(filename)


def get_answers_to_question(question_id, answers_file):
    all_answers = connection.read_file(answers_file)
    answers_to_question = []

    for answer in all_answers:
        if answer["question_id"] == question_id:
            answers_to_question.append(answer)

    return answers_to_question
