import sqlite3
import logging
import json
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.logger.info("Database connection established!")
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['connection_count'] = 0

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error(f"An article with id:{post_id} is accessed which is non-existent and a 404 page is returned")
        return render_template('404.html'), 404
    else:
        app.logger.debug(f"Article \"{post['title']}\" retrieved!")
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug('About page is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            app.logger.debug(f'Article "{title}" created successfully!')
            return redirect(url_for('index'))

    return render_template('create.html')

# Define healthz endpoint
@app.route("/healthz")
def healthz():
    try:
        connection = get_db_connection()
        connection.close()
        response = app.response_class(
                                        response=json.dumps({"result":"OK - healthy"}),
                                        status=200,
                                        mimetype='application/json'
                                        )
        app.logger.info('healthz request successfull')
        return response
    except Exception:
        response = app.response_class(
                                        response=json.dumps({"result":"ERROR - db connection failed"}),
                                        status=200,
                                        mimetype='application/json'
                                        )
        app.logger.error('healthz request failed')
        return response

@app.route("/metrics")
def metrics():
    try:
        connection = get_db_connection()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        num_posts = len(posts)
        info = {"db_connection_count": app.config['connection_count']
                , "post_count": num_posts}
        response = app.response_class(
                                        response=json.dumps({"status":"success","data":info}),
                                        status=200,
                                        mimetype='application/json'
                                        )
        app.logger.info('metrics request successfull')
        return response
    except Exception:
        response = app.response_class(
                                        response=json.dumps({"status":"error","code":0,"data":{"db_connection_count":0}}),
                                        status=200,
                                        mimetype='application/json'
                                        )
        app.logger.error('metrics request failed')
        return response

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('Starting up the application')
    app.run(host='0.0.0.0', port='3111')
