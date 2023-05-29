from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class UserModel(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True)
    profile = db.Column(db.String())

    def __init__(self, name, email, profile):
        self.name = name
        self.email = email
        self.profile = profile

