import os
import json
import requests
import pymysql

# Database connection
def get_database_connection():
    connection = pymysql.connect(
        host="us-cdbr-east-06.cleardb.net",
        user="b005c8a97ae61d",
        password="04eca8ce",
        db="heroku_3442ee38bf9fb24"
    )
    return connection

# Fetch all tokens from the database
def get_all_device_tokens():
    connection = get_database_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    query = "SELECT token FROM fcm_tokens"
    cursor.execute(query)
    tokens = cursor.fetchall()
    cursor.close()
    connection.close()
    return [token["token"] for token in tokens]

# Send FCM push notification
def send_fcm_push_notification(tokens, title, body):
    api_key = "edf04d625d90c15be31e42579bff217780cd8b1c"
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key={}".format(api_key)
    }

    payload = {
        "registration_ids": tokens,
        "notification": {
            "title": title,
            "body": body
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

# Main function to send push notifications
def send_push_notifications(title, body):
    tokens = get_all_device_tokens()
    if not tokens:
        print("No device tokens found")
        return

    response = send_fcm_push_notification(tokens, title, body)
    print("FCM push notification response:", response)

if __name__ == "__main__":
    title = "Test Notification"
    body = "This is a test notification from FCM."
    send_push_notifications(title, body)