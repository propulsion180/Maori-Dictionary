# This is all the things I have to import
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from datetime import *

app = Flask(__name__) #app name
bcrypt = Bcrypt(app) #Just things for the encrytion to work
app.secret_key = "adfaef3234fwef4rg423refaewsf" # This is the key for the encrytion

def create_connection(db_file): # This function is used to make a connection with the database.
    try:                        #It is used when ever I do a query.
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)


def return_page(page, **extras): # This function does the rendering of the webpages. It allows me to pass through all of the cateogory information to all the pages.
    con = create_connection("maori_dictionary.db") # Makes connection and executes query to get category information.

    query = "SELECT categoryid, category  FROM category"

    cur = con.cursor()
    cur.execute(query)
    categorylist = dict(cur.fetchall())
    print(categorylist)
    con.close

    return render_template(page, categories=categorylist, **extras) # Renders all the webpages and sends category information.


def get_date(): # Is used to give date to any route that is going to change values in the database.
    date = datetime.now()
    return date.strftime("%d/%m/%Y")


def duplicate_check(m, e, c, d, l): # Checks if any words that are inputted already exist in the database.
    con = create_connection("maori_dictionary.db") # Query tries to find any words that have all of the main columns the same.

    query = "SELECT maori, english, category, definition, level, picture FROM dictionary_values WHERE maori=? and english=? and category=? and definition=? and level=?"

    cur = con.cursor()
    cur.execute(query, (m, e, c, d, l))
    values = cur.fetchall()
    print(values)
    con.close()

    if values == None: # If the word is duplicate False is returned otherwise True is returned.
        return True
    else:
        return False


def validity_checker(m, e, c, d, l): # Checks if words that are added are valid.
    if len(m) <= 0 or len(e) <= 0 or c == 0 or len(d) == 0 or l == 0 or int(l) > 10 or type(m) == int or type(e) == int or type(d) == int:
        return False
    else:
        return True #If the word is not valid False is returned otherwise True is returned.


@app.route('/') # Homepage
def render_home():
    message = request.args.get("message") # Gets the homepage message

    if is_logged_in(): # Tells me in the terminal that a user is logged in.
        print("logged in")

    return return_page('home.html', message=message, logged_in=is_logged_in()) # Displays the homepage and sends message to HTML.


@app.route('/categorypage') # Cateogory Page
def render_categorypage():
    categoryid = request.args.get("category") #Gets the categroy from the URL argument in the link.

    con = create_connection("maori_dictionary.db") # Gets all the words in that category and puts them into "words".
    query = "SELECT id, maori, english, category, definition, level, picture FROM dictionary_values WHERE category=?"
    cur = con.cursor()
    cur.execute(query, (categoryid,))
    words = cur.fetchall()
    print(words)
    con.close()

    con = create_connection("maori_dictionary.db") # Gets category data for this category and sends it to the HTML.
    query = "SELECT categoryid, category  FROM category WHERE categoryid=?"
    cur = con.cursor()
    cur.execute(query, (categoryid,))
    categoryname = cur.fetchall()[0]
    con.close()

    return return_page('categorypage.html', words=words, category=categoryname, logged_in=is_logged_in()) # Renders the category page and sends info to HTML.


@app.route('/wordpage') # Word Page
def render_wordpage():
    id = request.args.get("word") #Gets the information from the URL arguments.
    categoryname = request.args.get("category")

    con = create_connection("maori_dictionary.db") # Gets all the information for the one word.
    query = "SELECT id, maori, english, category, definition, level, picture, userid, date_modified FROM dictionary_values WHERE id=?"
    cur = con.cursor()
    cur.execute(query, (id,))
    print(cur.fetchall)
    one = cur.fetchall()[0]
    userid = one[7]
    print(userid)
    print(one)
    con.close()

    con = create_connection("maori_dictionary.db") # This gets all the creator/modifiers information.
    query = "SELECT fname, lname, email FROM users WHERE id=?"
    cur = con.cursor()
    cur.execute(query, (userid,))
    details = cur.fetchall()
    print(details[0])
    fname = details[0][0]
    lname = details[0][1]
    email = details[0][2]
    con.close()

    return return_page('wordpage.html', oneword=one, category=categoryname, logged_in=is_logged_in(), fname=fname, lname=lname, email=email) # renders the wordpage and sends all the information to the HTML page.


