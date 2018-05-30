from flask import Flask, render_template, flash, request, url_for, redirect, session
from passlib.hash import pbkdf2_sha256
#from . import models
import datetime
from .models import *
from .generate import sample_database
from pony import orm
from functools import wraps
from pathlib import Path

COURSES_DICT = {"Programming" : "cprogramming/", 
								"Python" : "pythonprog/"}

sql_file = Path("lms.sqlite")
# session = {}

try:
	db.bind(provider='sqlite', filename = 'lms.sqlite', create_db=True)
	db.generate_mapping(create_tables=True)
except TypeError:	# avoid repeated binding
	pass

try:
	sample_database(db)
except orm.core.TransactionIntegrityError: #database has already been created
	pass
	
app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yXR~XHH!jmN]LWX/,?RT'

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to be logged in")
			return redirect(url_for("homepage"))
	return wrap

@app.route('/', methods = ["GET", "POST"])
@orm.db_session
def homepage():
	error = None
	try:
		if 'logged_in' in session.keys():
			if session['logged_in']:
				return redirect(url_for("dashboard"))
		if request.method == "POST":
			attempted_email = request.form['email']
			attempted_password = request.form['password']
			validating_user = Person[attempted_email]
			if pbkdf2_sha256.verify(attempted_password, validating_user.password_hash):
				session['logged_in'] = True
				session['email'] = attempted_email
				return redirect(url_for("dashboard"))
			else:
				error = "Invalid credentials. Try again"
				flash(error)
		return render_template("index.html")
	
	except Exception as e:
		flash("Invalid credentials. Try again")
		flash(e)
		return render_template("index.html", error=error)

@app.route("/profile")
@login_required
@orm.db_session
def profile():
	person = Person[session['email']]
	markings = orm.select(m for m in Markings if m.student == person)[:]
	gpa = 0
	for m in markings: 
		if m.curr_mark and m.exam_mark:
			gpa += (m.curr_mark * m.course.curr_weight + m.exam_mark * m.course.exam_weight)
	gpa = gpa / len(markings)
	return render_template("profile.html", user=person, markings=markings, gpa = gpa)

@app.route("/logout")
@login_required
def logout():
	session.clear()
	flash("You have been logged out!")	
	return redirect(url_for("homepage"))

@app.route('/dashboard/')
@login_required
@orm.db_session
def dashboard():
	person = Person[session['email']]
	if person.access_level == 1:
	    markings = orm.select(m for m in Markings if m.student.email == session['email'])
	    courses_list = [x.course for x in markings[:]]
	    tasks = orm.select(t for t in Task if t.owner == person and not t.task.endswith('@'))
	    imp = orm.select(t for t in Task if t.owner == person and t.task.endswith('@'))
	    events = orm.select(e for e in Event if e.owner == person)
	    homeworks = orm.select(h for h in Homework if 	h.lesson.course_belong in courses_list)
	    calendar = 'calendar' in session
	return render_template("dashboard.html", markings = markings, tasks = tasks, imp = imp, events = events, homeworks = homeworks, calendar=calendar)


@app.route('/courses/<int:courseid>')
@login_required
@orm.db_session
def coursepage(courseid):
	try:
		course = Course[courseid]
		markings = orm.select(m for m in Markings if m.student.email == session['email'] and m.course.course_id == courseid)
		lessons = orm.select(l for l in Lesson if l.course_belong.course_id == courseid)
		return render_template("coursepage.html", course = course, markings=markings, lessons = lessons)

	except Exception as e:
		flash(str(e))
		return redirect(url_for("homepage"))

@app.route('/courses/<int:courseid>/<int:lessonid>')
@login_required
@orm.db_session
def lessonpage(courseid, lessonid):
	try:
		course = Course[courseid]
		lesson= Lesson[lessonid]
		homework = orm.select(h for h in Homework if h.lesson == lesson)
		return render_template("lessonpage.html", course = course, lesson = lesson, homework = homework)

	except Exception as e:
		flash(str(e))

@app.errorhandler(404)
def not_found_error(e):
	return render_template("404.html")		

@app.route("/addtask", methods = ["POST"])
@orm.db_session
def addtask():
	task = request.form['newtask']
	owner = Person[session['email']]
	session['calendar'] = True
	Task(task = task, owner=owner)
	return redirect(url_for("dashboard") + "#pills-calendar")

@app.route("/addcalevent", methods = ["POST"])
@login_required
@orm.db_session
def addcalevent():
	try:
		year = datetime.datetime.now().year
		day = request.form['date']
		month = request.form['month']
		event = request.form['event']
		owner = Person[session['email']]
		newdate = date(year, int(month), int(day))
		session['calendar'] = True
		Event(task = event, owner=owner, date=newdate)

		return redirect(url_for("dashboard"))
	except ValueError:
		flash("Please enter valid date")
		return redirect(url_for("dashboard") + "#pills-calendar")

@app.route("/del/<task>")
@login_required
@orm.db_session
def delete(task):
	Task[task].delete()
	session['calendar'] = True
	return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run()