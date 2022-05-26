import json
import urllib.parse
import jsonpath_ng
import requests
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from random_word import RandomWords
import sqlite3
from util.sqlite import Database

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
    word_of_the_day_response = word_of_the_day()
    word = word_of_the_day_response["word"]
    part_of_speech = []
    definitions = []
    user = None

    for definition in word_of_the_day_response["definations"]:
        definitions.append(definition["text"])
        part_of_speech.append(definition["partOfSpeech"])

    word_results = zip(part_of_speech, definitions)

    if 'user_id' in session:
        db = Database()
        query = "SELECT * FROM User WHERE Id='{0}'".format(session['user_id'])
        users = db.selection_query(query)
        if len(users) > 0:
            user = users[0]

    return render_template("base.html", word=word, word_results=word_results, user=user)


@app.route('/', methods=['POST'])
def word_search():
    if 'user_id' in session:
        user_text = request.form['user_text']
        if user_text != "":
            return word_definition(user_text)
        else:
            return redirect(url_for("index"))
    else:
        redirect(url_for("index"))


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
    if 'user_id' not in session:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']

        query = "INSERT INTO User(Username, Email, Password, Firstname, Lastname) VALUES ('{0}','{1}','{2}','{3}'," \
                "'{4}') "
        query = query.format(username, email, password, name, surname)

        db = sqlite3.connect('util/dictionary.db')
        db.execute("PRAGMA foreign_keys = 1")
        db.row_factory = sqlite3.Row

        cur = db.cursor()
        cur.execute(query)
        last_id = cur.lastrowid
        db.commit()
        db.close()

        session['user_id'] = last_id

        return redirect(url_for("index"))
    else:
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


@app.route('/favorite', methods=['POST'])
def favorite():
    if 'user_id' in session:
        # Save word for user
        word = request.form['word']
        session_id = session['user_id']
        query = "INSERT INTO SavedWord(Content, UserId) VALUES('{0}','{1}')".format(word, session_id)
        db = Database()
        db.post_query(query)
        return redirect(url_for("account"))
    else:
        return redirect(url_for("index"))


def word_of_the_day():
    # Get word of the day using the random words package and API.
    # Sometimes API doesn't work and returns None instead of JSON string, causing Internal Server Error.
    global random_words
    current_word_of_the_day = random_words.word_of_the_day()
    word_of_the_day_response = json.loads(current_word_of_the_day)
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
        # Parse the JSON response to find the word, pronunciation and audio
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

        # Find the required information from the JSON response
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
        add_search_word(word, session["user_id"])

        # Show the play audio button only when a word is present
        audio_button = True
    except KeyError:
        # Render word_not_found.html if API doesn't return any definitions
        return render_template("word_not_found.html"), 404

    db = Database()
    session_id = session['user_id']
    query = "SELECT * FROM User WHERE Id={0}".format(session_id)
    users = db.selection_query(query)
    user = users[0]
    if len(users) > 0:
        return render_template("word.html", word=word, pronunciation=pronunciation, audio=audio_link,
                               word_results=word_results,
                               audio_button=audio_button, synonyms=synonyms, antonyms=antonyms, user=user)


def add_search_word(word, user_id):
    # check if word exists
    query = "SELECT * FROM SearchWord Where Content='{0}' AND UserId='{1}'".format(word, user_id)
    db = Database()
    words = db.selection_query(query)
    if len(words) > 0:
        # word already exists, increase frequency
        frequency = int(words[0]["Frequency"])
        frequency += 1
        word_id = words[0]["Id"]
        query = "UPDATE SearchWord SET Frequency='{0}' WHERE Id='{1}'".format(frequency, word_id)
    else:
        # word doesn't exist, add to searched words
        query = "INSERT INTO SearchWord(Content, Frequency, UserId) VALUES('{0}', '{1}', '{2}')".format(word, str(0),
                                                                                                        user_id)

    db = Database()
    db.post_query(query)


def get_searched_words(user_id):
    query = "SELECT * FROM SearchWord WHERE UserId='{0}'".format(user_id)
    db = Database()
    words = db.selection_query(query)
    print(words)
    return words


def get_saved_words(user_id):
    query = "SELECT * FROM SavedWord WHERE UserId='{0}'".format(user_id)
    db = Database()
    words = db.selection_query(query)
    print(words)
    return words


if __name__ == '__main__':
    app.run()
