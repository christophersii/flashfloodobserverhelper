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
    cursor = connection.cursor()
    cursor.execute("SET time_zone = '+08:00'")
    cursor.close()
    return connection

# Fetch all tokens from the database
def get_fcm_tokens_for_admin(admin_id):
    connection = get_database_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    query = "SELECT token FROM fcm_tokens WHERE admin_id = %s"
    cursor.execute(query, (admin_id,))
    tokens = cursor.fetchall()
    cursor.close()
    connection.close()
    return [token["token"] for token in tokens]

# Remove token from the database
def remove_token(token):
    # Your PHP script URL
    url = "http://flashfloodobserver.herokuapp.com/remove_token.php"
    data = {
        'tokens': [token]
    }

    # Send the POST request.
    response = requests.post(url, data=data)

    # Print the response from your PHP script.
    print(response.text)

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
            response_json = response.json()
            if 'failure' in response_json and response_json['failure'] > 0:
                for result_index, result_item in enumerate(response_json['results']):
                    if 'error' in result_item and result_item['error'] == 'NotRegistered':
                        remove_token(tokens[result_index])
            return response_json
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None
    else:
        print("Empty response from FCM server")
        return None

# Main function to send push notifications
def send_push_notifications(admin_id, title, body):
    tokens = get_fcm_tokens_for_admin(admin_id)
    if not tokens:
        print("No device tokens found")
        return

    response = send_fcm_push_notification(tokens, title, body)
    if response:
        print("FCM push notification response:", response)
    else:
        print("Failed to send FCM push notification")

if __name__ == "__main__":
    title = "Test Notification"
    body = "This is a test notification from FCM."
    send_push_notifications(admin_id, title, body)
