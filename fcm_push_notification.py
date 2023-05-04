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
    api_key = "AAAAsE70k0U:APA91bFnJpSGW95c1LbH958wipDoPnbXIDms6lcTz3fMLh5zP-sm9fkEaKYrMlFdchb2gRrCSi5kI65u_8_DfX-Jz5Y_Pgd1wLJcpiDNYtwZQl8_Zh93oGVa4wmFkZWStM8qmDzMOAEJ"
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
    
    print(f"FCM server response status code: {response.status_code}")
    print(f"FCM server response headers: {response.headers}")

    if response.text:  # Check if the response is not empty
        try:
            return response.json()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None
    else:
        print("Empty response from FCM server")
        return None

# Main function to send push notifications
def send_push_notifications(title, body):
    tokens = get_all_device_tokens()
    if not tokens:
        print("No device tokens found")
        return

    response = send_fcm_push_notification(tokens, title, body)
    if response:
        print("FCM push notification response:", response)
        #handle_fcm_response(response, tokens)
    else:
        print("Failed to send FCM push notification")


#def handle_fcm_response(response, tokens):
#    results = response.get('results', [])
#    tokens_to_remove = []

#    for index, result in enumerate(results):
#        if 'error' in result and result['error'] == 'NotRegistered':
#            tokens_to_remove.append(tokens[index])

#    if tokens_to_remove:
#        remove_tokens_from_database(tokens_to_remove)


#def remove_tokens_from_database(tokens):
#    connection = get_database_connection()
#    cursor = connection.cursor()

#    for token in tokens:
#        query = f"DELETE FROM fcm_tokens WHERE token = %s"
#        cursor.execute(query, token)

#    connection.commit()
#    cursor.close()
#    connection.close()
#    print(f"Removed {len(tokens)} NotRegistered tokens from the database")

if __name__ == "__main__":
    title = "Test Notification"
    body = "This is a test notification from FCM."
    send_push_notifications(title, body)
