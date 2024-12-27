from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)  # New field for username
    password = db.Column(db.String(200), nullable=False)  # Hashed password
    role = db.Column(db.String(50), default="Client")  # Role field (Client, Candidate, etc.)
    approved = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'Client {self.username}, password: {self.password}>'

class InternalTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    pan_card = db.Column(db.String(20), nullable=False, unique=True)
    education = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    employment_history = db.relationship('EmploymentHistory', backref='candidate', lazy=True)
    status = db.Column(db.String(20), default="Pending")
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

class EmploymentHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
