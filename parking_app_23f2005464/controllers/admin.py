from flask import Blueprint, request,redirect,url_for,flash,render_template,session,make_response
from models.model import * 
from sqlalchemy import text,or_,func
from datetime import datetime,timezone,timedelta

# addlot_bp=Blueprint("add_lot",__name__,url_prefix='/admin')
admin_bp=Blueprint("admin",__name__,url_prefix='/admin')

def admin_session():
    admin_email = session.get("admin_id")
    if not admin_email:
        return None
    return Admin.query.filter_by(email=admin_email).first()


def user_session():
    user_email=session.get('user_id')
    if not user_email:
        return None
    return User.query.filter_by(email=user_email).first()


def paying_hrs(hrs):
    paying_hrs=0
    if hrs < 1:
        paying_hrs = 1
    elif hrs == int(hrs):
       paying_hrs = int(hrs)
    else:
        paying_hrs = int(hrs) + 1  #for 1.56  int(1.56) = 1 something
    return paying_hrs    
   
def hr_calc(current_time,parking_time):
    hr=(current_time-parking_time.replace(tzinfo=timezone.utc)).total_seconds()/3600
    nearest_int=paying_hrs(hr)
    return nearest_int
       
def get_ist_now(time):
    parking_t= time + timedelta(hours=5, minutes=30)
    return parking_t.replace(tzinfo=None).replace(microsecond=0)

@admin_bp.route('view_profile',methods=['GET'])
def user_profile():
    print("log ::admin profile view automatically")
    data=admin_session() #automatically get user_id from session
    print(data.email)
    print("log :: admin user_profile completed ")
    return render_template('edit_admin_profile.html',admin=data)

  
@admin_bp.route('user_edit/<int:admin_id>',methods=['POST'])
def user_edit(admin_id):
     print("log ::  admin edit requested")
     print(f"form data request {request.form.get('Name')} ,email: {request.form.get('email')} ")  
   
     db.session.execute(text('''UPDATE admins SET Full_Name=:Name,
                                                    email=:email '''),
                                           {

                                               "Name":request.form.get('Name'),
                                               "email":request.form.get('email'),
                                           }                        
                                           
                                            )
     db.session.commit()
     
                 
     return render_template('success.html',message="Profile updated successfully",redirect_url=url_for("login"))

 
 
@admin_bp.route('/form_add_lot',methods=['GET'])
def form_add_lot():
    print("log :: add lot form loaded")
    return render_template("add_lot_form.html")


@admin_bp.route('admin/addlot_formdata',methods=['POST'])
def add_lot():
    print("log :: add lot intialized 78 line")
    admin=admin_session()
    if not  admin or not admin.id :
            print("unauth access")
            return "Unautorized Access"
    if admin.id:
        data=request.form
        prime_location=data['prime_location']
        Address=data['Address']
        Pincode=data['Pincode']
        Max_no_of_spots=data['max_spots']
        price_per_hour_of_spot=data['Price_per_hr']
        admin_id=admin.id
        
        print(f"logging{admin_id},{prime_location},{Address},{Pincode},{Max_no_of_spots},{price_per_hour_of_spot}")
        
        new_lot=Parking_lot(prime_location=prime_location,Address=Address,Pincode=Pincode,Max_no_of_spots=Max_no_of_spots,price_per_hour_of_spot=price_per_hour_of_spot,admin_id=admin_id)
        db.session.add(new_lot)
        db.session.flush()
        lot_id = new_lot.id
        #automatic spot intially A (unocuppied)
        for i in range(0,int(Max_no_of_spots)):
             db.session.add(Parking_spot(status="A",lot_id=lot_id))
       
        db.session.commit()
        print("completed")
        return render_template('success.html',message="Parking lot successfully Add",redirect_url=url_for('admin.query'))
    else :
         return "Unauthorized", 401
     
