from flask import Flask, render_template, redirect, request, url_for, g, session
from werkzeug.utils import secure_filename
import util
import os
import data_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["IMAGE_UPLOADS"] = "./static/images"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024

QUESTIONS_FILE_PATH = "./sample_data/question.csv"
ANSWERS_FILE_PATH = "./sample_data/answer.csv"
QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]


@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    session.pop('user', None)
    hashed_password = data_manager.get_user_password(request.form.get('username'))
    check_password = util.verify_password(request.form.get('password'), hashed_password['password'] if hashed_password else None)
    if hashed_password is None or check_password is False:
        return render_template('login.html', error=True)
    session['user'] = request.form.get('username')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'GET':
        return render_template('register.html')
    if request.form.get('password') != request.form.get('confirm-password'):
        return render_template('register.html', error="Password and Confirm password doesn't match!")
    password = util.hash_password(request.form.get('password'))
    username = request.form.get('username')
    if data_manager.get_user(username):
        return render_template('register.html', error='This username already exists!')
    user = data_manager.create_user(username, password)
    if user is False:
        return render_template('register.html', error='This username already exists!')
    return redirect(url_for('login'))


@app.route('/')
def index():
    if g.user:
        data = data_manager.get_latest_questions()
        labels = ["submission_time", "view_number", "vote_number", "title", "message"]
        return render_template("list.html",
                               all_questions=data,
                               file_labels=labels,
                               order={"DESC": "Descending", "ASC": "Ascending"},
                               userpick_label="submission_time",
                               userpick_order="DESC",
                               )
    return redirect(url_for('login'))


@app.route('/list')
def show_questions():
    LABEL = 0
    ORDER = 1
    try:
        label_to_sortby = request.args.getlist('sorting')[LABEL]
        if label_to_sortby == None:  # if has no value, request.args returns empty dict with value None
            raise ValueError
    except:
        label_to_sortby = "submission_time"

    try:
        order = request.args.getlist('sorting')[ORDER]
        if order == None:
            raise ValueError
    except (IndexError, ValueError):
        order = "DESC"

    data = data_manager.get_all_questions(label_to_sortby, order)
    labels = ["submission_time", "view_number", "vote_number", "title", "message"]
    return render_template("list.html",
                           all_questions=data,
                           file_labels=labels,
                           order={"DESC": "Descending", "ASC": "Ascending"},
                           userpick_label=label_to_sortby,
                           userpick_order=order,
                           )


@app.route('/add-questions', methods=['GET', 'POST'])
def add_new_question():
    if request.method == 'POST':
        new_question = dict(request.form)
        image = request.files['image']
        if image.filename == "" or image.filename is None:
            new_question['image'] = ""
        else:
            image.save(os.path.join(app.config['IMAGE_UPLOADS'], image.filename))
            new_question["image"] = image.filename
        username = session['user']
        new_question.update({"user_name": username})
        data_manager.write_new_question_to_database(new_question)
        return redirect('/list')
    return render_template('add_question_or_answer.html')


"""
@app.route('/question/<question_id>/new-answerD', methods=['GET', 'POST'])  #### del the D from the end
def add_new_answer(question_id):
    if request.method == 'POST':
        new_answer = dict(request.form)
        username = session['user']
        new_answer.update({"user_name": username})
        data_manager.write_new_answer_to_database(question_id, new_answer)
        return redirect(f'/questions/{question_id}')

    return render_template('add_question_or_answer.html')
"""


@app.route('/question/<question_id>/new-comment', methods=['GET', 'POST'])
@app.route('/answer/<question_id>/<answer_id>/new-comment', methods=['GET', 'POST'])
def write_new_comment(question_id, answer_id=None):
    if request.method == 'POST':
        comment = request.form.to_dict()
        username = session['user']
        comment.update({"question_id": question_id, "user_name": username})
        data_manager.write_new_comment_to_database(comment)
        return redirect(url_for("manage_questions", question_id=question_id))

    if answer_id:
        id_type = "answer_id"
        id = answer_id
        route = url_for('write_new_comment', question_id=question_id, answer_id=answer_id)
        labelaction = "Add new comment for the answer"
    else:
        id_type = "question_id"
        id = question_id
        route = url_for('write_new_comment', question_id=question_id, answer_id=None)
        labelaction = "Add new comment for the question"
    return render_template("comment.html",
                           id_type=id_type,
                           id=id,
                           sending_route=route,
                           labelaction=labelaction,
                           method="POST")


