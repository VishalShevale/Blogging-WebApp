from flask import (
    Flask,
    render_template,
    flash,
    redirect,
    url_for,
    session,
    logging,
    request,
)

# from data import Articles   this is for files dataset
from flask_mysqldb import MySQL
from wtforms import Form, TextAreaField, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import (
    wraps,
)  # with this we can't go directly dashboard without login.Safety First
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField


# create flask instance for ckeditor
app = Flask(__name__)
# add ckeditor
ckeditor = CKEditor(app)
# done for ckeditor


# configuration for MYSQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Vishal@123"
app.config["MYSQL_DB"] = "myflaskapp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

# Initialize MYSQL

mysql = MySQL(app)


# Articles = Articles()  this is from reading data from file


# app.debug = True
@app.route("/")
@app.route("/index")
# these are the decoraters


# Index
def index():
    return render_template("home.html")


# Home
@app.route("/home")
def home():
    return render_template("/home.html")


# About
@app.route("/about")
def about():
    return render_template("/about.html")


# Articles
@app.route("/articles")
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template("articles.html", articles=articles)
    else:
        msg = "No articles found"
        return render_template("articles.html", msg=msg)
    # close connection
    cur.close()


# signle article
@app.route("/article/<string:id>/")
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get article
    result = cur.execute("select * from articles where id =%s", [id])

    article = cur.fetchone()

    return render_template("/article.html", article=article)


# now we have to make the classes for the registration side all preocesses handling . we are now implementhing the OOPS concepts in it.
class RegistrationForm(Form):
    name = StringField("Name", [validators.Length(min=1, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField(
        "Password",
        [
            validators.Length(min=8),
            validators.EqualTo("confirm", message="Password do not match"),
        ],
    )
    confirm = PasswordField("Confirm password")


# user registration form
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(
            str(form.password.data)
        )  # this is for encryption purpose.

        # create a cursor
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users(name, email,username, password) VALUES(%s , %s, %s, %s)",
            (name, email, username, password),
        )

        # Commmit to DB (database)
        mysql.connection.commit()

        # close the connection
        cur.close()

        # it is like a pop up notification or a alert type meaasge
        flash("You are now registered and can log in !", "Success !")

        # now we have to redirect to login page
        return redirect(url_for("index"))
    #  now on above line i scuccessfully updated the tables and also rendered to the home / index page

    return render_template("register.html", form=form)


# now we have to set up for a user login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # get form fields
        username = request.form["username"]
        password_candidate = request.form["password"]

        # create cursor
        cur = mysql.connection.cursor()

        # get by username
        result = cur.execute("select * from users where username = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data["password"]

            # comapre passwords
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session["logged_in"] = True
                session["username"] = username

                flash("You are now logged in ", "success")
                return redirect(url_for("dashboard"))

            else:
                error = "Incorrect Password !"
                return render_template("login.html", error=error)
            # close connection
            cur.close()
        else:
            error = "Username not Found"
            return render_template("login.html", error=error)

    return render_template("login.html")


# for url hiding we use the if else loops or maybe some special conditions in navbar html page
# here we just used the value of session which we have assigned after the successfull login.
# so it is useful for url hiding


# now the main challange to not give direct acces without the login
# to links inside the login session
# for that we are using the flask decorators

#  ************This down code is for that thing  **********


# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please out", "danger")
            return redirect(url_for("login"))

    return wrap


# user logout
@app.route("/logout")
def logout():
    session.clear()
    flash("You are logged out", "success")
    return redirect(url_for("login"))


# Dashboard
@app.route("/dashboard")
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template("dashboard.html", articles=articles)
    else:
        msg = "No articles found"
        return render_template("dashboard.html", msg=msg)
    # close connection
    cur.close()


# This class is  for articles .
class ArticleForm(Form):
    title = StringField("Title", [validators.Length(min=1, max=200)])
    body = CKEditorField("Body", [validators.Length(min=20, max=200)])


# Add Article
@app.route("/add_article", methods=["GET", "POST"])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data[3:-6]
        print(body)
        # create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute(
            "insert into articles(title, body, author) values(%s,%s,%s)",
            (title, body, session["username"]),
        )

        # Commit to BD
        mysql.connection.commit()

        # close connection
        cur.close()

        flash("Article Created !", "success")

        return redirect(url_for("dashboard"))
    return render_template("add_article.html", form=form)


# start from 12 : 51 uses of ckeditor


# Edit Article
@app.route("/edit_article/<string:id>", methods=["GET", "POST"])
@is_logged_in
def edit_article(id):

    # create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("select * from articles where id = %s", [id])

    article = cur.fetchone()

    # get form
    form = ArticleForm(request.form)

    # populate artucle form field
    form.title.data = article["title"]
    form.body.data = article["body"]

    if request.method == "POST" and form.validate():
        title = request.form["title"]
        body = request.form["body"]

        # create cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)

        # Execute
        cur.execute(
            "update articles set title=%s , body=%s where id=%s", (title, body, id)
        )

        # Commit to BD
        mysql.connection.commit()

        # close connection
        cur.close()

        flash("Article Updated !", "success")

        return redirect(url_for("dashboard"))
    return render_template("edit_article.html", form=form)


# Delete Article
@app.route("/delete_article/<string:id>", methods=["post"])
@is_logged_in
def delete_article(id):

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("delete from articles where id = %s", [id])

    # commit to db
    mysql.connection.commit()

    # close connection
    cur.close()

    flash("Article Deleted", "success")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.secret_key = "secret123"
    app.run(debug=True)

# note for not wanting plane text area we use the
# ckeditor
# it is simple and wasy to use
# for forms making it awesome looking


# article developed successfully now i need to fix some bugs and issues and ui
# flash messages
# ui
# seperate databases for each user
# comments on another users article
# only authors can edit articles
# for delete no direct changes in databases   new duplicated database should be created ! 😁😁
# counting on

# this type data filling in database

# sugfs</p> <p>sfhisyf</p> <p>dsfuosgf  ?????????????????????  note


# features
# personal space
# to - do list
# notes on topics
# online paste bin
# etc.


# learn zeet
# upload this on zeet
# python anywhere


# goodnight