#admin home rendering and card updating route     
@admin_bp.route('/',methods=['GET'])     
def query():
        print("log :: query intialized ")
        admin=admin_session()
        if not  admin or not admin.id  :
            return render_template('error.html',message='Unauthorized access',redirect_url=url_for('login'))
        sql_query="""
                     SELECT 
                              l.id AS lot_id, 
                              l.prime_location, 
                              l.Max_no_of_spots,
                              l.price_per_hour_of_spot,
                              l.Pincode,
                     COUNT(CASE WHEN s.status = 'A' THEN 1 END) AS available_spots,
                     COUNT(CASE WHEN s.status = 'O' THEN 1 END) AS occupied_spots
                     FROM parking_lots l
                     LEFT JOIN parking_spots s ON l.id = s.lot_id
                     WHERE l.admin_id = :admin_id  
                     GROUP BY l.id, l.prime_location, l.Max_no_of_spots, l.price_per_hour_of_spot,l.Pincode 

        """
        result = db.session.execute(text(sql_query), {"admin_id": admin.id})
        rows = result.fetchall() # or .fetchone() or .scalars()
        lots_with_spots=[]
        #row[0]=lot_id,row[1]=name of lot ,row[2]=max_spots ,row[3]=price/hr ,row[4]=Pincode, row[5]=available spots,
        for row in rows:

                lots_with_spots.append({
                    "lot_id":row[0],  
                    "prime_location":row[1],
                    "Max_no_of_spots":row[2],
                    "Available_spots":row[5],
                    "price_per_hr":row[3],
                    "Occupied_spots":row[6],
                    "Pincode":row[4]
                })          
        print("log:: completed")          
        return  render_template("admin_home.html", lots=lots_with_spots)
    
    
#----------------------------------------------editing lot info---------------------
@admin_bp.route('/edit_lot/<int:lot_id>',methods=['POST','GET'])    
def edit_lot(lot_id):
    print("log :: edit lot intialized")
    if request.method=='POST':
        existing_count = db.session.execute(text("SELECT COUNT(*) FROM parking_spots WHERE lot_id = :lot_id AND status IN ('A', 'O')"), {"lot_id": lot_id}).scalar()
        new_count=int(request.form.get('max_spots'))
        
        
        if new_count > existing_count:
         for i in range(existing_count, new_count):
            db.session.add(Parking_spot(status="A", lot_id=lot_id))
        
        elif new_count < existing_count:
    # Marking excess spots as inactive
             db.session.execute(text(  """                        
                     UPDATE parking_spots 
                     SET status = 'I' 
                     WHERE id IN (
                     SELECT id FROM parking_spots 
                     WHERE lot_id = :lot_id AND status = 'A'
                    LIMIT :limit
                    )
                    """),
                    {"lot_id": lot_id, "limit": existing_count - new_count})
        
        
        
        db.session.execute(text('''UPDATE parking_lots SET prime_location=:prime_location, 
                                                           Max_no_of_spots=:Max_no_of_spots,
                                                           Address=:Address,
                                                           Pincode=:Pincode,
                                                           price_per_hour_of_spot=:price_per_hr 
                                                           where id=:lot_id'''),
                                                         {
                                                           "lot_id":lot_id,
                                                            "prime_location":request.form.get('prime_location'),
                                                            "Address":request.form.get('Address'),
                                                            "Pincode":request.form.get("Pincode"),
                                                            "price_per_hr":request.form.get('Price_per_hr'),
                                                            "Max_no_of_spots":request.form.get('max_spots'),
                                                          })
        
        db.session.commit()
        print("completed")
        return render_template('success.html',message="Parking lot successfully Add",redirect_url=url_for('admin.query'))

    
    lot=db.session.execute(text('SELECT prime_location,Max_no_of_spots,Address,Pincode,price_per_hour_of_spot from parking_lots where id=:lot_id'),{"lot_id":lot_id}).fetchone()
    if lot :
        data={
            "prime_location":lot.prime_location,
            "Max_no_of_spots":lot.Max_no_of_spots,
            "Address":lot.Address,
            "Pincode":lot.Pincode,
            "price_per_hr":lot.price_per_hour_of_spot,
            "lot_id":lot_id
        }
        print("completed")
        return render_template('edit_lot_form.html',lot=data)

