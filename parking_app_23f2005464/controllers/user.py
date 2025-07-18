from flask import Blueprint,request,render_template,flash,redirect,url_for
from sqlalchemy import text
from models.model import * 
from controllers.admin import user_session,paying_hrs,get_ist_now,hr_calc
from datetime import datetime,timezone
user_bp=Blueprint('user',__name__,url_prefix="/user")




@user_bp.route("/search_lots",methods=['POST','GET'])
def search_lots():
    pincode=request.form.get('pincode')
    user_id=user_session()
    print(pincode)
    lots=Parking_lot.query.filter_by(Pincode=pincode).all() 
    if not lots:
        return render_template('error.html',message="parking lot not found in your area",redirect_url=url_for('home'))
    
    result=[]
    
    # available_spots=
    for lot in lots:
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

    history=Reserve_parking_spot.query.filter_by(user_id=str(user_id.id)).all()    
    return render_template("home.html", lots=result, searched_pincode=pincode,user_id=user_id,reserves=history,get_ist_now=get_ist_now,paying_hrs=paying_hrs,Searched_flag=True)   


@user_bp.route('users_data',methods=['GET'])
def users_data():
   users_data=db.session.execute(text("Select * from users"))
   print(users_data)
   users=[]
   for user in users_data:
       users.append({
           "user_id":user.id,
           "email":user.email,
           "Name":user.Full_Name,
           "Address":user.Address,
           "Pincode":user.Pincode,
       })
   return render_template('users_data.html',users=users)

#------------------------------------------------------------View profile------------------------------------------------------->
@user_bp.route('view_profile',methods=['GET'])
def user_profile():
    print("log :: profile view automatically")
    data=user_session()#automatically get user_id from session
    print(data.email)
    print(data.id)
    return render_template('edit_profile_user.html',user=data)
   
@user_bp.route('user_edit/<int:user_id>',methods=['POST'])
def user_edit(user_id):
     print("log ::  edit requested")
     print(f"form data request {request.form.get('Name')} ,Address: {request.form.get('Address')} , Pincode : {request.form.get('Pincode')}")  
   
     db.session.execute(text('''UPDATE users SET Full_Name=:Name,
                                                 Address=:Address ,
                                                 Pincode=:Pincode 
                             where email=:email '''),
                                           {

                                               "Name":request.form.get('Name'),
                                               "Address":request.form.get('Address'),
                                               "Pincode":request.form.get('Pincode'),
                                               "email":request.form.get('email')
                                           }                        
                                           
                                            )
     db.session.commit()
     
     return render_template('success.html',message="Profile updated successfully",redirect_url=url_for('user.user_profile'))
 
# reservation logic
@user_bp.route('/booking/<int:lot_id>')
def booking_spot_form(lot_id):
    id_allocationing=db.session.execute(text(''' Select id from parking_spots where lot_id=:lot_id and status=:status LIMIT 1 '''),{"lot_id":lot_id,"status":'A'}).fetchone()
    if id_allocationing is None:
        return render_template('error.html',message='Spot is Not Available!',redirect_url=url_for('home'))
   
    return render_template('booking_form.html',lot_id=lot_id,user_id=user_session().id, spot_id=id_allocationing[0])


@user_bp.route('/booking/<string:user_id>/<string:spot_id>',methods=['POST'])
def reserving(user_id,spot_id):
    db.session.execute(text(''' UPDATE parking_spots SET status='O' WHERE id=:spot_id '''),{"spot_id":spot_id})
    
    # spot status not required to check bcoz booking spot func logic already give only A spots
    
    #for confirmation lets check if user already reserved? bcoz if user hinder the load or alter url
    exist_reservation=Reserve_parking_spot.query.filter_by(user_id=user_id,spot_id=spot_id).filter(Reserve_parking_spot.end_parking_timestamp.is_(None)).first()
    if exist_reservation:
        return render_template('error.html',message='Spot Already reserved by you',redirect_url=url_for('home'))
    
    
    db.session.execute(text(''' INSERT INTO reserve_parking_spot (user_id,spot_id,parking_timestamp,Total_amount_user_paid,vehicle_number,end_parking_timestamp)
                                VALUES (:user_id,:spot_id,CURRENT_TIMESTAMP,:total_amt,:vehicle_no,:end_parking_stamp)'''),{"spot_id":spot_id,"user_id":user_id,"vehicle_no":request.form['vehicle_no'],"total_amt":0,"end_parking_stamp":None})
    db.session.commit()
    
    return render_template("success.html",message="Booked spot successfully",redirect_url=url_for('home'))

