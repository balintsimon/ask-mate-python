from flask import Flask, render_template, redirect, request, url_for
from werkzeug.utils import secure_filename
import os
import data_manager
import connection
import util

app = Flask(__name__)

app.config["IMAGE_UPLOADS"] = "./static/images/"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024

QUESTIONS_FILE_PATH = "./sample_data/question.csv"
ANSWERS_FILE_PATH = "./sample_data/answer.csv"
QUESTION_HEADERS = connection.get_data_header_with_convert_format(QUESTIONS_FILE_PATH)
ANSWERS_HEADERS = connection.get_data_header_with_convert_format(ANSWERS_FILE_PATH)


@app.route('/')
def show_questions():
    LABEL = 0
    ORDER = 1
    try:
        label_to_sortby = request.args.getlist('sorting')[LABEL]
    except:
        label_to_sortby = "submission_time"
    try:
        order = request.args.getlist('sorting')[ORDER]
        order = bool(order == "True")
    except:
        order = True

    data = data_manager.get_all_questions(reverse=order, key=label_to_sortby)
    # = data_manager.get_all_questions(QUESTIONS_FILE_PATH, reverse=order, key=label_to_sortby)
    header = connection.get_data_header_with_convert_format(QUESTIONS_FILE_PATH)
    labels = ["submission_time", "view_number", "vote_number", "title", "message"]
    return render_template("list.html",
                           all_questions=data,
                           question_header=header,
                           file_labels=labels,
                           order={True: "Descending", False: "Ascending"},
                           userpick_label=label_to_sortby,
                           userpick_order=order,
                           )


@app.route('/add-questions', methods=['GET', 'POST'])
def add_new_question():
    if request.method == 'POST':
        new_question = dict(request.form)
        final_question = data_manager.fill_out_missing_question(new_question, QUESTIONS_FILE_PATH)
        connection.write_changes_to_csv_file(QUESTIONS_FILE_PATH, final_question, adding=True)
        return redirect('/')
    return render_template('add_question_or_answer.html', question=True)


@app.route('/question/<question_id>/new-answerD', methods=['GET', 'POST']) #### del the D from the end
def add_new_answer(question_id):
    if request.method == 'POST':
        new_answer = dict(request.form)
        final_answer = data_manager.fill_out_missing_answer(new_answer, question_id, ANSWERS_FILE_PATH)
        connection.write_changes_to_csv_file(ANSWERS_FILE_PATH, final_answer, adding=True)
        return redirect(f'/questions/{question_id}')

    return render_template('add_question_or_answer.html')


@app.route('/questions/<question_id>')
def manage_questions(question_id):
    if request.args.getlist('addinganswer'):
        addinganswer = True
    else:
        addinganswer = False
    data_manager.modify_view_number(QUESTIONS_FILE_PATH, question_id)

    actual_question = data_manager.get_single_line_by_id_and_convert_time(question_id, QUESTIONS_FILE_PATH)
    answers_to_question = data_manager.get_answers_to_question(question_id, ANSWERS_FILE_PATH)

    return render_template("question-child.html",
                           url_action=url_for("edit_question", question_id=question_id),
                           page_title=f"Answers to question: \"{ actual_question['title'] }\"",
                           question=actual_question,
                           answers=answers_to_question,
                           addinganswer=addinganswer,
                           question_headers=QUESTION_HEADERS,
                           answer_headers=ANSWERS_HEADERS)



@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    question = data_manager.get_single_line_by_id_and_convert_time(question_id, QUESTIONS_FILE_PATH)
    if request.method == "POST":
        edited_question = {"id": question["id"],
                           "submission_time": util.get_unix_time(),
                           "view_number": question["view_number"],
                           "vote_number": question["vote_number"],
                           "title": request.form.get("title"),
                           "message": request.form.get("message"),
                           "image": request.form.get("image", question["image"]),
                           }

        print(edited_question)
        connection.write_changes_to_csv_file(QUESTIONS_FILE_PATH, edited_question, adding=False)
        return redirect("/")

    return render_template("form.html",
                           question_id=question_id,
                           url_action=url_for("edit_question", question_id=question_id),
                           action_method="post",
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


@app.route('/question/<question_id>/<vote_method>')
def vote_questions(vote_method, question_id):
    data_manager.modify_vote_story(QUESTIONS_FILE_PATH, vote_method, question_id)
    return redirect('/')


@app.route('/answer/<question_id>/<answer_id>/<vote_method>')
def vote_answers(vote_method, answer_id, question_id):
    data_manager.modify_vote_story(ANSWERS_FILE_PATH, vote_method, answer_id)
    return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/answer/<question_id>/<answer_id>/delete')
def delete_answer(question_id, answer_id):
    data_manager.delete_answer(ANSWERS_FILE_PATH, answer_id)
    return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/question/<question_id>/delete')
def delete_question(question_id):
    data_manager.delete_records(answer_file=ANSWERS_FILE_PATH, question_file=QUESTIONS_FILE_PATH, id=question_id)
    return redirect('/')


@app.route('/upload-image', methods=['GET', 'POST'])
def upload_image():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]

            if image.filename == "":
                return redirect(request.referrer)

            if data_manager.allowed_image(image.filename, app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                question_id = request.form.get("question_id")
                data_manager.upload_image_path(QUESTIONS_FILE_PATH, question_id, filename)
                print("Image saved")
                return redirect(request.referrer)

            else:
                print("not allowed image")
                return redirect(request.referrer)


@app.route('/question/<question_id>/new-answer', methods=['GET', 'POST'])
def add_newstuff_withimage(question_id):
    if request.method == "POST":
        if request.files:
            image = request.files["image"]

            if image.filename != "":

                #return redirect(request.referrer) # error

                if data_manager.allowed_image(image.filename, app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))

                    print("Image saved")

                else:
                    print("not allowed image")
                    return redirect(request.referrer)

        new_answer = dict(request.form)
        if image.filename:
            new_answer.update({"image": filename}) # ugly solution, a band-aid

        final_answer = data_manager.fill_out_missing_answer(new_answer, question_id, ANSWERS_FILE_PATH)
        connection.write_changes_to_csv_file(ANSWERS_FILE_PATH, final_answer, adding=True)
        return redirect(url_for("manage_questions", question_id=question_id))

        # return redirect(f'/questions/{question_id}')



if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
