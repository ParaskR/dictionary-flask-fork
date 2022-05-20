from flask import Flask, render_template

app = Flask(__name__)


@app.route('/home')
def home():  # put application's code here
    return render_template("home.html")


@app.route('/login')
def login():  # put application's code here
    return render_template("login.html")


@app.route('/register')
def register():  # put application's code here
    return render_template("register.html")


if __name__ == '__main__':
    app.run()
