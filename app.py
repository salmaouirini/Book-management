from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SECRET_KEY'] = '93f94dc7c3da1f5f83f8f585ea04c34cc445bd2cb844d089'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = 'static/uploads'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    books = db.relationship('Book', backref='author', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(400), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    books = db.relationship('Book', backref='category', lazy=True)


######################## REGISTER #####################################
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        newUser = User(username=username, password=hashed_password)
        db.session.add(newUser)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')



############################## LOGIN ################################
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.context_processor
def inject_user():
    return dict(user=current_user)



################################# USER_PROFILE ###########################
@app.route('/user/<int:id>')
def userProfile(id):
    if current_user.id != id:
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    return render_template('userProfile.html', user=user)

@app.route('/user/<int:id>/edit')
def editUser(id):
    user = User.query.get_or_404(id)
    return render_template('edit.html', user=user)

@app.route('/user/<int:id>/update', methods=['POST'])
@login_required
def update_user(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username:
            user.username = username
        
        if password:
            hashed_password = generate_password_hash(password)
            user.password = hashed_password
        
        db.session.commit()
        return redirect(url_for('userProfile', id=user.id))

    return render_template('update_user.html', user=user)


############################# LOGOUT ###########################

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    print(f"User {current_user.username} logging out")
    logout_user()
    return redirect(url_for('login'))


############################### BOOKS_CRUD ##############################
@app.route('/add-category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        if category_name:
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('add_category.html')


@app.route('/')
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/search')
def search():
    title_query = request.args.get('title', '')
    author_query = request.args.get('author', '')
    category_query = request.args.get('category', '')

    query = Book.query

    if title_query:
        query = query.filter(Book.title.ilike(f'%{title_query}%'))
    
    if author_query:
        # Get author IDs that match the query
        author_ids = [author.id for author in Author.query.filter(Author.name.ilike(f'%{author_query}%')).all()]
        query = query.filter(Book.author_id.in_(author_ids))
    
    if category_query:
        # Get category IDs that match the query
        category_ids = [category.id for category in Category.query.filter(Category.name.ilike(f'%{category_query}%')).all()]
        query = query.filter(Book.category_id.in_(category_ids))

    books = query.all()
    return render_template('index.html', books=books)

@app.route('/create_book')
def create_book():
    authors = Author.query.all()
    categories = Category.query.all()
    return render_template('create_book.html', authors=authors, categories=categories)


@app.route('/add_book', methods=['POST'])
def store_book():
    title = request.form.get('title')
    author_id = request.form.get('author_id')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    image = request.files.get('image')  

    if image and image.filename:
        filename = secure_filename(image.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(path)
    else:
        filename = None
    newBook = Book(title=title, author_id=author_id, image=filename, description=description, category_id=category_id)
    db.session.add(newBook)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/book/<int:id>/edit_book')
def edit_book(id):
    book = Book.query.get_or_404(id)
    authors = Author.query.all()
    categories = Category.query.all()
    return render_template('edit_book.html', book=book, authors=authors, categories=categories)


@app.route('/book/<int:id>/update_book', methods=['POST'])
def update_book(id):
    book = Book.query.get_or_404(id)
    title = request.form.get('title')
    author_id = request.form.get('author_id')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    image = request.files.get('image')  
    if image and image.filename:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        book.image = filename
    else:
        if not image:
            book.image = book.image
    book.title = title
    book.author_id = author_id
    book.category_id = category_id
    book.description = description
    db.session.commit()
    return redirect(url_for('show_book', id=book.id))


@app.route('/book/<int:id>')
def show_book(id):
    book = Book.query.get_or_404(id)
    return render_template('show_book.html', book=book)


@app.route('/book/<int:id>/delete_book', methods=['post'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))


################################### AUTHORS_CRUD #########################

@app.route('/create_author')
def create_author():
    return render_template('create_author.html')

@app.route('/add_author', methods=['POST'])
def store_author():
    name = request.form.get('name')
    bio = request.form.get('bio')
    
    # Create a new Author instance
    newAuthor = Author(name=name, bio=bio)
    db.session.add(newAuthor)
    db.session.commit()
    
    return redirect(url_for('index'))


@app.route('/book/<int:id>/edit_author')
def edit_author(id):
    book = Book.query.get_or_404(id)
    authors = Author.query.all()
    return render_template('edit_author.html', book=book, authors=authors)

@app.route('/book/<int:id>/update_author', methods=['POST'])
def update_author(id):
    book = Book.query.get_or_404(id)
    title = request.form.get('title')
    author_id = request.form.get('author_id')
    image = request.files.get('image')  
    if image and image.filename:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        book.image = filename
    book.title = title
    book.author_id = author_id
    db.session.commit()
    return redirect(url_for('show', id=book.id))




@app.route('/authors_books')
def authors_books():
    page = request.args.get('page', 1, type=int)
    authors = Author.query.paginate(page=page, per_page=3)  # Adjust per_page as needed
    return render_template('authors_books.html', authors=authors)


##########################################################################
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)