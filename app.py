from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import db, Admin, Client, InternalTeam, Candidate, EmploymentHistory
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Initialize the database and create the default admin
def initialize_database():
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

        # Check if the default admin already exists
        if not Admin.query.filter_by(username='admin').first():
            # Create the default admin user
            default_admin = Admin(
                username='admin',
                password=generate_password_hash('admin', method='pbkdf2:sha256')  # Correct hash method
            )
            db.session.add(default_admin)
            db.session.commit()
            print("Default admin user created: username='admin', password='admin'")
        else:
            print("Default admin user already exists.")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        password = request.form.get('password')
            
        if user_type == 'admin':
            user = Admin.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_type'] = 'admin'
                session['username'] = username
                return redirect(url_for('admin_dashboard'))
        
        elif user_type == 'client':
            user = Client.query.filter_by(username=username).first()
            print(username)
            print(check_password_hash(user.password, password))
            print(password)
            if user and check_password_hash(user.password, password):
                session['user_type'] = 'client'
                session['client_id'] = user.id
                session['username'] = username
                session['client_name'] = user.client_name

                return redirect(url_for('client_dashboard'))
        
        elif user_type == 'internal_team':
            user = InternalTeam.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_type'] = 'internal_team'
                session['username'] = username
                return redirect(url_for('internal_team_dashboard'))
            else:
                return "Invalid pass"
        
        elif user_type == 'candidate':
            user = Candidate.query.filter_by(pan_card=username).first()
            if user and user.dob == request.form.get('dob'):
                session['user_type'] = 'candidate'
                return redirect(url_for('candidate_status', candidate_id=user.id))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        location = request.form.get('location')
        email = request.form.get('email')
        user_name = request.form.get('username')
        password=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        client = Client(client_name=client_name, location=location, email=email,username=user_name,password=password)
        db.session.add(client)
        db.session.commit()
        flash('Client registration successful. Await admin approval.')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session['user_type']:
        return redirect(url_for('login'))
    clients = Client.query.all()
    internal_teams = InternalTeam.query.all()
    return render_template('admin_dashboard.html', clients=clients, internal_teams=internal_teams)

@app.route('/manage_clients')
def manage_clients():
    # Ensure the user is logged in and is an admin
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not admin

    # Query the database to get all clients who are pending approval
    clients  = Client.query.all()
    
    return render_template('manage_clients.html', clients=clients)

@app.route('/approve_client/<int:client_id>', methods=['POST'])
def approve_client(client_id):
    # Ensure the user is logged in and is an admin
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not admin

    # Find the client by ID
    client = Client.query.get_or_404(client_id)

    if client:
        # Update client status to approved
        client.approved = True
        db.session.commit()

        flash(f"Client {client.username} approved successfully.", "success")
        return redirect(url_for('manage_clients'))  # Redirect back to the manage clients page

    flash("Client not found.", "danger")
    return redirect(url_for('manage_clients'))

@app.route('/reject_client/<int:client_id>', methods=['POST'])
def reject_client(client_id):
    # Ensure the user is logged in and is an admin
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))  # Redirect to login if not admin

    # Find the client by ID
    client = Client.query.get_or_404(client_id)

    if client:
        # Delete the client from the database (or mark them as rejected)
        db.session.delete(client)
        db.session.commit()

        flash(f"Client {client.username} rejected and removed.", "danger")
        return redirect(url_for('manage_clients'))  # Redirect back to the manage clients page

    flash("Client not found.", "danger")
    return redirect(url_for('manage_clients'))

@app.route('/client_dashboard')
def client_dashboard():
    if 'client' not in session['user_type']:
        return redirect(url_for('login'))
    all_candidates = Candidate.query.filter_by(client_id=session['client_id']).all()
    context = {'all_candidates':all_candidates, 'client_name':session['client_name'] }
    return render_template('client_dashboard.html', context=context)


@app.route('/candidate_status/<int:candidate_id>', methods=['GET'])
def view_candidate_status(candidate_id):
    if 'client_id' not in session or session.get('user_type') != 'client':
        flash('You must be logged in as a client to view candidate status.', 'danger')
        return redirect(url_for('login'))

    candidate = Candidate.query.get_or_404(candidate_id)
    # Ensure the candidate belongs to the logged-in client
    if candidate.client_id != session['client_id']:
        flash('Unauthorized access to candidate status.', 'danger')
        return redirect(url_for('client_dashboard'))
    return render_template('candidate_status.html', candidate=candidate)

