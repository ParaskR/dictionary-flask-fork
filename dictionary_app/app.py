from flask import Flask, render_template, request, escape
from random_word import RandomWords
import requests
import jsonpath_ng
import json
import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from backend.util.sqlite import Database
from backend.util.db import engine, Base

flask_app = Flask(__name__)
app = FastAPI()

Base.metadata.create_all(bind=engine)


# flask routes

@flask_app.route('/')
def index():
    return word_of_the_day()


@flask_app.route('/', methods=['POST'])
def word_search():
    user_text = request.form['user_text']
    if user_text != "":
        return word_definition(user_text)
    else:
        return render_template("base.html")


@flask_app.route('/login', methods=['GET'])
def login():
    return render_template("login.html")


@flask_app.route('/login', methods=['POST'])
def login_post():  # put flask_application's code here
    username = request.form['username']
    password = request.form['password']

    query = "SELECT * FROM User WHERE Username={0} AND Password={1} OR Email={0} AND Password={1}".format(username, password)
  
    db = Database('backend/util/dictionary.db')
    users = db.selection_query(query)
    if users.count > 0:
        return render_template("base.html")
    else:
        pass


@flask_app.route('/register')
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    name = request.form['name']
    surname = request.form['surname']

    query = "INSERT INTO User(Username, Email, Password, Firstname, Lastname) VALUES ({0},{1},{2},{3},{4})"
    db = Database('backend/util/dictionary.db')
    user = db.post_query(query.format(username, email, password, name, surname), ())
    print(user)
    if user is not None:
        print(user)
        return render_template("base.html")
    else:
        pass


@flask_app.route('/', methods=['POST'])
def word_search_post():
    user_text = request.form['user_text']
    if user_text != "":
        return word_definition(user_text)
    else:
        return render_template("base.html")


app.mount("/v1", WSGIMiddleware(flask_app))


def word_of_the_day():
    r = RandomWords()
    r = json.loads(r.word_of_the_day())

    word = r["word"]
    part_of_speech = []
    definitions = []

    for definition in r["definations"]:
        definitions.append(definition["text"])
        part_of_speech.append(definition["partOfSpeech"])

    word_results = zip(part_of_speech, definitions)
    return render_template("base.html", word=word, word_results=word_results)


def word_definition(word):
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    # Parse and clean the user's word so that it is appropriate for the API call
    clean_url = url + urllib.parse.quote(word)

    # Check that the url does not contain any whitespaces, i.e., that the user only entered 1 word
    if "%20" in clean_url:
        return render_template("word_not_found.html"), 404

    response = requests.get(clean_url)
    entries = response.json()

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
    flask_app.run()
