from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'puppy'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
##############################################################################
# Homepage
##############################################################################
@app.route('/')
def index():
    return render_template('index.html')

# ###########################################################################
# Checking To See If Email Is Taken
# ###########################################################################
@app.route('/check-em', methods=['POST'])
def email():
    found = False
    mysql = connectToMySQL('python_exam')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { 'email': request.form['email'] }
    result = mysql.query_db(query, data)
    print('Hello')
    if result:
        found = True
    return render_template('partials/email.html', found=found)
############################################################################
# Registration Validation
############################################################################
@app.route("/registration", methods=['POST'])
def register():
    is_valid = True
    if len(request.form['fname']) < 1:
        is_valid = False
        flash("Please Enter a Valid First Name", "fnametoolittle")
    
    if len(request.form['lname']) < 1:
        is_valid = False
        flash("Please Enter a Valid Last Name", "lnametoolittle")

    if len(request.form['email']) < 1:
        is_valid = False
        flash("Please Enter a Valid Email", "emailtoolittle")
    
    else:
        mysql = connectToMySQL('python_exam')
        query = "Select * FROM users WHERE email=%(email)s"
        data = {
            'email': request.form['email']
        }
        result = mysql.query_db(query, data)
        if len(result) > 0:
            is_valid = False
            flash("This Email Is Already In Use", 'emailtoolittle')
    
    if len(request.form['pass']) <= 7:
        is_valid = False
        flash("Please Enter A Valid Password", 'pickpassword')
    
    if (request.form['cpass']) != request.form['pass']:
        is_valid = False
        flash("This Password Does Not Match", 'confpw')
    
    if not is_valid:
        return redirect("/")
    
    else:
        mysql = connectToMySQL('python_exam')
        pw_hash = bcrypt.generate_password_hash(request.form['pass'])
        print(pw_hash)
        query = "INSERT INTO users (first_Name, last_Name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(passW)s, NOW(), NOW());"
        data = {
            'fn': request.form['fname'],
            'ln': request.form['lname'],
            'em': request.form['email'],
            'passW': pw_hash
        }
        new_user_id = mysql.query_db(query, data)
        session['id'] = new_user_id
        session['first_name'] = request.form['fname']
        print(session['first_name'])
        print (session['id'])
        print(new_user_id)
        flash("You've Been Successfully Registered!", "Welcomein")
        return redirect("/dashboard/"+str(new_user_id))
############################################################################
# Registration Successful
############################################################################
@app.route("/success/<id>")
def registered(id):
    mysql = connectToMySQL('python_exam')
    users = "SELECT * FROM users WHERE id="+str(session['id'])
    # user = users
    fname = session['first_name']
    print(fname)
    return render_template("dashboard.html", users = users)
############################################################################
# Validating Log In
############################################################################
@app.route('/processlogin', methods=['POST'])
def logging():
    mysql = connectToMySQL('python_exam')
    query = 'SELECT * FROM users WHERE email = %(email)s'
    data = {
        'email': request.form['email']
    }
    user = mysql.query_db(query, data)
    if len(user) > 0:
        if bcrypt.check_password_hash(user[0]['password'], request.form['pass']):
            session['id'] = user[0]['id']
            return redirect('/dashboard/'+str(user[0]['id']))

        else:

            flash('That Email And Password Does Not Match', 'passwordwrong')
            return redirect('/')
############################################################################
# Logged In
############################################################################
@app.route('/dashboard/<id>')
def Loggedin(id):
    print("Hello")
    if 'id' in session:
        mysql = connectToMySQL('python_exam')
        query = "SELECT * FROM users WHERE id="+str(session['id'])
        user_info = mysql.query_db(query)
        mysql = connectToMySQL('python_exam')
        query = "SELECT * FROM myjobs RIGHT JOIN jobs ON jobs.id = myjobs.job_id"
        mysql = connectToMySQL('python_exam')
        jobs = mysql.query_db(query)
        print(jobs)
        mysql = connectToMySQL('python_exam')
        query = "SELECT myjobs.user_id, myjobs.job_id, jobs.title, jobs.location FROM myjobs JOIN jobs ON jobs.id = myjobs.job_id WHERE myjobs.user_id = "+str(session['id'])
        myjobs = mysql.query_db(query)
        print(myjobs)
        return render_template('dashboard.html', user_info = user_info, jobs = jobs, myjobs = myjobs)
    else:
        flash("You Are Not Logged In", 'loginhere')
        return redirect('/')
############################################################################
# Adding A Job
############################################################################
@app.route('/new_job/<id>')
def add_job(id):
    mysql = connectToMySQL('python_exam')
    query = "SELECT * FROM users WHERE id="+str(session['id'])
    user_info = mysql.query_db(query)
    return render_template('new.html', user_info = user_info)