@app.route('/signup', methods=['GET', 'POST']) #Signup page
def render_signup():
    if request.method == 'POST':
        print(request.form) # prints the request form to the console.
        fname = request.form.get('fname').strip().title()# All the new users info from the signup page.
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2: # validation password
            return redirect("/signup?error=Passwords+dont+match")

        if len(password) < 8:# validation password
            return redirect('/signup?error=Password+must+be+8+characters+or+more')

        hashed_password = bcrypt.generate_password_hash(password) # Encrypting the password

        con = create_connection('maori_dictionary.db') # Makes the connection
        query = "INSERT INTO users (id, fname, lname, email, password) " \
                "VALUES(NULL,?,?,?,?)"
        cur = con.cursor()
        try:# Tries to do the query
            cur.execute(query, (fname, lname, email, hashed_password))  # Makes the query and inserts the values.
        except sqlite3.IntegrityError: # If the query fails the code below happens.
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')# Sends the user to login after making the account.

    return return_page('signup.html')# renders the signup page.


@app.route('/addword', methods=['GET', 'POST']) # The addword page
def render_addword():
    if request.method == 'POST':
        print(request.form) # Prints the request form to the console.
        maori = request.form.get('maori').strip().lower() # Gets the nev data from the addword form.
        english = request.form.get('english').strip().lower()
        category = request.form.get('category')
        level = request.form.get('level')
        definition = request.form.get('definition').title()
        userid = session['userid']
        image = "noimage"
        date = get_date() # gets the date

        print(level)
        if duplicate_check(maori, english, category, definition, level) == False:                            # The following 4 lines of code sends the new data through a coup
            return redirect('/?message=Sorry but this word all ready exists. Please check existing words.')
        elif validity_checker(maori, english, category, definition, level) == False:
            return redirect('/?message=Sorry but the valuse that you inputed are invalid. Please try again.')
        else:

            con = create_connection('maori_dictionary.db') # Makes a connection
            query = "INSERT INTO dictionary_values (maori, english, category, definition, level, picture, userid, date_modified ) " \
                "VALUES (?,?,?,?,?,?,?,?)" # The query

            cur = con.cursor()
            try:
                cur.execute(query, (maori, english, category, definition, level, image, userid, date))  # executes the query and sends in the validated data.
            except sqlite3.IntegrityError:
                return redirect('/addwords?error=you+screwed+something+up') # If it failed it does this redirect.
            con.commit()
            con.close()
            return redirect('/?message=You have added a word.')# Sends you to the home page with the message.
    return return_page('addword.html', logged_in=is_logged_in()) # Renders the addword page.


@app.route('/login', methods=['GET', 'POST']) # Login page
def render_login():
    if request.method == "POST":
        email_account = request.form['email'].strip().lower() # Gets the data from the form.
        password = request.form['password'].strip()

        con = create_connection('maori_dictionary.db') # Creates a connection and gets data for the login process.
        query = "SELECT id, fname, password FROM users WHERE email = ?"
        cur = con.cursor()
        cur.execute(query, (email_account,))
        user_data = cur.fetchall()
        con.close()
        try: # Tries to send the data to variables
            userid = user_data[0][0]
            fname = user_data[0][1]
            db_password = user_data[0][2]
            email = email_account
            print("stuffs good")
        except IndexError:
            return redirect("/login?error=Email+fnameinvalid+or+password+incorrect")


        if not bcrypt.check_password_hash(db_password, password): # Checks if password provided is correct
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email # Makes the session and adds values to the sessin variables.
        session['userid'] = userid
        session['firstname'] = fname

        return redirect("/?message=You have logged in as " + fname) # Sends user to the homepage witha message.
    return return_page('login.html', logged_in=is_logged_in())# Renders the login page.


