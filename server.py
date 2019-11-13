from flask import Flask, render_template, redirect, request, url_for
import data_manager
import connection
import util

app = Flask(__name__)

QUESTIONS_FILE_PATH = "./sample_data/question.csv"
ANSWERS_FILE_PATH = "./sample_data/answer.csv"
QUESTION_HEADERS = connection.get_data_header(QUESTIONS_FILE_PATH)
ANSWERS_HEADERS = connection.get_data_header(ANSWERS_FILE_PATH)


@app.route('/')
def show_questions():
    try:
        label_to_sortby = request.args.getlist('sorting')[0]
    except IndexError:
        label_to_sortby = "submission_time"
    data = data_manager.get_all_questions(QUESTIONS_FILE_PATH, key=label_to_sortby, reverse=True)
    header = connection.get_data_header(QUESTIONS_FILE_PATH)
    labels = ["submission_time", "view_number", "vote_number", "title", "message"]
    return render_template("list.html", all_questions=data, question_header=header, file_labels=labels)


@app.route('/add-questions', methods=['GET', 'POST'])
def add_new_question():
    if request.method == 'POST':
        new_question = dict(request.form)
        final_question = data_manager.fill_out_missing_data(new_question, QUESTIONS_FILE_PATH)
        connection.add_new_data(QUESTIONS_FILE_PATH, final_question, data_manager.QUESTION_HEADERS)
        return redirect('/')
    return render_template('form.html',
                           url_action="",
                           action_method="post",
                           page_title=f'Add new question',
                           header_title='Add new question',
                           title_field_title='Your title:',
                           body_edit_title='Your message:',
                           question={'title': "", 'message': "", 'image': ""},
                           button_title="Post")


@app.route('/question/<question_id>/new-answer', methods=['GET', 'POST'])
def add_new_answer(question_id):
    return redirect('/')


@app.route('/questions/<question_id>', methods=['GET', 'POST'])
def manage_questions(question_id):
    actual_question = data_manager.get_single_line_by_id(question_id, QUESTIONS_FILE_PATH)
    answers_to_question = data_manager.get_answers_to_question(question_id, ANSWERS_FILE_PATH)

    if request.method == "GET":
        return render_template("question.html",
                               url_action=url_for("edit_question", question_id=question_id),
                               page_title=f"Answers to question ID {question_id}",
                               question=actual_question,
                               answers=answers_to_question,
                               question_headers=QUESTION_HEADERS,
                               answer_headers=ANSWERS_HEADERS)
    pass


@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    question = data_manager.get_single_line_by_id(question_id, QUESTIONS_FILE_PATH)
    if request.method == "POST":
        edited_question = {"id": question["id"],
                           "submission_time": util.get_unix_time(),
                           "view_number": question["view_number"],
                           "vote_number": question["vote_number"],
                           "title": request.form.get("title"),
                           "message": request.form.get("message"),
                           "image": request.form.get("image", question["image"]),
                           }

        connection.update_file(QUESTIONS_FILE_PATH, edited_question, adding=False)
        return redirect("/")

    return render_template("form.html",
                           url_action=url_for("edit_question", question_id=question_id),
                           action_method="get",
                           page_title=f"Edit question ID {question_id}",
                           header_title=f"Edit question ID {question_id}",
                           question=question,
                           title_field_title="Edit title:",
                           body_title="Edit question:",
                           image_title="Edit image:",
                           button_title="Save change")


@app.route('/answer/<answer_id>', methods=('GET', 'POST'))
def manage_answer(answer_id):
    if request.method == "POST":
        pass
    pass


@app.route('/question/<question_id>/<vote_method>', methods=['GET', 'POST'])
def vote_questions(vote_method, question_id):
    filename = QUESTIONS_FILE_PATH

    # question = data_manager.get_single_line_by_id(question_id, filename)
    modified_story = data_manager.modify_vote_story(filename, vote_method, story_id=question_id)
    connection.update_file(filename, new_dataset=modified_story, adding=False)

    return redirect(url_for("show_questions"))




if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
