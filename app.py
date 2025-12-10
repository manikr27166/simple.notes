from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_session import Session
from otp import genotp
import flask_excel as excel
import mimetypes
import re
from cmail import send_mail
from stoken import endata,dndata
import mysql.connector
from io import BytesIO
mydb = mysql.connector.connect(user='root',host='localhost',password='Manikanta@8290',database='snm_db')
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='mani@333'
excel.init_excel(app)

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form.get('email').strip()
        email=request.form.get('email').strip()
        password=request.form.get('password').strip()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where useremail=%s',[email])
            email_count=cursor.fetchone() #(1,) or (0,)
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not connect to DB')
            return redirect(url_for('register'))
        else:
            if email_count:
                if email[0]==0:
                    gotp=genotp()
                    #crna qtae qcdh hoco
                    userdata={'username':username,'useremail':email,'userpassword':password,'server_otp':gotp}
                    subject=f'OTP verification for SNM'
                    body=f'Use the give otp {gotp}'
                    send_mail(to=email,subject=subject,body=body)
                    flash('OTP has been sent to given email')
                    return redirect(url_for('otpverify',server_data=endata(userdata)))
                elif email_count[0]==1:
                    flash('Email already existed pls check')
                    return redirect(url_for('register'))
            else:
                flash('Email id not verifed in DB')
    return render_template('register.html')