@app.route('/delete_category', methods=['GET', 'POST']) # The delete category page.
def render_deletecategory():
    categoryId = request.args.get("category") # Gets the category id from the URL argument.

    con = create_connection('maori_dictionary.db')  # This block of database queries first deletes all the words in that category and then deletes the category itself.
    query = "DELETE FROM dictionary_values WHERE category = ?"
    cur = con.cursor()
    cur.execute(query, (categoryId,))
    con.commit()
    con.close()
    con = create_connection('maori_dictionary.db')
    query = "DELETE FROM category WHERE categoryid = ?"
    cur = con.cursor()
    cur.execute(query, (categoryId,))
    con.commit()
    con.close()
    return redirect('/?message=You have deleted a category ') # Sends the user to the home page with a message.


@app.route('/add_category', methods=['GET', 'POST']) # Add category page.
def render_addcategory():
    if request.method == "POST":
        category_name = request.form.get("category_name").strip().lower() # Gets the category name from the form.

        con = create_connection('maori_dictionary.db') # This opens a connection and tries to insert the values into the database.
        query = "INSERT INTO category (category) VALUES(?)"
        cur = con.cursor()
        try:
            cur.execute(query, (category_name,))
        except sqlite3.IntegrityError:
            return redirect('/add_category?error=you+screwed+something+up')
        con.commit()
        con.close()
    return return_page('add_category.html', logged_in=is_logged_in()) # Renders the add category page and sends data to the HTML file.


@app.route('/delete_word', methods=['GET', 'POST']) # The delete word page
def deleteword():
    wordid = request.args.get("word") # Gets the id of the word to be deleted from the URL argument.

    con = create_connection('maori_dictionary.db') # Creates a connection and deletes the word from the dictionary_values table.
    query = "DELETE FROM dictionary_values WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (wordid,))
    con.commit()
    con.close()
    return redirect('/?message=You have deleted a word.') # This sends the user back to the homepage with a message.


@app.route('/editword', methods=['GET', 'POST']) # This is the edit word page.
def render_editwordpage():
    wordid = request.args.get("id") # This gets the id of the word to be edited from the URL argument.
    date = get_date() # This gets the dat which will be inserted into the table as the word is being modified.
    new_maori = request.form.get("maori") # This gets all the new data from the form.
    new_english = request.form.get("english")
    new_category = request.form.get("category")
    new_level = request.form.get("level")
    new_definition = request.form.get("definition")

    con = create_connection('maori_dictionary.db') # This connection and query are used to get the default values for the edit word form.
    query = "SELECT maori, english, category, definition, level FROM dictionary_values WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (wordid,))
    word_list = cur.fetchall()
    con.commit()
    con.close()


    con = create_connection('maori_dictionary.db') # This opens a connection
    query = "UPDATE dictionary_values SET maori=?, english=?, category=?, definition=?, level=?, date_modified=? WHERE id=? " # This query is used to update values in the database.
    cur = con.cursor()
    try:
        cur.execute(query, (new_maori, new_english, new_category, new_definition, new_level, date, wordid))  # This line  executes the query and inserts the data.
    except sqlite3.IntegrityError:
        return redirect("/?message=Sorry but your edit has failed. To try again navigate to the word and press the edit button.") # If the query fails then the user is sent to this page.
    con.commit()
    con.close()
    return return_page('editword.html', word_list=word_list, logged_in=is_logged_in())  # This renders the editword page and sends data to the HTML page.




@app.route('/logout') # This is the logout function.
def logout(): # Destroys the session.
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


def is_logged_in(): # Checks if and user is logged in.
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


if __name__ == '__main__':
    app.run()
