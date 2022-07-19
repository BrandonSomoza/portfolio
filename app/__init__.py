import json
import os
import datetime
import re

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_nav import Nav, register_renderer
from flask_nav.elements import Navbar, View

from generate_map import generate_map
from navbar_renderer import NavbarRenderer

from peewee import *

from playhouse.shortcuts import model_to_dict

load_dotenv()
app = Flask(__name__)

# Create dynamic navbar Instance
nav_bar = Navbar('Navigation',
                 View('Home', 'index'),
                 View('Work Experience', 'experience'),
                 View('Hobbies', 'hobbies'),
                 View('Timeline', 'timeline')
                 )


# If in testing mode --> create in-memory sqlite database
if os.getenv("TESTING") == "true":
    print("Running in test mode")
    mydb = SqliteDatabase('file:memory?mode=memory&cache=shared',
uri=True)
else:
    mydb = MySQLDatabase(os.getenv("MYSQL_DATABASE"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=3306
    )

# Timeline 
class TimelinePost(Model):
    name = CharField()
    email = CharField()
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = mydb
mydb.connect()
mydb.create_tables([TimelinePost])

# Initialize and register Nav library
nav = Nav()
nav.register_element('navigation', nav_bar)
nav.init_app(app)
# Register the custom navbar renderer
register_renderer(app, 'navbar', NavbarRenderer)

# Load the JSON data with group member info
json_path = os.path.join(app.root_path, "static/data", "group.json")
json_data = json.load(open(json_path))

# Check if templates/generated exists, if not create the folder
folder_path = os.path.join(app.root_path, "templates/generated")
if not os.path.isdir(folder_path):
    os.mkdir(folder_path)

# Generate the Folium map HTML
generate_map(os.path.join(app.root_path, "templates/generated", "generated_map.html"), json_data)


@app.route('/')
def index():
    return render_template('index.html', json_data=json_data, title="About Us", url=os.getenv("URL"))


@app.route('/experience')
def experience():
    return render_template('experience.html', json_data=json_data, title="Work Experience", url=os.getenv("URL"))


@app.route('/hobbies')
def hobbies():
    return render_template('hobbies.html', json_data=json_data, title="Hobbies", url=os.getenv("URL"))


# This route is only used in an iframe, so it doesn't need to be on the navbar
@app.route('/map')
def travel_map():
    return render_template('generated/generated_map.html')


# Route to timeline page
@app.route('/timeline')
def timeline():
    all_posts = get_time_line_post()
    return render_template('timeline.html', title="Timeline", all_posts=all_posts)

# Adds a timeline post
@app.route('/api/timeline_post', methods=['POST'])
def post_time_line_post():
    name = request.form.get('name')
    email = request.form.get('email')
    content = request.form.get('content')

    # Adding regex pattern for email validation
    # pattern = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    pattern = '([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'

    if name == None:
        return "Invalid name", 400
    elif content == None or content == "":
        return "Invalid content", 400
    elif not (re.search(pattern, email)):
        return "Invalid email", 400


    timeline_post = TimelinePost.create(name=name, email=email, content=content)
    return model_to_dict(timeline_post)

# Gets a timeline post
@app.route('/api/timeline_post', methods=['GET'])
def get_time_line_post():
    return {
        'timeline_posts': [
            model_to_dict(p)
            for p in 
TimelinePost.select().order_by(TimelinePost.created_at.desc())
        ]
    }

# Deletes a timeline post
@app.route('/api/timeline_post', methods=["DELETE"])
def delete_time_line_post():
    sql = TimelinePost.delete()
    sql.execute
    return {
        'timeline_posts': [
            model_to_dict(p)
            for p in TimelinePost.select().order_by(TimelinePost.created_at.desc())
        ]
    }
    

    