from flask import Flask, render_template, redirect, request
import connection
import data_manager


app = Flask(__name__)

QUESTIONS_FILE_PATH = "/sample_data/question.csv"
ANSWERS_FILE_PATH = "/sample_data/answer.csv"
QUESTION_HEADERS = connection.get_data_header(QUESTIONS_FILE_PATH)
ANSWERS_HEADERS = connection.get_data_header(ANSWERS_FILE_PATH)

@app.route('/')
def show_questions():
    return render_template("index.html")


@app.route('/questions/<question_id>', methods=['GET', 'POST'])
def manage_questions(question_id):
    actual_question = data_manager.get_single_line_by_id(question_id, QUESTIONS_FILE_PATH)
    answers_to_question = data_manager.get_answers_to_question(question_id, ANSWERS_FILE_PATH)

    if request.method == "GET":
        return render_template("question.html",
                               question=actual_question,
                               answers=answers_to_question,
                               QUESTION_HEADERS=QUESTION_HEADERS,
                               ANSWERS_HEADERS=ANSWERS_HEADERS)
    pass


@app.route('/answer/<answer_id>', methods=('GET', 'POST'))
def manage_answer(answer_id):
    if request.method == "POST":
        pass
    pass


if __name__ == '__main__':
    app.run(
        port=5000,
        debug=True,
    )