@user_bp.route('/history/release/<string:spot_id>',methods=['GET','POST'])
def release_and_payment(spot_id):
  
    if request.method=='GET':
        current_timestamp = datetime.now(timezone.utc)  #utc=coordinated universal time
        Data=db.session.query(Reserve_parking_spot,Parking_lot,Parking_spot).join(Parking_spot,Reserve_parking_spot.spot_id==Parking_spot.id).join(Parking_lot,Parking_spot.lot_id==Parking_lot.id).filter(Reserve_parking_spot.spot_id==spot_id).filter(Reserve_parking_spot.end_parking_timestamp==None).first()
        reserve,lot,spot=Data
        print(reserve.parking_timestamp.replace(tzinfo=timezone.utc))
        parking_timestamp=reserve.parking_timestamp
        userdata=User.query.filter_by(id=user_session().id).first()
        name=userdata.Full_Name
        email=userdata.email
        duration=hr_calc(current_timestamp,parking_timestamp)
        total_amt=int(duration)*int(lot.price_per_hour_of_spot)
        print(f"log:: func release_add_payment , {name} parked for duration {duration} has total amount {total_amt}***********")
        return render_template('payment.html',name=name,email=email,parking_timestamp=parking_timestamp,current_timestamp=current_timestamp,duration=duration,spot_id=spot_id,get_ist_now=get_ist_now,total_amt=float(total_amt))
   
   
   
   
    if request.method=='POST':
            current_timestamp=request.form['utc_now']
            total_amt=request.form['total_amt']
            hrs=request.form['hrs']
            db.session.execute(text('''
                    UPDATE reserve_parking_spot
                    SET end_parking_timestamp = :current_timestamp , duration =:hrs,Total_amount_user_paid=:Total_amt
                    WHERE user_id = :user_id AND spot_id = :spot_id AND end_parking_timestamp IS NULL
                '''), {
                    "user_id": user_session().id,
                    "spot_id": spot_id,
                    "current_timestamp":current_timestamp,
                    "hrs":hrs,
                    "Total_amt":total_amt
                })
                    
            
            db.session.execute(text('''UPDATE parking_spots SET status='A' WHERE id=:spot_id'''),{"spot_id":spot_id})
            db.session.commit()
            return render_template('success.html',message=f"Successfully Paid Amount {total_amt} ",redirect_url=url_for('home'))

@user_bp.route('/user_summary', methods=['GET', 'POST'])
def user_summary():
    print("log :: user summary initialized")
    user_id = user_session().id
    #this below query will do filter with join reserveparking spot ,parking spot and parking lot filter by userid and active users 
    query = db.session.query(Reserve_parking_spot, Parking_spot, Parking_lot
    ).join(Parking_spot, Reserve_parking_spot.spot_id == Parking_spot.id
    ).join(Parking_lot, Parking_spot.lot_id == Parking_lot.id
    ).filter(
        Reserve_parking_spot.user_id == user_id,
        Reserve_parking_spot.end_parking_timestamp == None
    ).all()

    current_timestamp = datetime.now(timezone.utc)
    durations = []
    counts_loc = {}

    aggregated_durations = {}
    #data processing for list of dic 
    for res, ps, pl in query:
        parking_timestamp = res.parking_timestamp
        duration = hr_calc(current_time=current_timestamp, parking_time=parking_timestamp)

        counts_loc[pl.prime_location] = counts_loc.get(pl.prime_location, 0) + 1

        if pl.prime_location not in aggregated_durations:
            aggregated_durations[pl.prime_location] = {
                "total_duration": duration,
                "spots": [{"spot_id": ps.id ,"duration":duration}]
            }
        else:
            aggregated_durations[pl.prime_location]["total_duration"] += duration
            aggregated_durations[pl.prime_location]["spots"].append(
                {"spot_id": ps.id,"duration":duration}
            )
    for loc,values in aggregated_durations.items():
        durations.append({
        "prime_location": loc,
        "total_duration": values["total_duration"],
        "spots": values["spots"]
    })
    
    print("completed")
    return render_template('user_summary.html', data=durations, count_loc=counts_loc)

