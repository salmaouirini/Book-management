# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Mail, Message
from sqlalchemy.orm import joinedload
import os
import reprlib

load_dotenv()


app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY')
print("SECRET_KEY:", SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_ADDRESS')
app.config['MAIL_PASSWORD'] = 'voue xtse zdbq zyop'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEBUG'] = True

s = Serializer(app.config['SECRET_KEY'])
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
UPLOAD_FOLDER = 'static/uploads'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


#################################### MODELS #######################################
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  
    is_confirmed = db.Column(db.Boolean, default=False)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    books = db.relationship('Book', backref='author', lazy=True, cascade="all, delete-orphan")

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    file = db.Column(db.String(400), nullable=True)  # PDF file
    cover_image = db.Column(db.String(400), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    books = db.relationship('Book', backref='category', lazy=True)


#################################### TOKEN_EMAIL_RESET_PASSWORD ###############################
def generate_confirmation_token(email):
    return s.dumps(email, salt='email-confirm')
def confirm_token(token, expiration=3600):
    try:
        email = s.loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False
    return email    


def generate_reset_token(email):
    return s.dumps(email, salt='password-reset')
def confirm_reset_token(token, expiration=3600):
    try:
        email = s.loads(token, salt='password-reset', max_age=expiration)
    except:
        return False
    return email  


######################### TEST_EMAIL ############################
# @app.route('/send_simple_email')
# def send_simple_email():
#     msg = Message(
#         'Simple Test Email',
#         sender=app.config['MAIL_USERNAME'],
#         recipients=[app.config['MAIL_USERNAME']]
#     )
#     msg.body = 'Test email with plain ASCII characters.'
#     try:
#         mail.send(msg)
#         return 'Simple test email sent successfully!'
#     except Exception as e:
#         return f'Failed to send simple test email: {str(e)}'



######################## REGISTER #####################################
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        hashed_password = generate_password_hash(password)
        newUser = User(username=username, password=hashed_password, email=email)
        db.session.add(newUser)
        db.session.commit()

        token = generate_confirmation_token(email)
        verification_link = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirm Your Email', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'Your link is {verification_link}'
        mail.send(msg)
        flash('A verification email has been sent to your account. Please check your email.', 'info')
        return redirect(url_for('login'))
    return render_template('register.html')


############################# EMAIL_CONFIRMATION ############################
@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if email:
        user = User.query.filter_by(email=email).first_or_404()
        if user.is_confirmed:
            flash('Your email has already been verified.', 'info')
        else:
            user.is_confirmed = True
            db.session.commit()
            flash('Your email has been successfully verified! You can now log in to your account.', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')
    return redirect(url_for('login'))


@app.route('/resend_verification_email', methods=['POST'])
def resend_verification_email():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            if user.is_confirmed:
                flash('Your email is already verified.', 'info')
            else:
                token = generate_confirmation_token(user.email)
                verification_link = url_for('confirm_email', token=token, _external=True)
                msg = Message('Resend Confirmation Email', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
                msg.body = f'Your link is {verification_link}'
                mail.send(msg)
                flash('A new verification email has been sent. Please check your email.', 'info')
        else:
            flash('Email not found. Please register first.', 'danger')
    return redirect(url_for('login'))


############################## LOGIN ################################
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_confirmed:
                login_user(user)
                return redirect(url_for('books_index'))
            else:
                flash('Please confirm your email before logging in.', 'info')
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html')


@app.context_processor
def inject_user():
    return dict(user=current_user)


############################### FORGOT_PASSWORD ############################
@app.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(email)
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your link is {reset_link}'
            mail.send(msg)
            flash('Check your email for the password reset link.', 'info')
        else:
            flash('Invalid email or password. Please try again.', 'danger')    
    return render_template('request_password_reset.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = confirm_reset_token(token)
    if not email:
        return 'The reset link is invalid or has expired.'
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(password)
        db.session.commit()
        flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')


@app.route('/resend_password_reset', methods=['POST'])
def resend_password_reset():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(email)
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Resend Password Reset Link', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your link is {reset_link}'
            mail.send(msg)
            flash('A new password reset link has been sent. Please check your email.', 'info')
        else:
            flash('Email not found. Please try again.', 'danger')
    return redirect(url_for('request_password_reset'))



################################# USER_PROFILE ###########################
@app.route('/user/<int:id>')
@login_required
def userProfile(id):
    if current_user.id != id:
        return redirect(url_for('books_index'))
    user = User.query.get_or_404(id)
    return render_template('userProfile.html', user=user)

@app.route('/user/<int:id>/edit')
@login_required
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
            flash('Username updated successfully!', 'success')
        if password:
            hashed_password = generate_password_hash(password)
            user.password = hashed_password
            flash('Password updated successfully!', 'success')
        db.session.commit()
        return redirect(url_for('userProfile', id=user.id))
    return render_template('update_user.html', user=user)


@app.route('/user/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:  
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted.', 'success')
        logout_user()  
        return redirect(url_for('books_index'))  
    flash('You are not authorized to delete this account.', 'danger')
    return redirect(url_for('login'))


############################# LOGOUT ###########################
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    print(f"User {current_user.username} logging out")
    logout_user()
    return redirect(url_for('login'))


############################### CATEGORY #############################
@app.route('/categories_list')
@login_required
def categories_list():
    categories = Category.query.all()
    return render_template('Category/categories_list.html', categories=categories)

@app.route('/search_category', methods=['GET'])
def search_category():
    category_query = request.args.get('category', '').strip()
    if category_query:
        categories = Category.query.filter(Category.name.ilike(f'%{category_query}%')).all()
    else:
        categories = Category.query.all()
    categories_list = [{'id': category.id, 'name': category.name} for category in categories]
    return jsonify(categories_list)


@app.route('/add-category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        if category_name:
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('categories_list'))
    return render_template('Category/add_category.html')


@app.route('/category/<int:id>/edit_category')
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    return render_template('Category/edit_category.html', category=category)

@app.route('/category/<int:id>/update_category', methods=['POST'])
@login_required
def update_category(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('category_name')  
    category.name = name
    db.session.commit()
    return redirect(url_for('categories_list'))

@app.route('/category/<int:id>/delete_category', methods=['post'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('categories_list'))


############################### BOOKS_CRUD ##############################
@app.route('/')
@login_required
def books_index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    books = Book.query.options(joinedload(Book.author), joinedload(Book.category)).paginate(page=page, per_page=9)
    return render_template('Books/index.html', books=books)

@app.route('/search', methods=['GET'])
@login_required
def search():
    try:
        title_query = request.args.get('title', '')
        author_query = request.args.get('author', '')
        category_query = request.args.get('category', '')
        query = Book.query
        if title_query:
            query = query.filter(Book.title.ilike(f'%{title_query}%'))
        if author_query:
            author_ids = [author.id for author in Author.query.filter(Author.name.ilike(f'%{author_query}%')).all()]
            query = query.filter(Book.author_id.in_(author_ids))
        if category_query:
            category_ids = [category.id for category in Category.query.filter(Category.name.ilike(f'%{category_query}%')).all()]
            query = query.filter(Book.category_id.in_(category_ids))
        books = query.all()
        books_list = [{
            'id': book.id,
            'title': book.title,
            'author': book.author.name,
            'category': book.category.name,
            'image': book.cover_image  
        } for book in books]
        return jsonify(books_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_book')
@login_required
def create_book():
    authors = Author.query.all()
    categories = Category.query.all()
    return render_template('Books/create_book.html', authors=authors, categories=categories)

@app.route('/add_book', methods=['POST'])
@login_required
def store_book():
    if request.method == 'POST':
        title = request.form['title']
        author_id = request.form['author_id']
        category_id = request.form['category_id']  
        file = request.files['file']
        cover_image = request.files.get('cover_image')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            image_filename = None
            if cover_image and allowed_file(cover_image.filename):
                image_filename = secure_filename(cover_image.filename)
                cover_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            new_book = Book(
                title=title,
                author_id=author_id,
                category_id=category_id,  
                file=filename,
                cover_image=image_filename
            )

            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully', 'success')
            return redirect(url_for('books_index'))
        else:
            flash('Invalid file format. Please upload an image or PDF.', 'danger')


@app.route('/book/<int:id>/edit_book')
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    authors = Author.query.all()
    categories = Category.query.all()
    return render_template('Books/edit_book.html', book=book, authors=authors, categories=categories)

@app.route('/book/<int:id>/update_book', methods=['POST'])
@login_required
def update_book(id):
    book = Book.query.get_or_404(id)
    title = request.form.get('title')
    author_id = request.form.get('author_id')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    
    # Handle cover image
    cover_image = request.files.get('cover_image')
    if cover_image and cover_image.filename:
        filename = secure_filename(cover_image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cover_image.save(image_path)
        book.cover_image = filename
    # No change if no new cover image is uploaded
    # Else, keep existing cover_image value if no file is provided

    # Handle file
    file = request.files.get('file')
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        book.file = filename
    # No change if no new file is uploaded
    # Else, keep existing file value if no file is provided

    # Update other book details
    book.title = title
    book.author_id = author_id
    book.category_id = category_id
    book.description = description
    
    db.session.commit()
    return redirect(url_for('show_book', id=book.id))

@app.route('/book/<int:id>')
@login_required
def show_book(id):
    book = Book.query.get_or_404(id)
    return render_template('Books/show_book.html', book=book)

@app.route('/book/<int:id>/delete_book', methods=['post'])
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('books_index'))


################################### AUTHORS_CRUD #########################
@app.route('/authors_list')
@login_required
def authors_list():
    authors = Author.query.all()
    return render_template('Authors/authors_list.html', authors=authors)

@app.route('/search_author', methods=['GET'])
@login_required
def search_author():
    author_query = request.args.get('author', '').strip()
    if author_query:
        authors = Author.query.filter(Author.name.ilike(f'%{author_query}%')).all()
    else:
        authors = Author.query.all()
    authors_list = [{'id': author.id, 'name': author.name} for author in authors]
    return jsonify(authors_list)


@app.route('/create_author')
@login_required
def create_author():
    return render_template('Authors/create_author.html')

@app.route('/add_author', methods=['POST'])
@login_required
def store_author():
    name = request.form.get('name')
    bio = request.form.get('bio')
    newAuthor = Author(name=name, bio=bio)
    db.session.add(newAuthor)
    db.session.commit()
    return redirect(url_for('authors_list'))

@app.route('/author/<int:id>/edit_author')
@login_required
def edit_author(id):
    author = Author.query.get_or_404(id)
    return render_template('Authors/edit_author.html', author=author)

@app.route('/author/<int:id>/update_author', methods=['POST'])
@login_required
def update_author(id):
    author = Author.query.get_or_404(id)
    name = request.form.get('author_name')  
    bio = request.form.get('bio')  
    author.name = name
    author.bio = bio
    db.session.commit()
    return redirect(url_for('authors_list'))

@app.route('/author/<int:id>')
@login_required
def show_author(id):
    author = Author.query.get_or_404(id)
    return render_template('Authors/show_author.html', author=author)

@app.route('/author/<int:id>/delete_author', methods=['post'])
@login_required
def delete_author(id):
    author = Author.query.get_or_404(id)
    db.session.delete(author)
    db.session.commit()
    flash('Author and all associated books have been deleted.', 'success')
    return redirect(url_for('authors_list'))


################################### AUTHORS_BOOKS ##################
@app.route('/authors_books')
@login_required
def authors_books():
    page = request.args.get('page', 1, type=int)
    authors = Author.query.paginate(page=page, per_page=4)
    paginated_books_by_author = {}
    for author in authors.items:
        book_page = request.args.get(f'book_page_{author.id}', 1, type=int)
        paginated_books_by_author[author.id] = Book.query.filter_by(author_id=author.id).paginate(page=book_page, per_page=3)
    return render_template('authors_books.html', authors=authors, paginated_books_by_author=paginated_books_by_author)

##########################################################################
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)