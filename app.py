from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect
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
	return return_page('home.html')


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

	query = "SELECT id, maori, english, category, definintion, level, picture FROM dictionary_values WHERE category=?"

	cur = con.cursor()
	cur.execute(query, (categoryid, ))
	words = cur.fetchall()
	print(words)
	con.close()

	con = create_connection("maori_dictionary.db")

	query = "SELECT categoryid, category  FROM category WHERE categoryid=?"

	cur = con.cursor()
	cur.execute(query, (categoryid, ))
	categoryname = cur.fetchall()[0][1]
	return return_page('categorypage.html', words=words, categoryname=categoryname)


@app.route('/wordpage')
def render_wordpage():
	id = request.args.get("word")
	print(id)

	con = create_connection("maori_dictionary.db")

	query = "SELECT maori, english, category, definintion, level, picture FROM dictionary_values WHERE id=?"

	cur = con.cursor()
	cur.execute(query, (id, ))

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
	return return_page('login.html')


if __name__ == '__main__':
	app.run()