############################################################################
# Adding Jobs Process
############################################################################
@app.route('/add_job', methods=['POST'])
def adding_jobs():
    is_valid = True
    if len(request.form['tname']) < 1:
        is_valid = False
        flash("This Title Is Too Short", 'titletoolittle')
        
    if len(request.form['desc']) < 5:
        is_valid = False
        flash("This Description Needs To Be Longer", 'desctoolittle')
    
    if len(request.form['location']) < 1:
        is_valid = False
        flash(" This address is too short", "loctoolittle")
    
    if not is_valid:
        return redirect('/new_job/'+str(session['id']))

    else: 
        mysql = connectToMySQL('python_exam')
        query = 'INSERT INTO jobs (title, description, location, category, created_at, updated_at, users_id) VALUES (%(tit)s, %(desc)s, %(loc)s, %(cat)s, NOW(), NOW(), %(us)s);'
        data = {
            'tit': request.form['tname'],
            'desc': request.form['desc'],
            'loc': request.form['location'],
            'cat': request.form['category'],

            'us': session['id']
        }
        mysql.query_db(query, data)
        return redirect('/dashboard/'+str(session['id']))
############################################################################
# Viewing A Job
############################################################################
@app.route('/jobs/<job_id>')
def viewjob(job_id):
    print("Hello")
    if 'id' in session:
        mysql = connectToMySQL('python_exam')
        query = "SELECT * FROM users WHERE id="+str(session['id'])
        user_info = mysql.query_db(query)
        mysql = connectToMySQL('python_exam')
        query = "SELECT * FROM jobs WHERE id="+job_id
        jobs = mysql.query_db(query)
        mysql = connectToMySQL('python_exam')
        query = "SELECT jobs.id, jobs.title, users.first_name FROM jobs JOIN users ON users.id = jobs.users_id WHERE jobs.id = "+job_id
        added = mysql.query_db(query)
        return render_template('jobs.html', user_info = user_info, job = jobs, added=added)
    else:
        flash("You Are Not Logged In", 'loginhere')
        return redirect('/')
############################################################################
# Editing Jobs
############################################################################
@app.route('/edit_jobs/<job_id>')
def editjob(job_id):
    mysql = connectToMySQL('python_exam')
    query = "Select * FROM jobs WHERE id="+job_id
    jobs = mysql.query_db(query)
    mysql = connectToMySQL('python_exam')
    query = "SELECT * FROM users WHERE id="+str(session['id'])
    user_info = mysql.query_db(query)
    print(jobs)
    return render_template('/edit.html', job = jobs[0], user_info = user_info)
############################################################################
# Editing Jobs Process
############################################################################
@app.route('/edit_jobsprocess', methods=['POST'])
def edit_jobsprocess():
    mysql = connectToMySQL('python_exam')
    query = "UPDATE jobs SET title=%(tit)s, description=%(desc)s, location=%(loc)s, updated_at=NOW() WHERE id=%(id)s"
    data = {
        "tit": request.form['tname'],
        "desc": request.form['desc'], 
        'loc': request.form['add_loc'],
        'id': request.form['job_id']
    }
    mysql.query_db(query, data)
    print("puppy")
    return redirect('/dashboard/'+str(session['id']))
############################################################################
# Adding To myjobs
############################################################################
@app.route("/addtomyjobs/<job_id>")
def adding_favs(job_id):
    print(job_id)
    mysql = connectToMySQL('python_exam')
    query = 'INSERT INTO myjobs (job_id, user_id) VALUES (%(ji)s, %(ui)s)'
    data = {
        'ji': job_id,
        'ui': session['id']
    }
    mysql.query_db(query, data)
    return redirect ("/dashboard/"+str(session['id']))
############################################################################
# Deleting a job
############################################################################
@app.route('/delete/<job_id>')
def deletejob(job_id):
    print('hello')
    mysql = connectToMySQL('python_exam')
    query = "DELETE FROM jobs WHERE id="+job_id
    mysql.query_db(query)
    return redirect('/dashboard/'+str(session['id']))
############################################################################
# Deleting a job From List
############################################################################
@app.route('/deletefromlist/<job_id>')
def deletefromlist(job_id):
    print(job_id)
    mysql = connectToMySQL('python_exam')
    query = 'DELETE FROM myjobs WHERE job_id='+job_id
    mysql.query_db(query)
    return redirect('/dashboard/'+str(session['id']))
############################################################################
# End Session
############################################################################
@app.route('/endsession/<id>')
def sessionover(id):
        session.clear()
        return redirect('/')

if __name__ == ("__main__"):
    app.run(debug=True)