@admin_bp.route('delete_lot/<int:lot_id>')
def delete_lot(lot_id):
        print(lot_id)
        lot = db.session.get(Parking_lot, lot_id)
        if not lot:
            return "Lot not found", 404
        db.session.delete(lot)
        db.session.commit()
        return redirect(url_for('admin.query'))
   
   

    
       
       
       
@admin_bp.route('/occupied_spots/<int:lot_id>',methods=['POST','GET'])
def user_occupied_spots(lot_id):
    current_time= datetime.now(timezone.utc)
    print(f"log :: running admin.user_occupied_spots")
    reservation_data=db.session.query(Reserve_parking_spot,Parking_spot,User,Parking_lot).join(Parking_spot,Reserve_parking_spot.spot_id==Parking_spot.id).join(User, Reserve_parking_spot.user_id == User.id).join(Parking_lot,Parking_lot.id==Parking_spot.lot_id).filter(Parking_spot.lot_id==lot_id).filter(Parking_spot.status=='O').all()
    
    temp=[{"spot_id": res.spot_id, "lot_id": spot.lot_id,"user_id":res.user_id,"vehicle_no":res.vehicle_number,"parking_timestamp":get_ist_now(res.parking_timestamp.replace(tzinfo=timezone.utc)),"status":spot.status,"email":user.email,"estimate_pay":(hr_calc(current_time,res.parking_timestamp))*int(lot.price_per_hour_of_spot),"duration":hr_calc(current_time,res.parking_timestamp.replace(tzinfo=timezone.utc))}for res,spot,user,lot in reservation_data]

    if temp==[]:
        return render_template('admin_spot_data.html')
   
    return render_template('admin_spot_data.html',users=temp,lot_id=lot_id) 


@admin_bp.route('/summary/dashboard',methods=['POST','GET'])
def summary():
    print(f"log :: summary function intialized")
    admin_id=admin_session().id
    active_data = db.session.execute(text("""
        SELECT l.prime_location, COUNT(r.id) AS total_reservations
        FROM parking_lots l
        JOIN parking_spots s ON s.lot_id = l.id
        JOIN reserve_parking_spot r ON r.spot_id = s.id                                 
        WHERE l.admin_id =:admin_id AND s.status='O' AND r.end_parking_timestamp is NULL
        GROUP BY l.id, l.prime_location
        ORDER BY total_reservations DESC
    """), {"admin_id": admin_id}).fetchall()

    best_perform_lot = max(active_data,key=lambda i :i[1])
    occupied_spots=0
    available_spots=db.session.execute(text(""" Select Count(p.id)  from parking_spots p WHERE p.status='A' """)).first()
    for i in active_data:
       occupied_spots+=i[1]


    #profits
    lot_profits = (
        db.session.query(
            Parking_lot.prime_location,
            func.coalesce(func.sum(Reserve_parking_spot.Total_amount_user_paid), 0).label("total_profit")
        )
        .join(Parking_spot, Parking_spot.lot_id == Parking_lot.id)
        .join(Reserve_parking_spot, Reserve_parking_spot.spot_id == Parking_spot.id, isouter=True)
        .filter(Parking_lot.admin_id == admin_id)
        .group_by( Parking_lot.prime_location)
        .order_by(func.sum(Reserve_parking_spot.Total_amount_user_paid).desc())
        .all()
    )    

    data={"occupied_spots":occupied_spots,
     "available_spots":available_spots[0],
     "best_perform_lot_name":best_perform_lot[0],
     "best_perform_lot_users":best_perform_lot[1],
     "profits": [{"prime_location":i.prime_location,"profits_total":i.total_profit} for i in lot_profits]
     }
    print(f"log :: summary function completed")
    return render_template("admin_summary.html",data=data )




