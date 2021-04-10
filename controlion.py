from flask import Flask,render_template,url_for,g,request,redirect,session
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os



app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

def get_current_user():
    user_result = None
    if "user" in session:
        user = session["user"]
        db = get_db()
        db.execute("SELECT id,name,password,expert,admin FROM users WHERE name = %s",(user,))
        user_result = db.fetchone()
    return user_result

@app.teardown_appcontext
def close(error):
    if hasattr(g,"postgres_db_conn"):
        g.postgres_db_conn.close()

    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()

@app.route("/")
def index():

    user = get_current_user()
    db = get_db()

    db.execute("SELECT questions.id,questions.question_text,asked.name AS askedname,expert.name as expertname FROM questions JOIN users AS asked ON asked.id = questions.asked_by_id JOIN users AS expert ON expert.id = questions.expert_id  WHERE questions.answer_text IS NOT NULL")
    questions = db.fetchall()



    return render_template('home.html',user=user,questions=questions)

@app.route("/register",methods=["GET","POST"])
def register():
    user = get_current_user()
    if request.method == "POST":
        db = get_db()

        db.execute("SELECT id FROM users WHERE name = %s",(request.form['name'],))
        existing_user = db.fetchone()

        if existing_user:
            return render_template('register.html',user=user,error="User already exists!")

        hashed_password = generate_password_hash(request.form["password"],method="sha256")
        db.execute("INSERT INTO users (name,password,expert,admin) VALUES (%s,%s,%s,%s)",(request.form['name'],hashed_password,'0','0'))


        session["user"] = request.form['name']

        return redirect(url_for('index'))
    return render_template('register.html',user=user)

@app.route("/login",methods=["POST", "GET"])
def login():
    user = get_current_user()
    error = None
    if request.method == 'POST':
        db = get_db()

        name = request.form["name"]
        password = request.form["password"]

        db.execute("SELECT name,password FROM users WHERE name = %s",(name,))
        result = db.fetchone()

        if result:

            if check_password_hash(result["password"],password):
                session["user"] = name
                return redirect(url_for("index"))
            else:
                error = "The password is incorrect."
        else:
            error = "The name is incorrect."
    return render_template('login.html',user=user,error=error)

@app.route("/question/<question_id>")
def question(question_id):
    user = get_current_user()
    db = get_db()


    db.execute("SELECT questions.id,questions.question_text,asked.name AS askedname,expert.name AS expertname FROM questions JOIN users AS asked ON asked.id = questions.asked_by_id JOIN users AS expert ON expert.id = questions.expert_id  WHERE questions.id = %s",(question_id))
    question = db.fetchone()



    return render_template('question.html',user=user,question=question)

@app.route("/answer/<question_id>",methods=["GET", "POST"])
def answer(question_id):
    user = get_current_user()
    db = get_db()

    if not user:
        return redirect(url_for("login"))
    if not user["expert"]:
        return redirect(url_for("index"))


    if request.method == "POST":
        db.execute("UPDATE questions SET answer_text = %s WHERE id = %s",(request.form["answer"],question_id))

        return redirect(url_for("unanswered"))

    db.execute("SELECT question_text FROM questions WHERE id = %s",(question_id,))
    question = db.fetchone()
    
    return render_template('answer.html',user=user,question=question)

@app.route("/ask",methods=["GET", "POST"])
def ask():

    user = get_current_user()

    if not user:
        return redirect(url_for("login"))


    db = get_db()
    if request.method == "POST":

        db.execute("INSERT INTO questions (question_text,asked_by_id,expert_id) VALUES (?,?,?)",[request.form["question"],user["id"],request.form["expert"]])
        db.commit()

        return redirect(url_for("ask"))




    expert_cur = db.execute("SELECT id,name FROM users WHERE expert = 1")
    expert_result = expert_cur.fetchall()

    return render_template('ask.html',user=user,experts = expert_result)

@app.route("/unanswered")
def unanswered():

    user = get_current_user()

    if not user:
        return redirect(url_for("login"))
    # if user["expert"] == 0:
    #     return redirect(url_for("index"))

    db = get_db()

    db.execute("SELECT questions.id,questions.question_text,questions.asked_by_id,users.name FROM questions JOIN users ON users.id = questions.asked_by_id WHERE questions.answer_text IS NULL AND questions.expert_id = %s",(user["id"],))
    questions = db.fetchall()

    return render_template('unanswered.html',user=user,questions=questions)

@app.route("/users")
def users():
    user = get_current_user()
 
    if not user:
        return redirect(url_for("login"))
    if not user["admin"]:
        return redirect(url_for("index"))

    db = get_db()
    db.execute("SELECT id,name,expert,admin FROM users")
    users_results = db.fetchall()

    return render_template('users.html',user=user,users=users_results)

@app.route("/logout")
def logout():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/promote/<user_id>")
def promote(user_id):

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    if not user["admin"]:
        return redirect(url_for("index"))

    db = get_db()
    db.execute("UPDATE users SET expert = True WHERE id = %s",(user_id,))



    return redirect(url_for("users"))

if __name__ == '__main__':
    app.run(debug=True)