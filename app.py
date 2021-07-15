from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "adfaef3234fwef4rg423refaewsf"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)


def return_page(page, **extras):
    con = create_connection("maori_dictionary.db")

    query = "SELECT categoryid, category  FROM category"

    cur = con.cursor()
    cur.execute(query)
    categorylist = dict(cur.fetchall())
    con.close

    return render_template(page, categories=categorylist, **extras)


@app.route('/')
def render_home():
    if is_logged_in():
        print("logged in")

    print(session)
    return return_page('home.html', logged_in=is_logged_in())


@app.route('/words', methods=['GET', 'POST'])
def render_menu_page():
    con = create_connection("maori_dictionary.db")

    query = "SELECT maori, english, category, definintion, level, picture FROM dictionary_values"

    cur = con.cursor()
    cur.execute(query)
    dictionary_values = cur.fetchall()
    con.close()

    return return_page('words.html', dictionary_values=dictionary_values)


@app.route('/categorypage')
def render_categorypage():
    categoryid = request.args.get("category")
    print(categoryid)

    con = create_connection("maori_dictionary.db")

    query = "SELECT id, maori, english, category, definition, level, picture FROM dictionary_values WHERE category=?"

    cur = con.cursor()
    cur.execute(query, (categoryid,))
    words = cur.fetchall()
    print(words)
    con.close()

    con = create_connection("maori_dictionary.db")

    query = "SELECT categoryid, category  FROM category WHERE categoryid=?"

    cur = con.cursor()
    cur.execute(query, (categoryid,))
    categoryname = cur.fetchall()[0][1]
    return return_page('categorypage.html', words=words, categoryname=categoryname)


@app.route('/wordpage')
def render_wordpage():
    id = request.args.get("word")
    print(id)

    con = create_connection("maori_dictionary.db")

    query = "SELECT maori, english, category, definition, level, picture FROM dictionary_values WHERE id=?"

    cur = con.cursor()
    cur.execute(query, (id,))

    one = cur.fetchall()[0]
    print(one)
    con.close()

    return return_page('wordpage.html', oneword=one)


@app.route('/signup', methods=['GET', 'POST'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').strip().title()
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect("/signup?error=Passwords+dont+match")

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+8+characters+or+more')

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection('maori_dictionary.db')

        query = "INSERT INTO users (id, fname, lname, email, password) " \
                "VALUES(NULL,?,?,?,?)"

        cur = con.cursor()  # You need this line next

        try:
            cur.execute(query, (fname, lname, email, hashed_password))  # this line actually executes the query
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()

    return return_page('signup.html')


@app.route('/addword', methods=['GET', 'POST'])
def render_addword():
    if request.method == 'POST':
        print(request.form)
        maori = request.form.get('maori').strip()
        english = request.form.get('english').strip()
        category = request.form.get('category').strip()
        level = request.form.get('level')
        definition = request.form.get('definition').title()

        con = create_connection('maori_dictionary.db')

        query = "INSERT INTO dictionary_values (maori, english, category, definition, level) " \
                "VALUES(?,?,?,?,?)"

        cur = con.cursor()  # You need this line next

        try:
            cur.execute(query, (maori, english, category, definition, level))  # this line actually executes the query
        except sqlite3.IntegrityError:
            return redirect('/addwords?error=you+screwed+something+up')

        con.commit()
        con.close()
    return return_page('addword.html')


@app.route('/login', methods=['GET', 'POST'])
def render_login():
    if request.method == "POST":
        email_account = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = "SELECT id, fname, password FROM users WHERE email = ?"
        con = create_connection('maori_dictionary.db')
        cur = con.cursor()
        cur.execute(query, (email_account,))
        user_data = cur.fetchall()
        con.close()
        # if given the email is not in the database this will raise an error
        # would be better to find out how to see if the query return an empty resultset
        try:
            userid = user_data[0][0]
            fname = user_data[0][1]
            db_password = user_data[0][2]
            email = email_account
            print("stuffs good")
        except IndexError:
            return redirect("/login?error=Email+fnameinvalid+or+password+incorrect")

        # check if the password is incorrect for that email address

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = fname

        print(session)

    return return_page('login.html', logged_in=is_logged_in())


@app.route('/delete_category', methods=['GET', 'POST'])
def render_deletecategory():
    if request.method == "POST":
        if is_logged_in():
            category = request.form.get('category').strip().lower()
            print(category)

            con = create_connection("maori_dictionary.db")
            query = "SELECT categoryid FROM category WHERE category = ?"
            cur = con.cursor()
            cur.execute(query, (category,))
            categoryid = (cur.fetchall()[0])[0]
            print(categoryid)


            con = create_connection('maori_dictionary.db')
            query = "DELETE FROM dictionary_values WHERE category = ?"
            cur = con.cursor()
            cur.execute(query, (categoryid,))
            con.commit()
            con.close()
            con = create_connection('maori_dictionary.db')
            query = "DELETE FROM category WHERE category = ?"
            cur = con.cursor()
            cur.execute(query, (category,))
            con.commit()
            con.close()

            print("all done")
        else:
            return redirect('/')

    return return_page('delete_category.html', logged_in=is_logged_in())


@app.route('/add_category', methods=['GET', 'POST'])
def render_addcategory():
    if request.method == "POST":
        if is_logged_in():
            category_name = request.form.get("category_name").strip().lower()
            print(category_name)
            print(category_name)

            con = create_connection('maori_dictionary.db')
            query = "INSERT INTO category (category) VALUES(?)"
            cur = con.cursor()
            try:
                cur.execute(query, (category_name,))  # this line actually executes the query
            except sqlite3.IntegrityError:
                return redirect('/add_category?error=you+screwed+something+up')
            con.commit()
            con.close()
        else:
            return redirect('/')
    return return_page('add_category.html', logged_in=is_logged_in())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


if __name__ == '__main__':
    app.run()