@app.route('/questions/<question_id>')
def manage_questions(question_id):
    if request.args.getlist('addinganswer'):
        addinganswer = True
    else:
        addinganswer = False

    current_question = data_manager.get_question_by_id(question_id)
    answers_to_question = data_manager.get_answers_by_question_id(question_id)

    comments = data_manager.find_comments(question_id)

    return render_template("question-child.html",
                           question_id=int(question_id),
                           comments=comments,
                           question=current_question,
                           answers=answers_to_question,
                           addinganswer=addinganswer,
                           question_headers=QUESTION_HEADERS,
                           answer_headers=ANSWER_HEADERS)


@app.route('/modify_view/<question_id>')
def modify_view(question_id):
    data_manager.modify_view_number(question_id)
    return redirect(url_for('manage_questions', question_id=question_id))


@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    current_question = data_manager.get_question_by_id(question_id)

    if request.method == 'POST':
        updated_question = dict(request.form)
        image = request.files['image']
        if image.filename == "" or image.filename is None:
            updated_question['image'] = current_question["image"]
        else:
            image.save(os.path.join(app.config['IMAGE_UPLOADS'], image.filename))
            updated_question["image"] = image.filename
        data_manager.update_question(question_id, updated_question)
        return redirect("/")
    return render_template("add_question_or_answer.html",
                           question_id=question_id,
                           question=current_question)


@app.route('/answer/<answer_id>/edit', methods=['GET', 'POST'])
def edit_answer(answer_id):
    current_answer = data_manager.get_answer_by_answer_id(answer_id)
    question_id = current_answer['question_id']
    if request.method == "POST":
        update_answer = dict(request.form)
        data_manager.update_answer(answer_id, update_answer)
        return redirect(f'/questions/{question_id}')

    return render_template("edit-answer.html",
                           answer_id=answer_id,
                           answer=current_answer)


@app.route('/comment/<comment_id>/edit', methods=['GET', 'POST'])
def edit_comment(comment_id):
    if request.method == "POST":
        message = request.form.get("message")
        question_id = request.form.get("question_id")
        data_manager.edit_comment(comment_id, message)

        return redirect(url_for('manage_questions', question_id=question_id))

    commentdata = data_manager.get_comment_by_comment_id(comment_id)

    return render_template("comment.html",
                           id_type="question_id",
                           id=commentdata["question_id"], # need this for the post request redirection
                           sending_route=f'/comment/{comment_id}/edit',
                           labelaction='Edit comment',
                           method="POST",
                           message=commentdata["message"],)


@app.route('/question/<question_id>/<vote_method>')
def vote_questions(vote_method, question_id):
    data_manager.vote_question(vote_method, question_id)
    return redirect('/list')


@app.route('/answer/<answer_id>/<vote_method>')
def vote_answers(vote_method, answer_id):
    data_manager.vote_answer(vote_method, answer_id)
    answer = data_manager.get_answer_by_answer_id(answer_id)
    question_id = answer["question_id"]
    return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/answer/<answer_id>/delete')
def delete_answer(answer_id):
    answer = data_manager.get_answer_by_answer_id(answer_id)
    question_id = answer["question_id"]
    data_manager.delete_answer(answer_id)
    return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/<question_id>/<comment_id>/delete')
def delete_comment(question_id, comment_id):
    data_manager.delete_comment(comment_id)
    return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/question/<question_id>/delete')
def delete_question(question_id):
    data_manager.delete_question(question_id)
    return redirect('/list')


'''@app.route('/upload-image', methods=['GET', 'POST'])
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
                data_manager.upload_image_to_question(question_id, filename)
                print("Image saved")
                return redirect(request.referrer)

            else:
                print("not allowed image")
                return redirect(request.referrer)
'''


@app.route('/question/<question_id>/new-answer', methods=['GET', 'POST'])
def add_new_answer_with_image(question_id):
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            if image.filename != "":
                if data_manager.allowed_image(image.filename, app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                    print("Image saved")

                else:
                    print("not allowed image")
                    return redirect(request.referrer)

        new_answer = dict(request.form)
        if image.filename:
            new_answer.update({"image": filename})  # ugly solution, a band-aid
        else:
            new_answer.update({"image": ""})

        username = session['user']
        new_answer.update({"user_name": username})

        data_manager.write_new_answer_to_database(question_id, new_answer)
        return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/search')
def search_question():
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

    labels = ["submission_time", "view_number", "vote_number", "title", "message"]
    search_phrase = request.args.get('q')
    search_results = data_manager.search_question(search_phrase.lower())
    return render_template("list.html",
                           all_questions=search_results,
                           file_labels=labels,
                           order={True: "Descending", False: "Ascending"},
                           userpick_label=label_to_sortby,
                           userpick_order=order,
                           )


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
