"""Flask application with embedded chatbot and analytics"""
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask import Flask, render_template, request
from textblob import TextBlob
import random
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import matplotlib

matplotlib.use('Agg')

app = Flask(__name__)
bootstrap = Bootstrap(app)
moment = Moment(app)
app.config['SECRET_KEY'] = 'bdqVBWEsRebA4d@GiXm7'


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class Chatbot(FlaskForm):
    response = StringField('How are you feeling today?',
                           validators=[DataRequired()])
    submit = SubmitField('Submit')

class Chatbot1:
    def __init__(self):
        self.greeting = "Hi, I am here to collect your feedback. How is your whole experience in Hon's restaurant today? (press q to quit)"
        self.askname = "What is your name?"
        self.p = ['Great!', 'Nice to hear!', 'Wonderful!', 'Fantastic!']
        self.n = ['I am sorry to hear that!', 'Please accept my sincere apology', 'I hope I can make things better']
        self.farewell = 'Goodbye! Have a good day!'

    def start(self, name, g):
        g = g.lower()
        if self.sentiment(g) > 0:
            return self.positive(name, g)
        elif self.sentiment(g) == 0:
            neutral_1 = input('Do you mind expanding it a bit more?')
            if self.sentiment(neutral_1) > 0:
                return self.positive(name, g)
            else:
                return self.negative(name, g)
        else:
            return self.negative(name, g)

    def sentiment(self, res):
        return TextBlob(res).sentiment.polarity

    def positive(self, name, g):
        feedback = []
        feedback.append((random.choice(self.p), name))
        fav_part = input('Which of the following impresses you the most? Food, Vibe, Service, Others(Please specify)')
        feedback.append((random.choice(self.p), name))
        positive_1 = input('Which dish or dishes do you like the most?')
        feedback.append((random.choice(self.p), name))
        positive_2 = input('What do you like about the vibe of the restaurant?')
        feedback.append((random.choice(self.p), name))
        positive_3 = input('Any further improvements that you would want us to know?')
        feedback.append((random.choice(self.p), name))
        feedback.append((self.farewell,))
        #data.append({'Name': name, 'Sentiment': 'Positive','Favourite Part': fav_part, 'Favourite dish': positive_1, 'Favourite vibe': positive_2, 'Further comments': positive_3})
        return feedback

    def negative(self, name, g):
        feedback = []
        feedback.append((random.choice(self.n), name))
        negative_1 = input('Which of the following disappoints you the most? Food, Vibe, Service, Others(Please specify)')
        feedback.append((random.choice(self.n), name))
        negative_2 = input('What do you not like about it?')
        feedback.append((random.choice(self.n), name))
        negative_3 = input('Any further improvements that you would want us to know?')
        feedback.append((random.choice(self.n), name))
        feedback.append((self.farewell,))
        #data.append({'Name': name, 'Sentiment': 'Negative', 'Worst Part': negative_1, 'Reason of worst part': negative_2, 'Further comments': negative_3})
        return feedback

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', e=e), 404


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    name = None
    instr = "Please proceed to the Chatbot"
    if form.validate_on_submit():
        name = form.name.data
    return render_template('index.html', form=form, name=name, instr=instr)


@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    form = Chatbot()
    response = None
    if form.validate_on_submit():
        response = form.response.data
    return render_template('chatbot.html', form=form, response=response)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    sentiment = db.Column(db.String(10), nullable=False)
    feedback = db.Column(db.String(1000), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/feedback')
def home():
    return render_template('feedback.html')

@app.route('/ask', methods=['POST'])
def ask():
    message = request.form['message'].strip()
    user_id = int(request.form['user_id'])
    response = chatbot_response(message, user_id)
    return jsonify(response)

states = {}

def chatbot_response(message, user_id):
    if user_id not in states:
        states[user_id] = 0

    response = ""

    if states[user_id] == 0:
        response = f"Hello {message}! How do you think about Hon's Restaurant?"
        states[user_id] = 1
    elif states[user_id] == 1:
        sentiment, reply = analyze_sentiment(message)
        response = f"{reply} What do you {'like' if sentiment == 'positive' else 'dislike'} the most about the restaurant?"
        states[user_id] = 2
        states[f"{user_id}_sentiment"] = sentiment
    elif states[user_id] == 2:
        sentiment = states[f"{user_id}_sentiment"]
        store_feedback(user_id, sentiment, message)
        response = "Thank you for your feedback!"
        del states[user_id]
        del states[f"{user_id}_sentiment"]

    return {"reply": response}

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = "positive" if blob.sentiment.polarity >= 0 else "negative"
    reply = "Great to hear that you enjoyed it!" if sentiment == "positive" else "We're sorry to hear that you didn't enjoy your experience."
    return sentiment, reply

def store_feedback(user_id, sentiment, feedback):
    new_feedback = Feedback(id=user_id, name='User', sentiment=sentiment, feedback=feedback)
    db.session.add(new_feedback)
    db.session.commit()


@app.route('/analytics')
def analytics():
    feedbacks = Feedback.query.all()
    pos_count = sum(1 for f in feedbacks if f.sentiment == 'positive')
    neg_count = sum(1 for f in feedbacks if f.sentiment == 'negative')

    fig, ax = plt.subplots()
    ax.bar(['Positive', 'Negative'], [pos_count, neg_count])
    ax.set_title('Feedback Sentiments')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    return render_template('analytics.html', plot_url=plot_url)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)



