import json
import urllib.parse
import jsonpath_ng
import requests
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from random_word import RandomWords
from util.sqlite import Database
import sqlite3

random_words = RandomWords()
app = Flask(__name__)
app.secret_key = b'ACSC_430'


# Make login sessions expire after 12 hours
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=12)


# Ensure responses aren't cached for sessions and logged-in behaviour to work correctly
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# Flask routes

@app.route('/')
def index():
    # Call API to get word of the day and its definitions
    word_of_the_day_response = word_of_the_day()
    user = None

    # Error handling for word of the day
    if word_of_the_day_response:
        word = word_of_the_day_response["word"]
        part_of_speech = []
        definitions = []

        for definition in word_of_the_day_response["definations"]:
            definitions.append(definition["text"])
            part_of_speech.append(definition["partOfSpeech"])

        error_message = None
        word_results = zip(part_of_speech, definitions)

    else:
        word = None
        word_results = None
        error_message = "We are sorry but there was an error getting the Word of the Day, please refresh."

    if 'user_id' in session:
        db = Database()
        query = "SELECT * FROM User WHERE Id='{0}'".format(session['user_id'])
        users = db.selection_query(query)
        if len(users) > 0:
            saved_word = check_saved_words(word)
            user = users[0]

            return render_template("base.html", word=word, word_results=word_results, user=user,
                                   error_message=error_message, saved_word=saved_word)

    return render_template("base.html", word=word, word_results=word_results, user=user, error_message=error_message)


@app.route('/', methods=['POST'])
def word_search():
    # Call Dictionary API to show word results if user searched for a word that wasn't empty
    user_text = request.form['user_text']
    if user_text != "":
        return word_definition(user_text)
    else:
        return redirect(url_for("index"))


@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        return redirect(url_for("index"))
    else:
        redirect(url_for("index"))


@app.route('/login')
def login():
    if 'user_id' not in session:
        return render_template("login.html")
    else:
        return redirect(url_for("index"))


@app.route('/login', methods=['POST'])
def login_post():
    # Log in user if they are in the database, show error message using flash if they are not
    if 'user_id' not in session:
        username = request.form['username']
        password = request.form['password']

        query = "SELECT * FROM User WHERE Username='{0}' AND Password='{1}' OR Email='{0}' AND Password='{1}'".format(
            username, password)

        db = Database()
        users = db.selection_query(query)

        if len(users) > 0:
            session['user_id'] = users[0]['Id']
            return redirect(url_for("index"))
        else:
            flash('Wrong login credentials, please try again!')
            return redirect(url_for("login"))
    else:
        return redirect(url_for("index"))


@app.route('/register')
def register():
    if 'user_id' not in session:
        return render_template("register.html")
    else:
        return redirect(url_for("index"))


@app.route('/register', methods=['POST'])
def register_post():
    # Add new user to database and log them in
    if 'user_id' not in session:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']

        query = "INSERT INTO User(Username, Email, Password, Firstname, Lastname) VALUES ('{0}','{1}','{2}','{3}'," \
                "'{4}') "
        query = query.format(username, email, password, name, surname)

        db = Database()
        try:
            last_id = db.post_query(query)
            session['user_id'] = last_id
        except sqlite3.Error:
            flash(
                "There was an error during registration. This is most likely due to a user being registered with the "
                "email or username you chose. Please try again.")
            return redirect(url_for("register"))

    return redirect(url_for("index"))


@app.route('/account', methods=['GET'])
def account():
    # Fetch account
    if 'user_id' in session:
        db = Database()
        session_id = session['user_id']
        query = "SELECT * FROM User WHERE Id={0}".format(session_id)
        users = db.selection_query(query)
        user = users[0]
        if len(users) > 0:
            searched_words = get_searched_words(session_id)
            saved_words = get_saved_words(session_id)
            return render_template("account.html", user=user, searched_words=searched_words, saved_words=saved_words)

    else:
        return redirect(url_for("index"))


@app.route('/account', methods=['POST'])
def account_edit():
    # Edit account
    if 'user_id' in session:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']
        session_id = session['user_id']
        query = "UPDATE User SET Username='{0}', Email='{1}', Password='{2}', Firstname='{3}', " \
                "Lastname='{4}' WHERE Id={5}".format(username, email, password, name, surname, session_id)
        db = Database()
        db.post_query(query)
        return redirect(url_for("account"))
    else:
        return redirect(url_for("index"))


@app.route('/save', methods=['POST'])
def save():
    # Save word for user
    if 'user_id' in session:
        word = request.form['word']
        query = "INSERT INTO SavedWord(Content, UserId) VALUES('{0}','{1}')".format(word, session['user_id'])
        db = Database()
        db.post_query(query)
        return redirect(url_for("account"))
    else:
        return redirect(url_for("index"))


@app.route('/display_saved_word', methods=['POST'])
def display_saved_word():
    # Display the result page of a user's saved words when they click on them
    if 'user_id' in session:
        user_text = request.form['word']
        if user_text != "":
            return word_definition(user_text)
    return redirect(url_for("index"))


