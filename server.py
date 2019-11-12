from flask import Flask, render_template, redirect, request, url_for
import data_manager
import connection


app = Flask(__name__)

QUESTIONS_FILE_PATH = "./sample_data/question.csv"
ANSWERS_FILE_PATH = "./sample_data/answer.csv"
QUESTION_HEADERS = connection.get_data_header(QUESTIONS_FILE_PATH)
ANSWERS_HEADERS = connection.get_data_header(ANSWERS_FILE_PATH)


@app.route('/')
def show_questions():
    data = data_manager.get_all_questions(QUESTIONS_FILE_PATH)
    header = connection.get_data_header(QUESTIONS_FILE_PATH)
    return render_template("list.html", all_questions=data, question_header=header)


@app.route('/add-questions', methods=['GET', 'POST'])
def add_new_question():
    if request.method == 'POST':
        new_question = dict(request.form)
        final_question = data_manager.fill_out_missing_data(new_question, QUESTIONS_FILE_PATH)
        connection.add_new_data(QUESTIONS_FILE_PATH, final_question, data_manager.QUESTION_HEADERS)
        return redirect('/')
    return render_template('add_question_or_answer.html')


@app.route('/questions/<question_id>', methods=['GET', 'POST'])
def manage_questions(question_id):
    actual_question = data_manager.get_single_line_by_id(question_id, QUESTIONS_FILE_PATH)
    answers_to_question = data_manager.get_answers_to_question(question_id, ANSWERS_FILE_PATH)

    if request.method == "GET":
        return render_template("question.html",
                               page_title=f"Answers to question ID {question_id}",
                               question=actual_question,
                               answers=answers_to_question,
                               question_headers=QUESTION_HEADERS,
                               answer_headers=ANSWERS_HEADERS)
    pass

@app.route('/question/<question_id>/edit')
def edit_question(question_id):
    pass

@app.route('/answer/<answer_id>', methods=('GET', 'POST'))
def manage_answer(answer_id):
    if request.method == "POST":
        pass
    pass


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )