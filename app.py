from flask import Flask
from flask import Flask, request, redirect
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.debug = True
# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
# Creating an SQLAlchemy instance
db = SQLAlchemy(app)

class data_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(20),  nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(db.String(20), nullable=False)
    due_date = db.Column(db.String(20), nullable=False)

@app.route('/')
def index():
    profiles = data_table.query.all() 
    return render_template('page.html', profiles=profiles)

if __name__ == '__main__':
    app.run()