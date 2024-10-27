# Book Management App

## Overview

The Book Management App is a web application built with Flask and Django, providing a platform for users to manage books, authors, and categories. Users can register, verify their email, log in, and perform various operations such as adding, updating, and deleting books, authors, and categories. 

## Features

- **User Registration & Email Verification**
  - New users can register and will receive a verification email with a confirmation link.
  - Upon clicking the link, users are redirected to the login page.
  
- **Password Recovery**
  - Users can request a password reset if they forget their password.

- **Book Management**
  - Users can view a list of books.
  - Search books by title, author, and category.
  - Add new books, including a title, author, file, and cover image.
  - Update existing book information.
  - Delete books.

- **Category Management**
  - Users can view a list of categories.
  - Add, update, or delete categories.

- **Author Management**
  - Users can view a list of authors.
  - Add, update, or delete authors.

- **Books by Author**
  - Users can view a dedicated page showing each author and their associated books.

- **User Profile Management**
  - Users can update their name and password.
  - Option to delete their account.

## Technologies Used

- **Backend:** Flask, Django
- **Frontend:** HTML, CSS
- **Database:** SQLite (or any other preferred database)
- **Email Service:** SMTP (for sending verification emails)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/book-management-app.git
   cd book-management-app
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   flask run


