# This script checks your public IP and notifies you if it changes

#########################################
#
# IMPORTS
#
#########################################

import urllib.request
import sqlite3
import os
import math
import json
from datetime import datetime, timezone

#########################################
#
# FUNCTIONS
#
#########################################


# read_env_vars function
# read environment variables for more advanced features such as remote notifications
def read_env_vars():
    json_file = open('env.json', 'r')
    env_vars = json.load(json_file)
    return env_vars


# check_db_exists function
# Checks if the database for storing IP addresses exists
def check_db_exists():
    local_files_dirs = os.listdir('.')
    if 'ip_addrs.db' in local_files_dirs:
        return True
    else:
        return False


# create_db function
# Creates a sqlite3 database for storing IP the addresses
def create_db():
    # Create DB
    db_con = sqlite3.connect("ip_addrs.db")
    cur = db_con.cursor()
    cur.execute('''CREATE TABLE Stored_IP_Addresses 
                (ip_addr, add_ip_addr_date_time)''')
    db_con.commit()

    # Check if DB and Table exist and try again if db and table not created
    res = cur.execute('''SELECT name 
                        FROM sqlite_master 
                        WHERE name='Stored_IP_Addresses' ''')
    if res.fetchone() is None:
        print("Trouble creating the database, trying again!")
        create_db()

    db_con.close()
    return True


# read_ip_address function
# Attempts to read from text file the last saved public IP address
def read_last_ip_address_from_db():
    db_con = sqlite3.connect("ip_addrs.db")
    cur = db_con.cursor()
    res = cur.execute('''SELECT ip_addr, add_ip_addr_date_time
                        FROM Stored_IP_Addresses
                        ORDER BY add_ip_addr_date_time DESC
                        LIMIT 1
                    ''')
    return res.fetchone()


# http_request_public_ip function
# This makes a request to a remote web server that will return your public IP address
# The response is a pointer for a memory location for an object that type is byte, so it must be decoded
# Function will decode response into a string and remove trailing new line characters
def http_request_public_ip():
    url = 'http://checkip.amazonaws.com/'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            return res.read().decode().removesuffix('\n')
    except Exception as e:
        print(e)
        raise


# get_current_date_time function
# gets the current date and time
def get_current_date_time():
    current_date_time = datetime.now(timezone.utc)
    return current_date_time


# find_time_delta_from_now function
# Function to find how long ago we last checked the public IP address to inform the user
def find_time_delta_from_now(last_date_time_ip_addr_changed):
    time_delta = datetime.now(timezone.utc) - datetime.strptime(last_date_time_ip_addr_changed,
                                                                '%Y-%m-%d %H:%M:%S.%f%z')
    calc_time_delta_hrs = math.floor(time_delta.seconds / 3600)
    calc_time_delta_mins = math.floor((time_delta.seconds % 3600) / 60)
    calc_time_delta_secs = math.ceil(((time_delta.seconds % 3600) % 60))
    return f'''{time_delta.days} days {calc_time_delta_hrs} hours {calc_time_delta_mins} minutes'''\
        f''' and {calc_time_delta_secs} seconds ago'''


# store_ip_address function
# Writes the updated ip address to a text file called my ip
def store_ip_addr(ip_addr, date_time_of_ip_addr_fetch):
    db_con = sqlite3.connect("ip_addrs.db")
    cur = db_con.cursor()
    cur.execute("INSERT INTO Stored_IP_Addresses VALUES(?, ?)", (ip_addr, date_time_of_ip_addr_fetch))
    db_con.commit()


# send_discord_notification function
# sends a notification using the webhook provided in the environment variables
def send_discord_notification(webhook_url, discord_id, message):
    # Extract webhook id and webhook token from provided url
    webhook_id = webhook_url.removeprefix('https://discord.com/api/webhooks/')
    webhook_id_and_token = webhook_id.partition('/')
    webhook_id = webhook_id_and_token[0]
    webhook_token = webhook_id_and_token[2]

    # Build request
    url = f'{webhook_url}?wait=true'

    payload = {
        "name": "Py Ip Checker",
        "type": 1,
        "token": webhook_token,
        "id": webhook_id,
        "content": message
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"
    }

    data = json.dumps(payload).encode('utf-8')

    try:
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as res:
            print(f'As requested a notification has been sent to Discord at '
                  f'{datetime.strftime(datetime.today(), "%H:%M:%S")}')
            return res.status
    except Exception:
        raise


#########################################
#
# MAIN
#
#########################################
def main():
    env_vars_main = read_env_vars()

    if check_db_exists() is True:
        last_ip_addr_with_date_time = read_last_ip_address_from_db()
        try:
            curr_ip_addr_date_time = [http_request_public_ip(), get_current_date_time()]
        except Exception:
            print("Unable to fetch public IP address, exiting...")
            exit()

        if curr_ip_addr_date_time[0] in last_ip_addr_with_date_time:
            print(f'''Your IP address has not changed since I checked''' 
                  f''' {find_time_delta_from_now(last_ip_addr_with_date_time[1])}''')
            store_ip_addr(curr_ip_addr_date_time[0], curr_ip_addr_date_time[1])
        else:
            print(f'''Your IP address has changed! Your new address is: {curr_ip_addr_date_time[0]}''')
            store_ip_addr(curr_ip_addr_date_time[0], curr_ip_addr_date_time[1])
            print(f'''Your new IP address is stored and I will be checking against it from now on!''')

            if env_vars_main['discord_notifications_enabled'] is True:
                message_to_send = 'Your IP Address has changed!'
                try:
                    send_discord_notification(env_vars_main['discord_webhook_url'], env_vars_main['discord_id'],
                                                message_to_send)
                except Exception:
                    print("Sorry unable to send a Discord notification, exiting...")
                    exit()
    else:
        print(f'''I don't have an IP address stored so creating a database now''')
        create_db()

        print(f'''Fetching your IP!''')
        first_ip_addr = http_request_public_ip()

        date_time_ip_addr_fetch = get_current_date_time()

        print(f'''Storing your first fetched IP address in the database!''')
        store_ip_addr(first_ip_addr, date_time_ip_addr_fetch)

        print(f'''Your current IP Address of {first_ip_addr} is stored!''')

        if env_vars_main['discord_notifications_enabled'] is True:
            message_to_send = 'Your current IP Address is now stored and being tracked for a change'
            send_discord_notification(env_vars_main['discord_webhook_url'], env_vars_main['discord_id'],
                                      message_to_send)


main()
