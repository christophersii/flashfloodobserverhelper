import os
import sys
import subprocess
from datetime import datetime, timedelta

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import mysql.connector
except ImportError:
    install("mysql-connector-python")
    import mysql.connector


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
except ImportError:
    install("requests")
    import requests
    
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pymysql
except ImportError:
    install("pymysql")
    import pymysql
    
from fcm_push_notification import send_push_notifications
import time

db_credentials = {
    'user': 'b005c8a97ae61d',
    'password': '04eca8ce',
    'host': 'us-cdbr-east-06.cleardb.net',
    'database': 'heroku_3442ee38bf9fb24'
}

last_processed_time = None

def get_water_level_data():
    global last_processed_time
    
    conn = mysql.connector.connect(**db_credentials)
    cursor = conn.cursor()

    query = """SELECT sr.device_id, s.drainage_depth - sr.water_level AS drainage_water_level, s.station_name, s.threshold_alert, s.threshold_warning, s.threshold_danger, s.drainage_depth, sd.admin_id, sr.reading_time
               FROM sensor_reading sr
               JOIN sensor_device sd ON sr.device_id = sd.device_id
               JOIN station s ON sd.station_code = s.station_code
               WHERE sr.reading_time = (SELECT MAX(reading_time) FROM sensor_reading WHERE device_id = sr.device_id)"""

    if last_processed_time is not None:
        query += f" AND sr.reading_time > '{last_processed_time}'"
    
    cursor.execute(query)
    water_level_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return water_level_data

def insert_admin_notification(admin_id, notify_info, device_id):
    conn = mysql.connector.connect(**db_credentials)
    cursor = conn.cursor()

    query = """INSERT INTO adminnotification (admin_id, notify_info, device_id)
               VALUES (%s, %s, %s)"""
    cursor.execute(query, (admin_id, notify_info, device_id))

    conn.commit()
    cursor.close()
    conn.close()

def process_water_level_data():
    global last_processed_time
    
    water_level_data = get_water_level_data()

    for device_id, drainage_water_level, station_name, threshold_alert, threshold_warning, threshold_danger, drainage_depth, admin_id, reading_time in water_level_data:
        last_processed_time = reading_time
        reading_time += timedelta(hours=8)
        device_id = device_id
        drainage_water_level = int(drainage_water_level)
        threshold_alert = int(threshold_alert)
        threshold_warning = int(threshold_warning)
        threshold_danger = int(threshold_danger)
        drainage_depth = int(drainage_depth)

        if drainage_water_level >= threshold_danger:
            title = "Water level reached threshold"
            body = f"Level      : Danger\nWater level: {drainage_water_level}mm/{drainage_depth}mm\nStation    :{station_name}\nDevice ID  : {device_id}"
            send_push_notifications(title, body)
            insert_admin_notification(admin_id, body, device_id)
        elif drainage_water_level >= threshold_warning:
            title = "Warning: Water level reached threshold"
            body = f"Warning water level: {drainage_water_level}mm/{drainage_depth}mm at station {station_name}."
            send_push_notifications(title, body)
            insert_admin_notification(admin_id, body, device_id)
        elif drainage_water_level >= threshold_alert:
            title = "Alert: Water level reached threshold"
            body = f"Alert water level: {drainage_water_level}mm/{drainage_depth}mm at station {station_name}."
            send_push_notifications(title, body)
            insert_admin_notification(admin_id, body, device_id)

if __name__ == "__main__":
     while True:
        process_water_level_data()
        time.sleep(30)  # Run every 1 minute
