from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'e1a139751d4d7926bb9d4d1faea91a0ffcdc05321a54d750'
app.config.from_pyfile('instance/config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    tasks = db.relationship('Todo', backref='user', lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.id}>'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/index', methods=['POST', 'GET'])
@login_required
def index():
    global error_message
    error_message = ""  # Reset error message on each request
    
    if request.method == 'POST':
        task_content = request.form.get('content')
        if task_content is not None and task_content.strip():
            new_task = Todo(content=task_content, user=current_user)  # Set user_id using current_user
            try:
                db.session.add(new_task)
                db.session.commit()
                return redirect('/index')
            except Exception as e:
                error_message = f'There was an issue adding your task: {e}'
        else:
            error_message = 'Task content cannot be empty'
    
    tasks = current_user.tasks  # Get tasks associated with current user
    return render_template('index.html', tasks=tasks, error_message=error_message)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    global error_message
    error_message = ""  # Reset error message on each request
    
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/index')
    except Exception as e:
        error_message = f'There was a problem deleting the task: {e}'
        return redirect('/index')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    global error_message
    error_message = ""  # Reset error message on each request
    
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task_content = request.form.get('content')
        if task_content is not None and task_content.strip():
            task.content = task_content
            try:
                db.session.commit()
                return redirect('/index')
            except Exception as e:
                error_message = f'There was an issue updating your task: {e}'
                return redirect(f'/update/{id}')
        else:
            error_message = 'Task content cannot be empty'
            return redirect(f'/update/{id}')
    else:
        return render_template('update.html', task=task, error_message=error_message)

@app.route('/', methods=['GET', 'POST'])
def login():
    global error_message
    error_message = ""  # Reset error message on each request
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)  # Log in the user
            next_page = request.args.get('next')  # Get the next parameter from the URL
            return redirect(next_page or '/index')  # Redirect to next page or /index

        error_message = 'Invalid username or password. Please try again.'
        return redirect('/')
    
    return render_template('login.html', error_message=error_message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    global error_message
    error_message = ""  # Reset error message on each request
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error_message = 'Both username and password are required.'
            return redirect('/register')

        new_user = User(username=username, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return 'User registered successfully!'
        except Exception as e:
            error_message = f'There was an issue registering the user: {e}'
            return redirect('/register')

    return render_template('register.html', error_message=error_message)

@app.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
