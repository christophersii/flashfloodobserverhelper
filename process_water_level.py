import os
import sys
import subprocess

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

def get_water_level_data():
    conn = mysql.connector.connect(**db_credentials)
    cursor = conn.cursor()

    query = """SELECT sr.device_id, s.drainage_depth - sr.water_level AS drainage_water_level, s.station_name, s.threshold_alert, s.threshold_warning, s.threshold_danger, sd.admin_id
               FROM sensor_reading sr
               JOIN sensor_device sd ON sr.device_id = sd.device_id
               JOIN station s ON sd.station_code = s.station_code
               WHERE sr.reading_time = (SELECT MAX(reading_time) FROM sensor_reading WHERE device_id = sr.device_id)"""

    cursor.execute(query)
    water_level_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return water_level_data

def insert_admin_notification(admin_id, notify_info, device_id):
    conn = mysql.connector.connect(**db_credentials)
    cursor = conn.cursor()

    query = """INSERT INTO adminnotification (admin_id, notify_info, noti_time, device_id)
               VALUES (%s, %s, NOW(), %s)"""
    cursor.execute(query, (admin_id, notify_info, device_id))

    conn.commit()
    cursor.close()
    conn.close()

def process_water_level_data():
    water_level_data = get_water_level_data()

    for device_id, drainage_water_level, station_name, threshold_alert, threshold_warning, threshold_danger, admin_id in water_level_data:
        drainage_water_level = float(drainage_water_level)
        threshold_alert = float(threshold_alert)
        threshold_warning = float(threshold_warning)
        threshold_danger = float(threshold_danger)

        if drainage_water_level >= threshold_danger:
            title = "Danger: Water level reached threshold"
            body = f"The water level has reached the danger threshold value at station {station_name}. Please take immediate action."
            send_push_notifications(title, body)
            insert_admin_notification(admin_id, body, device_id)
        elif drainage_water_level >= threshold_warning:
            title = "Warning: Water level reached threshold"
            body = f"The water level has reached the warning threshold value at station {station_name}. Please stay alert."
            send_push_notifications(title, body)
            insert_admin_notification(admin_id, body, device_id)
        elif drainage_water_level >= threshold_alert:
            title = "Alert: Water level reached threshold"
            body = f"The water level has reached the alert threshold value at station {station_name}. Please be cautious."
            send_push_notifications(title, body)
            insert_admin_notification(admin_id, body, device_id)

if __name__ == "__main__":
     while True:
        process_water_level_data()
        time.sleep(60)  # Run every 1 minute
