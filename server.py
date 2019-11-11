from flask import Flask, render_template, redirect, request

app = Flask(__name__)


@app.route('/')
def show_questions():
    return render_template("index.html")


@app.route('/questions/<question_id>', methods=('GET', 'POST'))
def manage_questions(question_id):
    if request.method == "POST":
        pass
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