@app.route('/otpverify/<server_data>',methods=['GET','POST'])
def otpverify(server_data):
    if request.method=='POST':
        user_otp=request.form['otp1']+request.form['otp2']+request.form['otp3']+request.form['otp4']+request.form['otp5']+request.form['otp6']
        try:
            deotp=dndata(server_data)
        except Exception as e:
            print(e)
            flash('could not verify otp')
            return redirect(url_for('register'))
        else:
            if user_otp==deotp['server_otp']:
                try:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('insert into user(username,useremail,password)values(%s,%s,%s)',[deotp['username'],deotp['useremail'],deotp['userpassword']])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('DB not connected')
                    return redirect(url_for('otpverify',server_data=server_data))
                else:
                    flash('details registered successfully')
                    return redirect(url_for('login'))
            else:
                flash('OTP was wrong pls re-check')         
    return render_template('otpverify.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        login_useremail=request.form.get('email').strip()
        login_password=request.form.get('password').strip()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where useremail=%s',[login_useremail])
            email_count=cursor.fetchone() #(1,) or (0,)
        except Exception as e:
            print(e)
            flash('Could not connect to DB')
            return redirect(url_for('login'))
        else:
            if email_count[0]==1:
                cursor.execute('select password from user where useremail=%s',[login_useremail])
                stored_password=cursor.fetchone() #('Manikanta@8290',) #None
                if stored_password:
                    if stored_password[0]==login_password:
                        session['user']=login_useremail
                        return redirect(url_for('dashboard'))
                    else:
                        flash('password wrong')
                        return redirect(url_for('login'))
                else:
                    flash('could not verify password')
                    return redirect(url_for('login'))
            elif email_count[0]==0:
                flash('email not found pls check')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('please login')
        return redirect(url_for('login'))
    
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST': 
            title = request.form.get('title').strip()
            description = request.form.get('description').strip()
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('select userid from user where useremail=%s',[session.get('user')])
                user_id = cursor.fetchone()
                if user_id:
                    cursor.execute('insert into notes(n_tittle,n_content,added_by) values(%s,%s,%s)', [title,description,user_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('Could not find user')
                    return redirect(url_for('addnotes'))
            except Exception as e:
                print(e)
                flash('Could not find DB')
                return redirect(url_for('addnotes'))
            else:
                flash('Notes added successfully')
        return render_template('addnotes.html')
    else:
        flash('Please login to Add Notes')
        return redirect(url_for('login'))
    
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select notesid,n_tittle,created_at from notes where added_by=%s',[user_id[0]])
                allnotes_data=cursor.fetchall() #[(1,'python','2025-09-12'),(2,'python2','2025-09-12'),..]
                cursor.close()
            else:
                flash('could not get the user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',allnotes_data=allnotes_data)
    else:
        flash('pls login first')
        return redirect(url_for('login'))
    
@app.route('/viewnotes/<nid>')   
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from notes where added_by=%s and notesid=%s',[user_id[0],nid])
                notes_data=cursor.fetchone() #[(1,'python','2025-09-12'),(2,'python2','2025-09-12'),..]
                cursor.close()
            else:
                flash('could not get the user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewnotes.html',notes_data=notes_data)
    else:
        flash('pls login first')
        return redirect(url_for('login'))

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('delete from notes where added_by=%s and notesid=%s',[user_id[0],nid])
                mydb.commit()
                cursor.close()
            else:
                flash('Could not get user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            flash('Notes deleted successfully')
            return redirect(url_for('viewallnotes'))
    else:
        flash('Please login')
        return redirect(url_for('login'))


@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select * from notes where added_by=%s and notesid=%s',[user_id[0],nid])
                notes_data=cursor.fetchone() #(1,'python','2025-09-12')
                cursor.close()
            else:
                flash('could not get the user data to fetch notes')
                return redirect(url_for('viewallnotes'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('viewallnotes'))
        else:
            if request.method=='POST':
                updated_title=request.form.get('title').strip()
                updated_desc=request.form.get('description').strip()
                try:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select userid from user where useremail=%s',[session.get('user')])
                    user_id=cursor.fetchone() #(1,)
                    if user_id:
                        cursor.execute('update notes set n_tittle=%s,n_content=%s where added_by=%s and notesid=%s',[updated_title,updated_desc,user_id[0],nid])
                        mydb.commit()
                        cursor.close()
                    else:
                        flash('could not get the user data to fetch notes')
                        return redirect(url_for('updatenotes',nid=nid))
                except Exception as e:
                    print(e)
                    flash('DB connection error')
                    return redirect(url_for('updatenotes',nid=nid))
                else:
                    flash('Notes updated successfully')
                    return redirect(url_for('viewnotes',nid=nid))

            return render_template('updatenotes.html',notes_data=notes_data)
    else:
        flash('pls login first')
        return redirect(url_for('login'))


@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('select notesid, n_tittle, n_content, created_at from notes where added_by=%s',[user_id[0]])
                allnotes_data = cursor.fetchall()
                cursor.close()
            else:
                flash('Could not get user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            if allnotes_data:
                array_data=[list(i) for i in allnotes_data]
                headings = ['Notes_id', 'Title', 'Content', 'Created_Time']
                array_data.insert(0,headings)
                return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
            else:
                flash('No notes found to get')
                return redirect(url_for('dashboard'))
    else:
        flash('Please login')
        return redirect(url_for('login'))

@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files.get('file')
            fname=filedata.filename
            fdata=filedata.read()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from user where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone() #(1,)
                if user_id:
                    cursor.execute('insert into filesdata(filename,file_content,added_by) values(%s,%s,%s)',[fname,fdata,user_id[0]])
                    mydb.commit()
                    cursor.close()
                else:
                    flash('could not get the user data to fetch notes')
                    return redirect(url_for('dashboard'))
            except Exception as e:
                print(e)
                flash('DB connection error')
                return redirect(url_for('dashboard'))
            else:
                flash('file uploaded successfully.')
        return render_template('uploadfile.html')
    else:
        flash('pls login first to upload a file')
        return redirect(url_for('login'))
@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select fid,filename,created_at from filesdata where added_by=%s',[user_id[0]])
                allfiles_data=cursor.fetchall() 
                cursor.close()
            else:
                flash('could not get the user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallfiles.html',files_data=allfiles_data)
    else:
        flash('pls login first')
        return redirect(url_for('login'))
@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select fid,filename,file_content from filesdata where added_by=%s and fid=%s',[user_id[0],fid])
                file_data=cursor.fetchone() #(1,'resume.pdf','filedata')
                cursor.close()
            else:
                flash('could not get the user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            mime_type, encoding = mimetypes.guess_type(file_data[1])
            bytes_data=BytesIO(file_data[2])
            return send_file(bytes_data,mimetype=mime_type,as_attachment=False, download_name=file_data[1])
    else:
        flash('pls login first')
        return redirect(url_for('login'))
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from user where useremail=%s',[session.get('user')])
            user_id=cursor.fetchone() #(1,)
            if user_id:
                cursor.execute('select fid,filename,file_content from filesdata where added_by=%s and fid=%s',[user_id[0],fid])
                file_data=cursor.fetchone() #(1,'resume.pdf','filedata')
                cursor.close()
            else:
                flash('could not get the user data to fetch notes')
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('DB connection error')
            return redirect(url_for('dashboard'))
        else:
            mime_type, encoding = mimetypes.guess_type(file_data[1])
            bytes_data=BytesIO(file_data[2])
            return send_file(bytes_data,mimetype=mime_type,as_attachment=True, download_name=file_data[1])
    else:
        flash('pls login first')
        return redirect(url_for('login'))
    
@app.route('/deletefile/<fid>')
def deletefile(fid):
   if session.get('user'):
      try:
         cursor=mydb.cursor(buffered=True)
         cursor.execute('select userid from user where useremail=%s',[session.get('user')])
         user_id=cursor.fetchone() #(1,)
         if user_id:
            cursor.execute('delete from filesdata  where added_by=%s and fid=%s',[user_id[0],fid])
            mydb.commit()
            cursor.close()
         else:
            flash('could not get the user data to fetch  file')
            return redirect(url_for('dashboard'))
      except Exception as e:
         print(e)
         flash('DB connection error')
         return redirect(url_for('dashboard'))
      else:
         flash('Notes Deleted Successfully')
         return redirect(url_for('viewallfiles'))
   
   else:
      flash('please login first')
      return redirect(url_for('login'))

@app.route('/search',methods=['POST'])
def search():
    if session.get('user'):
        search_data=request.form.get('q').strip()
        strg=['A-Z0-9a-z']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(search_data):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from user where useremail=%s',[session.get('user')])
                user_id=cursor.fetchone() #(1,)
                if user_id:
                    cursor.execute('select notesid,n_tittle,created_at from notes where added_by=%s and n_tittle like %s',[user_id[0],search_data+'%'])
                    search_result=cursor.fetchall()
                    cursor.close()
                else:
                    flash('Could not fetch user data')
                    return redirect(url_for('dashboard'))
            except Exception as e:
                print(e)
                flash('Could not fetch search data')
                return redirect(url_for('dashboard'))
            else:
                return render_template('viewallnotes.html',allnotes_data=search_result)
        else:
            flash('Search data is invalid')
            return redirect(url_for('dashboard'))
    else:
        flash('pls login first')
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('pls login first')
        return redirect(url_for('login'))
@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        email=request.form.get('email').strip()
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where useremail=%s',[email])
            email_count=cursor.fetchone()#(1,) or (0,) None
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not connect to DB')
            return redirect(url_for('login'))
        else:
            if email_count:
                if email_count[0]==1:
                    subject=f'Reset link  for SNM'
                    body=f"click on the given link  {url_for('newpassword',data=endata(email),_external=True)}"
                    send_mail(to=email,subject=subject,body=body)
                    flash('Reset link has been sent to give email')
                    return redirect(url_for('forgotpassword'))
                elif email_count[0]==0:
                    flash('Email Not found pls check')
                    return redirect(url_for('login'))
            else:
                flash('Email id not verified in DB')        
    return render_template('forgotpassword.html')
@app.route('/newpassword/<data>',methods=['GET','PUT'])
def newpassword(data):
    if request.method=='PUT':
        npassword=request.get_json('password')['password']
        print(npassword)
        try:
            ddata=dndata(data) #{'username':username,'useremail':email,'userpassword':password,'server_otp':gotp}
        except Exception as e:
            print(e)
            flash('Could not verify email')
            return redirect(url_for('login'))
        else:
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update user set password=%s where useremail=%s',[npassword,ddata])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('DB not connected ')
                return redirect(url_for('newpassword',data=data))
            else:
                flash('password updated successully')
                return 'ok'
    return render_template('newpassword.html',data=data)

if __name__ == '__main__':
    app.run(debug=True,use_reloader=True)