@app.route('/update_candidate_status/<int:candidate_id>', methods=['GET', 'POST'])
def update_candidate_status(candidate_id):
    #if 'user_id' not in session or session.get('user_type') != 'internal_team':
        #flash('You must be logged in as an internal team member to update candidate status.', 'danger')
        #return redirect(url_for('login'))

    candidate = Candidate.query.get_or_404(candidate_id)

    if request.method == 'POST':
        # Retrieve the selected statuses for each verification check
        address_status = request.form['address_status']
        education_status = request.form['education_status']
        employment_status = request.form['employment_status']

        # Update the candidate status
        candidate.address_status = address_status
        candidate.education_status = education_status
        candidate.employment_status = employment_status

        # Commit changes to the database
        db.session.commit()

        flash(f"Status for {candidate.first_name} {candidate.last_name} has been updated!", 'success')
        return redirect(url_for('internal_team_dashboard'))

    return render_template('update_candidate_status.html', candidate=candidate)



@app.route('/internal_team_dashboard',methods=['GET','POST'])
def internal_team_dashboard():
    if 'internal_team' not in session['user_type']:
        return redirect(url_for('login'))
    all_clients = Client.query.all()

    candidates = []

    if request.method == 'POST':
        # Filter by selected client
        client_id = request.form.get('client_id')
        print(client_id)
        print(Candidate.query.filter_by(client_id=client_id).all())
        if client_id:
            candidates = Candidate.query.filter_by(client_id=client_id).all()
        else:
            flash('Please select a client to filter candidates.', 'warning')

    context = {'all_clients': all_clients,'candidates':candidates}
    return render_template('internal_team_dashboard.html', context=context)

@app.route('/candidate_status/<int:candidate_id>')
def candidate_status(candidate_id):
    if 'candidate' not in session:
        return redirect(url_for('login'))
    candidate = Candidate.query.get(candidate_id)
    return render_template('candidate_status.html', candidate=candidate)

@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate():

    if 'client' not in session['user_type']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = request.form['dob']
        pan_card = request.form['pan_card']
        education = request.form['education']
        address = request.form['address']
        client_id = session['client_id']

        
        # Create new candidate
        candidate = Candidate(first_name=first_name, last_name=last_name, dob=dob, pan_card=pan_card, education=education, address=address, client_id=client_id)
        db.session.add(candidate)
        db.session.commit()

        # Add employment history
        for i in range(1, 6):  # Loop for up to 5 employment entries
            company_name = request.form.get(f'company_name_{i}')
            if company_name:
                start_date = request.form.get(f'start_date_{i}')
                end_date = request.form.get(f'end_date_{i}')
                designation = request.form.get(f'designation_{i}')
                employment = EmploymentHistory(company_name=company_name, start_date=start_date, end_date=end_date, designation=designation, candidate_id=candidate.id)
                db.session.add(employment)

        db.session.commit()
        flash('Candidate added successfully!')
        return redirect(url_for('client_dashboard'))
    
    return render_template('add_candidate.html')

@app.route('/add_internal_team', methods=['GET', 'POST'])
def add_internal_team():
    #if 'user_id' not in session or session.get('user_type') != 'admin':
     #   flash('You must be logged in as an admin to add internal team members.', 'danger')
      #  return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']

        # Generate username and default password
        username = f"{last_name[0].lower()}{first_name[:4].lower()}"
        password = generate_password_hash('1234')  # Default password is "1234"

        # Check if the username already exists
        existing_user = InternalTeam.query.filter_by(username=username).first()
        if existing_user:
            flash('A user with this username already exists.', 'danger')
            return redirect(url_for('add_internal_team'))

        # Add the new internal team member
        new_user = InternalTeam(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='internal_team'
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f'Internal team member {first_name} {last_name} added successfully! Username: {username}, Password: 1234', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_internal_team.html')


if __name__ == '__main__':
    initialize_database() 
    app.run(debug=True)
