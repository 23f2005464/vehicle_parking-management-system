from flask import Blueprint, request, jsonify,redirect,url_for,flash,render_template,session
from models.model import *
from passlib.hash import bcrypt
from sqlalchemy import text
from controllers.admin import admin_session,user_session

auth_bp= Blueprint('auth', __name__, url_prefix='/')

@auth_bp.route('/login_db', methods=['POST']) #endpoint url 
def login():     #endpoint name 
    if request.method=='POST':
      email=request.form['Email']
      pwd=request.form['password']
      user=User.query.filter_by(email=email).first()
      if user and bcrypt.verify(pwd,user.password):  
        session['user_id']=user.email  
        return redirect(url_for("home"))
    
      admin=Admin.query.filter_by(email=email,password=pwd).first()
      if admin and pwd==admin.password: 
          session['admin_id']=admin.email
          return redirect(url_for("admin.query")) #add_lot.query is admin_home rendering function
          
      else :
          return  render_template('error.html',message="No user Found",redirect_url=url_for("login"))

          
          
@auth_bp.route('/create_user',methods=['POST'])
def create_user():
    if request.method=='POST':
        print("user.create_user func intialized")
        email=request.form['Email']
        print(email)
        password=request.form['password']
        Full_name=request.form['Full name']
        Address =request.form['Address']
        pincode=request.form['pincode']
        print(pincode)
        
        exist_user=User.query.filter_by(email=email).first()
        if exist_user:
            flash('User with this email already exists.', 'error')
            return render_template("register.html")
        else: 
          db.session.add(User(email=email,password=bcrypt.hash(password),Full_Name=Full_name,Address=Address,Pincode=pincode))
          db.session.commit()          
          return render_template('success.html',message='Registered Successfully',redirect_url=url_for('login'))


@auth_bp.route('admin/logout' ,methods=['GET'])
def logout():
    try:
        admin = admin_session()
        user = user_session()

        if admin and admin.id:
            db.session.execute(text('''
                DELETE FROM parking_spots
                WHERE lot_id IN (
                    SELECT id FROM parking_lots WHERE admin_id = :admin_id
                ) AND status = 'I'
            '''), {"admin_id": admin.id})
            db.session.commit()
            session.clear()
            print("log :: admin logged out successfully")
            # flash("Logged out successfully.")
            return  render_template('successfull.html',message="Logged out successfully",redirect_url=url_for("login"))

        elif user:
            session.clear()
            print("log :: user logged out")
            return  render_template('successfull.html',message="Logged out successfully",redirect_url=url_for("login"))

        # flash("No user/admin session found.")
        return  render_template('successfull.html',message="No user/admin session found.",redirect_url=url_for("login"))

    except Exception as e:
        print("log :: exception in logout:", e)
        return redirect(url_for("login"))

@auth_bp.route('forgot_pwd',methods=['GET','POST'])
def forgot_pwd():
    if request.method=='GET':
          print("user.forgot_pwd intialized as get and rendered html")
          return render_template('forgot_pwd.html')
    if request.method=='POST':
        print("user.forgot_pwd intialized")
        email=request.form['Email']
        Full_Name=request.form['Full_name']
        new_password=request.form['new_pwd'] 
        user=User.query.filter_by(email=email,Full_Name=Full_Name).first()
        if user and bcrypt.verify(new_password,user.password):
            return  render_template('error.html',message="Previous password cannot be updated!",redirect_url=url_for('login')) 
        if user :
            user.password=bcrypt.hash(new_password)
            db.session.commit()
            return render_template('success.html',message="Password Updated",redirect_url=url_for('login'))
        else : 
            return render_template('error.html',message="User Not Found!",redirect_url=url_for('auth.forgot_pwd'))    
        