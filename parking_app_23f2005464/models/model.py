from sqlalchemy import Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,relationship
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):#mapped_column func from flask_sqlalchemy
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]= mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    Full_Name: Mapped[str] = mapped_column(String(120), nullable=False)
    Address: Mapped[str] = mapped_column(String(150), nullable=False)
    Pincode: Mapped[str] = mapped_column(String(7), nullable=False)
    reserve_parking_spots = relationship('Reserve_parking_spot', backref='user',lazy='dynamic')  # One-to-many relationship with Reserve_parking_spot
   
class Admin(db.Model):
    __tablename__ = 'admins'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    Full_Name: Mapped[str] = mapped_column(String(120), nullable=False)
    parking_lots=relationship('Parking_lot', backref='admin')  # One-to-many relationship with Parking_lot
    
class Parking_lot(db.Model):
    __tablename__ = 'parking_lots'
    id: Mapped[int] = mapped_column(primary_key=True)
    prime_location: Mapped[str] = mapped_column(String(120), nullable=False)
    Address: Mapped[str] = mapped_column(String(150), nullable=False)
    Pincode: Mapped[str] = mapped_column(String(7), nullable=False)
    Max_no_of_spots: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_hour_of_spot: Mapped[int] = mapped_column(Integer, nullable=False)
    admin_id: Mapped[int] = mapped_column(Integer,ForeignKey('admins.id') ,nullable=False,)  #FK
    parking_spots = relationship('Parking_spot', backref='parking_lot', lazy='dynamic',cascade="all, delete-orphan", passive_deletes=True)  # One-to-many relationship with Parking_spot
    
class Parking_spot(db.Model):
    __tablename__ = 'parking_spots'
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(1), nullable=False) 
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey('parking_lots.id',ondelete='CASCADE') ,nullable=False)
    reservations = relationship('Reserve_parking_spot', backref='parking_spot',cascade='all,delete-orphan',passive_deletes=True)
    
class Reserve_parking_spot(db.Model):
    __tablename__='reserve_parking_spot'
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id',ondelete='CASCADE'), nullable=False) #FK
    spot_id: Mapped[int] = mapped_column(Integer,  ForeignKey('parking_spots.id', ondelete='CASCADE'),nullable=False) #FK
    parking_timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)   # Timestamp of start of parking
    end_parking_timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=True)  # Timestamp of end of parking it cannot be null because then the user will reserve spot and remove instantly
    duration: Mapped[int] = mapped_column(Integer,nullable=True)  # Duration in hours
    Total_amount_user_paid: Mapped[int] = mapped_column(Integer,nullable=False,default=0)# Total amount paid by user for parking
    vehicle_number: Mapped[str] = mapped_column(String(15), nullable=False)  # Vehicle number of user
    #----------------all delete cascade is done through above relationship through ORM----------------------------------------------------------