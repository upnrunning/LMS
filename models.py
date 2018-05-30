from pony import orm  # 1
from datetime import date

db = orm.Database()

class Person(db.Entity):
    email = orm.PrimaryKey(str)
    password_hash = orm.Required(str)
    name = orm.Required(str)
    birthdate = orm.Required(date)
    access_level = orm.Required(int) # 1 - student, 2 - teacher, 3 - LMS admin
    tasks = orm.Set('Task')
    
class Student(Person):
    course_year = orm.Required(int)
    courses = orm.Set('Markings')
    homeworks = orm.Set('Homework')


class Course(db.Entity):
    course_id = orm.PrimaryKey(int, auto=True)
    name = orm.Required(str)
    description = orm.Required(orm.LongStr)
    curr_weight = orm.Required(float)
    exam_weight = orm.Required(float)
    credits = orm.Required(int)
    students = orm.Set('Markings')
    lessons = orm.Set('Lesson')

class Lesson(db.Entity):
    lesson_id = orm.PrimaryKey(int, auto=True)
    course_belong = orm.Required(Course)
    title = orm.Required(str)
    body = orm.Required(orm.LongStr)
    homework = orm.Optional('Homework')

class Markings(db.Entity):
    student = orm.Required(Student)
    course = orm.Required(Course)
    curr_mark = orm.Optional(float)
    exam_mark = orm.Optional(float)

class Task(db.Entity):
    task = orm.Required(str)
    owner = orm.Required(Person)

class Event(Task):
    date = orm.Required(date)    

class Homework(db.Entity):
    lesson = orm.Required(Lesson)
    date = orm.Required(date)
    description = orm.Required(str)
    owners = orm.Set(Student)