def check_type(keyword):
    print("checktype func 266 line")
    try:
         int_value = int(keyword)
         print(f"Integer input: {int_value}")
         return int_value
    except ValueError:
    # It is a non-integer string
        print(f"String input: {keyword}")
        return keyword

@admin_bp.route('/search',methods=['GET','POST'])
def search():
   print("log :: search function intialized")
   if request.method=='GET':
     return  render_template('admin_search.html')
   if request.method=='POST':
       keyword=request.form['keyword']
       category=request.form['category']
       temp=check_type(keyword)

       if category=="parking_lot":
           if isinstance(temp,int):
                
                #  data=Parking_lot.query.filter(Parking_lot.id==temp).all()
                data=db.session.query(Parking_lot,func.count(Parking_spot.id).label('available_spots')).join(Parking_spot,Parking_spot.lot_id==Parking_lot.id).filter(Parking_lot.id==temp).all()
              
                if  data[0][0] != None  :
                    return   render_template("admin_search.html",data=data)
                else :
                    return render_template("error.html",message="This lot not exist",redirect_url=url_for('admin.search') )
           else:
               data=db.session.query(Parking_lot,func.count(Parking_spot.id).label('available_spots')).join(Parking_spot,Parking_spot.lot_id==Parking_lot.id).filter(or_(Parking_lot.Address.ilike(f"%{temp}%"),Parking_lot.prime_location.ilike(f"%{temp}%"),Parking_lot.Pincode.ilike(f"%{temp}%")),Parking_spot.status=="A").group_by(Parking_lot.id).all() 
               print("search func completed")
               if data == []:
                    print("search 2 func completed")
                    return  render_template("error.html",message="Not found keyword or Invalid Input!",redirect_url=url_for('admin.search') )
               else :
                     return render_template("admin_search.html",data=data)


            




     #not showing the new user field
     
       if category=="user" :
            #    data=User.query.filter(or_(User.user_id.ilike(f"%{temp}%"),User.Full_Name.ilike(f"%{temp}%"),User.email.ilike((f"%{temp}%")))).all()
              if isinstance(temp,int):
                              data=db.session.query(User, Reserve_parking_spot, Parking_spot).join( Reserve_parking_spot, User.id == Reserve_parking_spot.user_id).join(Parking_spot, Reserve_parking_spot.spot_id == Parking_spot.id).filter(User.id==temp).all()
                              return render_template("admin_search.html",data2=data)  
              else:   
                 data=db.session.query(User, Reserve_parking_spot, Parking_spot).join( Reserve_parking_spot, User.id == Reserve_parking_spot.user_id).join(Parking_spot, Reserve_parking_spot.spot_id == Parking_spot.id).filter(or_(User.email.ilike(f"%{temp}%"),User.Full_Name.ilike(f"%{temp}%"),User.Address.ilike(f"%{temp}%"),User.Pincode.ilike(f"%{temp}%"),Reserve_parking_spot.vehicle_number.ilike(f"%{temp}%"))).all()
                 if data == []:
                    print("search 2 func completed")
                    return  render_template("error.html",message="Not found keyword or Invalid Input!",redirect_url=url_for('admin.search') )
                 else :
                     return render_template("admin_search.html",data2=data)


 
@admin_bp.route("spotdata/<int:lot_id>",methods=["GET","POST"])
def spot_management(lot_id):
    print("log :: spot_management intialized")
    query1=Parking_spot.query.filter(Parking_spot.lot_id==lot_id,Parking_spot.status=="A").all()
    print("complete")
    return render_template("spot_data.html",data=query1)  

@admin_bp.route("spot_delete/<int:spot_id>",methods=['GET','POST'])
def delete_spot(spot_id):
    print("log :: delete_spot intialized")
    spot=Parking_spot.query.get(spot_id)
    lot_id=spot.lot_id
    if spot:
        spot.status='I'
        db.session.commit()
    print("complete")
    return render_template("success.html",redirect_url=url_for('admin.spot_management',lot_id=lot_id))    


@admin_bp.route('/download_report')
def download_report():
    pass