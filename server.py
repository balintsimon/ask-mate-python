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

QUESTION_HEADERS = ["id", "submission_time", "view_number", "vote_number", "title", "message", "image"]
ANSWER_HEADERS = ["id", "submission_time", "vote_number", "question_id", "message", "image"]


@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']
        g.user_id = session['user_id']


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    session.pop('user', None)
    hashed_password = data_manager.get_user_password(request.form.get('username'))
    check_password = util.verify_password(request.form.get('password'),
                                          hashed_password['password'] if hashed_password else None)
    if hashed_password is None or check_password is False:
        return render_template('login.html', error=True)
    session['user'] = request.form.get('username')
    session['user_id'] = data_manager.get_user_id(session['user'])
 
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


@app.route('/', methods=['GET', 'POST'])
def index():
    if g.user:
        data = data_manager.get_latest_questions()
        return render_template("list.html", all_questions=data)
    return redirect(url_for('login'))


@app.route('/list')
def sort():
    if request.args.get('order_by') is None:
        data = data_manager.get_all_questions("submission_time", "DESC")
    else:
        data = data_manager.sort_questions(request.args.get('order_by'), request.args.get('order_direction'))
    return render_template('list.html',
                           all_questions=data)


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
        return redirect('/')
    return render_template('list.html')


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
    reputation = data_manager.get_reputation(current_question['user_name'])
    current_question['reputation'] = reputation['reputation']
    comments = data_manager.find_comments(question_id)

    if 'user' in session:
        question_vote = data_manager.check_if_user_voted_on_question(session['user'], question_id)
    else:
        question_vote = []

    return render_template("question-child.html",
                           question_id=int(question_id),
                           comments=comments,
                           question=current_question,
                           answers=answers_to_question,
                           addinganswer=addinganswer,
                           question_headers=QUESTION_HEADERS,
                           answer_headers=ANSWER_HEADERS,
                           question_vote=question_vote)


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
                           id=commentdata["question_id"],  # need this for the post request redirection
                           sending_route=f'/comment/{comment_id}/edit',
                           labelaction='Edit comment',
                           method="POST",
                           message=commentdata["message"], )


@app.route('/accept/<question_id>/<accepted_answer_id>')
def accept_answer(question_id, accepted_answer_id):
    data_manager.set_new_accepted_answer(question_id, accepted_answer_id)
    return redirect(url_for('manage_questions', question_id=question_id))


@app.route('/question/<question_id>/<vote_method>')
def vote_questions(vote_method, question_id):
    user_name = session["user"]
    user = data_manager.get_user_id_by_name(user_name)
    user.update({"user_name": user_name, "vote_method": vote_method})

    if data_manager.check_if_user_voted_on_question(user_name, question_id):
        result = data_manager.check_if_user_voted_on_question(user_name, question_id)
        voted = data_manager.delete_vote_on_question_from_votes_db(result, vote_method)
        if voted:
            data_manager.vote_question(vote_method, question_id)

            author = data_manager.get_author_by_question_id(question_id)["user_name"]
            author_repu = data_manager.get_reputation(author)
            new_repu = data_manager.annul_calc_reputation("question", vote_method, author_repu)
            data_manager.update_user_reputation(author, new_repu)
        return redirect(url_for("manage_questions", question_id=question_id))
    else:
        author = data_manager.get_author_by_question_id(question_id)["user_name"]
        author_repu = data_manager.get_reputation(author)
        new_repu = data_manager.calculate_reputation("question", vote_method, author_repu)
        data_manager.update_user_reputation(author, new_repu)

        data_manager.create_vote_on_question_in_votes_db(question_id, user)
        data_manager.vote_question(vote_method, question_id)
        return redirect(url_for("manage_questions", question_id=question_id))


@app.route('/answer/<answer_id>/<vote_method>')
def vote_answers(vote_method, answer_id):
    answer = data_manager.get_answer_by_answer_id(answer_id)
    question_id = answer["question_id"]

    user_name = session["user"]
    user = data_manager.get_user_id_by_name(user_name)
    user.update({"user_name": user_name, "vote_method": vote_method})

    if data_manager.check_if_user_voted_on_answer(user_name, answer_id):
        result = data_manager.check_if_user_voted_on_answer(user_name, answer_id)
        voted = data_manager.delete_vote_on_answer_from_votes_db(result, vote_method)
        if voted:
            data_manager.vote_answer(vote_method, answer_id)

            author = data_manager.get_author_by_answer_id(answer_id)["user_name"]
            author_repu = data_manager.get_reputation(author)
            new_repu = data_manager.annul_calc_reputation("answer", vote_method, author_repu)
            data_manager.update_user_reputation(author, new_repu)
        return redirect(f'/questions/{question_id}')
    else:
        author = data_manager.get_author_by_answer_id(answer_id)["user_name"]
        author_repu = data_manager.get_reputation(author)
        new_repu = data_manager.calculate_reputation("answer", vote_method, author_repu)
        data_manager.update_user_reputation(author, new_repu)

        data_manager.create_vote_on_answer_in_votes_db(answer_id, user)
        data_manager.vote_answer(vote_method, answer_id)
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
    return redirect(url_for('index'))


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
    labels = ["submission_time", "view_number", "vote_number", "title", "message"]
    search_phrase = request.args.get('q')
    search_results = data_manager.search_question(search_phrase.lower())
    return render_template("list.html",
                           all_questions=search_results,
                           file_labels=labels)


@app.route('/user', methods=['GET', 'POST'])
def list_users():
    if request.method == 'GET':
        all_users = data_manager.get_user_list()
        return render_template('users.html', all_users=all_users)


@app.route('/user/<user_id>')
def get_user_attributes(user_id):
    user_questions = data_manager.get_user_questions(user_id)
    user_answers = data_manager.get_user_answers(user_id)
    user_comments = data_manager.get_user_comments(user_id)
    return render_template('user_info.html', user_questions=user_questions, user_answers=user_answers,
                           user_comments=user_comments)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
    )