@app.route('/delete_saved_word', methods=['POST'])
def delete_saved_word():
    # Remove a word from a user's saved words
    if 'user_id' in session:
        word = request.form['word']
        query = "DELETE FROM SavedWord WHERE Content = '{0}' AND UserId = '{1}'".format(word, session['user_id'])
        db = Database()
        db.delete_query(query)
        return redirect(url_for("account"))
    return redirect(url_for("index"))


def word_of_the_day():
    # Get word of the day using the random words package and API.
    # Sometimes the free API doesn't work and returns None instead of JSON string, causing an Internal Server Error.
    # Thus, do appropriate error checking to see if the response is a JSON string and not NoneType and avoid the error.
    global random_words
    current_word_of_the_day = random_words.word_of_the_day()
    if current_word_of_the_day is not None:
        word_of_the_day_response = json.loads(current_word_of_the_day)
    else:
        word_of_the_day_response = False

    return word_of_the_day_response


def word_definition(word):
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    # Parse and clean the user's word so that it is appropriate for the API call
    clean_url = url + urllib.parse.quote(word)

    # Check that the url does not contain any whitespaces, i.e., that the user only entered 1 word
    if "%20" in clean_url:
        return render_template("word_not_found.html"), 404

    response = requests.get(clean_url)
    entries = response.json()

    pronunciation = None
    audio_link = None

    try:
        # Parse the API JSON response to find the word, pronunciation and audio
        query_word = jsonpath_ng.parse('[0].word[*]')
        for match in query_word.find(entries):
            word = (json.dumps(match.value)).strip('"')

        query_pronunciation = jsonpath_ng.parse('[0].phonetics[*].text[*]')
        for match in query_pronunciation.find(entries):
            pronunciation = json.loads(json.dumps(match.value))

        query_audio = jsonpath_ng.parse('[0].phonetics[*].audio[*]')
        for match in query_audio.find(entries):
            audio_link = (json.dumps(match.value)).strip('"')

        part_of_speech = []
        definitions = []
        examples = []
        synonyms = []
        antonyms = []

        # Find the required information from the API JSON response
        for entry in entries:
            for meaning in entry["meanings"]:
                for synonym in meaning["synonyms"]:
                    synonyms.append(synonym)
                for antonym in meaning["antonyms"]:
                    antonyms.append(antonym)

                for definition in meaning["definitions"]:
                    part_of_speech.append(meaning["partOfSpeech"])
                    definitions.append(definition["definition"])

                    for synonym in definition["synonyms"]:
                        synonyms.append(synonym)
                    for antonym in definition["antonyms"]:
                        antonyms.append(antonym)

                    if "example" in definition:
                        examples.append(definition["example"])
                    else:
                        examples.append("!")

        word_results = zip(part_of_speech, definitions, examples)

        users = []
        user = None
        saved_word = False
        if 'user_id' in session:
            add_search_word(word, session['user_id'])
            db = Database()
            query = "SELECT * FROM User WHERE Id={0}".format(session['user_id'])
            users = db.selection_query(query)
            user = users[0]
            saved_word = check_saved_words(word)

        # Show the play audio button only when a word is present
        audio_button = True
    except KeyError:
        # Render word_not_found.html if API doesn't return any definitions
        return render_template("word_not_found.html"), 404

    if len(users) > 0:
        return render_template("word.html", word=word, pronunciation=pronunciation, audio=audio_link,
                               word_results=word_results,
                               audio_button=audio_button, synonyms=synonyms, antonyms=antonyms, user=user,
                               saved_word=saved_word)
    else:
        return render_template("word.html", word=word, pronunciation=pronunciation, audio=audio_link,
                               word_results=word_results,
                               audio_button=audio_button, synonyms=synonyms, antonyms=antonyms)


def add_search_word(word, user_id):
    # Check if word exists
    query = "SELECT * FROM SearchWord Where Content='{0}' AND UserId='{1}'".format(word, user_id)
    db = Database()
    words = db.selection_query(query)
    if len(words) > 0:
        # Word already exists, increase frequency
        frequency = int(words[0]["Frequency"])
        frequency += 1
        word_id = words[0]["UserId"]
        query = "UPDATE SearchWord SET Frequency='{0}' WHERE UserId='{1}' AND Content='{2}'".format(frequency, word_id,
                                                                                                    word)
    else:
        # Word doesn't exist, add to searched words
        query = "INSERT INTO SearchWord(Content, Frequency, UserId) VALUES('{0}', '{1}', '{2}')".format(word, str(0),
                                                                                                        user_id)

    db = Database()
    db.post_query(query)


def get_searched_words(user_id):
    # Fetch search history
    query = "SELECT * FROM SearchWord WHERE UserId='{0}'".format(user_id)
    db = Database()
    words = db.selection_query(query)
    return words


def get_saved_words(user_id):
    # Fetch saved words
    query = "SELECT * FROM SavedWord WHERE UserId='{0}'".format(user_id)
    db = Database()
    words = db.selection_query(query)
    return words


def check_saved_words(word):
    # Check if user has a word already saved
    db = Database()
    query = "SELECT * FROM SavedWord WHERE Content='{0}' AND UserId='{1}'".format(word, session['user_id'])
    saved_words = db.selection_query(query)
    if len(saved_words) > 0:
        return True
    else:
        return False


if __name__ == '__main__':
    app.run()
