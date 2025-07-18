from flask import Flask,render_template,redirect,url_for,session
from models.model import *
from sqlalchemy import text #for raw SQL queries
from controllers.authentication import auth_bp,user_session,admin_session
from controllers.user import user_bp 
from controllers.admin import admin_bp,get_ist_now,paying_hrs
from flask.cli import with_appcontext
from flask_cors import CORS
from sqlalchemy.engine import Engine
from sqlalchemy import event

#-------------------this function for enabling foreign key constraints support------------------------------------------------------------------------>
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
#----------------------Sqlalchemy documentation -> ForeignKey Support -------------------------------------------------------------------------------->

app = Flask(__name__)
CORS(app)

#register app here 
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.jinja_env.auto_reload = True
#-----------------------configure database------------------------------------------------>
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking_app.db"
app.config['SECRET_KEY']="development"
db.init_app(app)


with app.app_context():
   db.create_all()
   if not admin_session:
       super_admin=Admin(  Full_Name="Admin",
                          email="admin@gmail.com",
                             password="a123")
       db.session.add(super_admin)
       session['admin_id']="admin@gmail.com"
       db.session.commit()
#--------------------routes-------------------------------------------------------------------------------------------------------------------->
# api html routes :
#                    url               | page             |     html
#                    '/'               =login page->          login.html
#            '/register'               =register page->       register.html
#               '/home'                = user home page ->    home.html  
#               '/admin'               = admin home page ->   admin_home.html
#   '/admin/form_add_lot'              = add lot form page->  add_lot_form.html (session needed:sn) 
#   '/admin/edit_lot/<int:lot_id>      = edit lot form page -> edit_lot_form.html (sn)
#------------------------------------------------------------------------------------------------------------------------------------------------>

@app.route('/')
def landing_page():
    return render_template('landing_page.html')

@app.route('/login')  
def login():
   return render_template('login.html')  
 
@app.route('/register')
def register():
   return render_template('register.html')

@app.context_processor
def userdata():
      try: 
         user_id = user_session().id
         user_data=User.query.filter_by(id=user_id).first()
         return dict(user_data=user_data)
      except:
         return dict(user_data=None)

@app.route('/home')
def home():
   user_id=user_session().id
   history=Reserve_parking_spot.query.filter_by(user_id=str(user_id)).all()
   user_data=User.query.filter_by(id=user_id).first()
   user_loc_lots=Parking_lot.query.filter_by(Pincode=user_data.Pincode).all()
   print(user_data.Full_Name)
   result=[]
   for lot in user_loc_lots:
        available_spots= db.session.execute(
                   text('SELECT COUNT(id) AS available_spots FROM parking_spots WHERE lot_id=:lot_id AND status="A"'),
                   {"lot_id": lot.id}
                    ).scalar()
        result.append({
            "id":lot.id,
            "Address":lot.Address,
            "Available_spots":available_spots,
            "price":lot.price_per_hour_of_spot,
        })
   return render_template('home.html',reserves=history,get_ist_now=get_ist_now,paying_hrs=paying_hrs,user_data=user_data,lots=result)
