import os
import sys
import subprocess
from datetime import datetime, timedelta
import json

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import mysql.connector
except ImportError:
    install("mysql-connector-python")
    import mysql.connector

try:
    import requests
except ImportError:
    install("requests")
    import requests

try:
    import pymysql
except ImportError:
    install("pymysql")
    import pymysql
    
try:
    import nexmo
except ImportError:
    install("nexmo")
    import nexmo

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

    cursor.execute("SET time_zone = '+08:00'")

    query = """SELECT sr.device_id, s.drainage_depth - (sr.water_level - 30) AS drainage_water_level, s.station_name, 
               s.threshold_alert, s.threshold_warning, s.threshold_danger, s.drainage_depth, 
               sd.admin_id, sr.reading_time, a.admin_phone
               FROM sensor_reading sr
               JOIN sensor_device sd ON sr.device_id = sd.device_id
               JOIN station s ON sd.station_code = s.station_code
               JOIN admin a ON sd.admin_id = a.admin_id
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
    cursor.execute(query, (admin_id, json.dumps(notify_info), device_id))

    conn.commit()
    cursor.close()
    conn.close()

def send_sms(admin_phone, message):
    client = nexmo.Client(key='6ef9f7e8', secret='V5eErgcm5D72mt0U')
    response = client.send_message({
        'from': 'FFObserver',
        'to': '60' + str(admin_phone),
        'text': message,
    })

    if response["messages"][0]["status"] != "0":
        print(f"Message failed with error: {response['messages'][0]['error-text']}")
    
def process_water_level_data():
    global last_processed_time

    water_level_data = get_water_level_data()

    for device_id, drainage_water_level, station_name, threshold_alert, threshold_warning, threshold_danger, drainage_depth, admin_id, reading_time, admin_phone in water_level_data:
        last_processed_time = reading_time
        device_id = device_id
        drainage_water_level = int(drainage_water_level)
        threshold_alert = int(threshold_alert)
        threshold_warning = int(threshold_warning)
        threshold_danger = int(threshold_danger)
        drainage_depth = int(drainage_depth)
        
        print(f"Admin phone number: {admin_phone}")
        print(f"Admin phone number in database: {admin_phone}")
        admin_phone_str = str(admin_phone)
        print(f"Admin phone number after conversion to string: 60{admin_phone_str}")

        if drainage_water_level >= threshold_danger:
            title = "PLEASE TAKE IMMEDIATE ACTION"
            body = f"Level: Danger\nWater level : {drainage_water_level}/{drainage_depth}mm\nStation: {station_name}\nDevice ID: {device_id}\nTime: {reading_time}"
            send_push_notifications(admin_id, title, body)
            send_sms(admin_phone, body)
            notification_data = {
                'level_title': 'PLEASE TAKE IMMEDIATE ACTION',
                'level': 'Danger',
                'reading_time': reading_time.strftime('%Y-%m-%d %H:%M:%S'),
                'station_name': station_name,
                'device_id': device_id,
                'drainage_water_level': drainage_water_level,
                'drainage_depth': drainage_depth
            }
            insert_admin_notification(admin_id, notification_data, device_id)
        elif drainage_water_level >= threshold_warning:
            title = "PLEASE BE PREPARED"
            body = f"Level: Warning\nWater level: {drainage_water_level}/{drainage_depth}mm\nStation: {station_name}\nDevice ID: {device_id}\nTime: {reading_time}"
            send_push_notifications(admin_id, title, body)
            send_sms(admin_phone, body)
            notification_data = {
                'level_title': 'PLEASE BE PREPARED',
                'level': 'Warning',
                'reading_time': reading_time.strftime('%Y-%m-%d %H:%M:%S'),
                'station_name': station_name,
                'device_id': device_id,
                'drainage_water_level': drainage_water_level,
                'drainage_depth': drainage_depth
            }
            insert_admin_notification(admin_id, notification_data, device_id)
        elif drainage_water_level >= threshold_alert:
            title = "PLEASE STAY ALERT"
            body = f"Level: Alert\nWater level: {drainage_water_level}/{drainage_depth}mm\nStation: {station_name}\nDevice ID: {device_id}\nTime: {reading_time}"
            send_push_notifications(admin_id, title, body)
            send_sms(admin_phone, body)
            notification_data = {
                'level_title': 'PLEASE STAY ALERT',
                'level': 'Alert',
                'reading_time': reading_time.strftime('%Y-%m-%d %H:%M:%S'),
                'station_name': station_name,
                'device_id': device_id,
                'drainage_water_level': drainage_water_level,
                'drainage_depth': drainage_depth
            }
            insert_admin_notification(admin_id, notification_data, device_id)

if __name__ == "__main__":
    while True:
        try:
            process_water_level_data()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(30)
