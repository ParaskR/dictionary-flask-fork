import json
import urllib.parse

import jsonpath_ng
import requests
from flask import Flask, render_template, request, session, redirect
from random_word import RandomWords

from util.sqlite import Database

random_words = RandomWords()
flask_app = Flask(__name__)
flask_app.secret_key = b'ACSC_430'


# flask routes

@flask_app.route('/')
def index():
    word_of_the_day_response = word_of_the_day()
    word = word_of_the_day_response["word"]
    part_of_speech = []
    definitions = []

    for definition in word_of_the_day_response["definations"]:
        definitions.append(definition["text"])
        part_of_speech.append(definition["partOfSpeech"])

    word_results = zip(part_of_speech, definitions)

    if 'user_id' in session:
        db = Database()
        query = "SELECT * FROM User WHERE Id={0}".format(session['user_id'])
        users = db.selection_query(query)
        if len(users) > 0:
            user = users[0]
            return render_template("account_nav.html", word=word, word_results=word_results, user=user)

    return render_template("account_nav.html", word=word, word_results=word_results)


@flask_app.route('/', methods=['POST'])
def word_search():
    user_text = request.form['user_text']
    if user_text != "":
        return word_definition(user_text)
    else:
        return redirect("/")


@flask_app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect("/")


@flask_app.route('/login')
def login():
    return render_template("login.html")


@flask_app.route('/login', methods=['POST'])
def login_post():  # put flask_application's code here
    username = request.form['username']
    password = request.form['password']

    query = "SELECT * FROM User WHERE Username='{0}' AND Password='{1}' OR Email='{0}' AND Password='{1}'".format(
        username, password)

    db = Database()
    users = db.selection_query(query)

    if len(users) > 0:
        session['user_id'] = users[0]['Id']
        return redirect("/")
    else:
        return "USER NOT FOUND"


@flask_app.route('/register')
def register():
    return render_template("register.html")


@flask_app.route('/register', methods=['POST'])
def register_post():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    name = request.form['name']
    surname = request.form['surname']

    query = "INSERT INTO User(Username, Email, Password, Firstname, Lastname) VALUES ('{0}','{1}','{2}','{3}','{4}')"
    query = query.format(username, email, password, name, surname)
    db = Database()
    user = db.post_query(query)

    if user:
        return redirect("/")


@flask_app.route('/account', methods=['GET'])
def account():
    # fetch account
    if session['user_id'] is not None:
        db = Database()
        session_id = session['user_id']
        query = "SELECT * FROM User WHERE Id={0}".format(session_id)
        users = db.selection_query(query)
        user = users[0]
        if len(users) > 0:
            return render_template("account.html", user=user)

    else:
        return redirect("/")


@flask_app.route('/account', methods=['POST'])
def account_edit():
    # edit account
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    name = request.form['name']
    surname = request.form['surname']
    user = (username, email, password, name, surname)
    session_id = session['user_id']
    query = "UPDATE User SET Username='{0}', Email='{1}', Password='{2}', Firstname='{3}', " \
            "Lastname='{4}' WHERE Id={5}".format(username, email, password, name, surname, session_id)
    db = Database()
    db.post_query(query)
    return render_template('account.html', user=user)


@flask_app.route('/favorite', methods=['POST'])
def favorite():
    word = request.form['word']
    session_id = session['user_id']
    query = "INSERT INTO Word(Content, UserId) VALUES('{0}','{1}')".format(word, session_id)
    db = Database()
    db.post_query(query)
    return redirect("/account")


def word_of_the_day():
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

        # Show the play audio button only when a word is present
        audio_button = True
    except KeyError:
        # Render word_not_found.html if API doesn't return any definitions
        return render_template("word_not_found.html"), 404

    return render_template("word.html", word=word, pronunciation=pronunciation, audio=audio_link,
                           word_results=word_results,
                           audio_button=audio_button, synonyms=synonyms, antonyms=antonyms)


if __name__ == '__main__':
    flask_app.run(debug=True)
