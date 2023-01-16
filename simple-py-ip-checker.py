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
import logging
import time
import calendar
from datetime import datetime, timezone


#########################################
#
# FUNCTIONS
#
#########################################


# read_env_vars function
# Read environment variables for more advanced features such as remote notifications
def read_env_vars():
    json_file = open('env.json', 'r')
    env_vars = json.load(json_file)
    return env_vars
    # TODO add regex check for '.db' and Discord webhook


# convert_str_time_utc_to_local_time
# Converts a string that represents a UTC time to a local time as type tuple
def convert_str_time_utc_to_local_time(str_time_utc):
    utc_time = time.strptime(str_time_utc, '%Y-%m-%d %H:%M:%S.%f%z')
    utc_time = calendar.timegm(utc_time)
    local_time = time.localtime(utc_time)
    return local_time


# check_db_exists function
# Checks if the database for storing IP addresses exists
def check_db_exists(db_name):
    logging.info(f'Checking if there is a database named {db_name} at current location')
    local_files_dirs = os.listdir('.')
    if db_name in local_files_dirs:
        logging.info(f'{db_name} found will reference last IP stored in the database')
        return True
    else:
        logging.info(f'No database named {db_name} found, will create a database named {db_name}')
        return False


# create_db function
# Creates a sqlite3 database for storing IP the addresses
def create_db(db_name):
    # Create DB
    try:
        db_con = sqlite3.connect(db_name)
        cur = db_con.cursor()
        cur.execute('''CREATE TABLE Stored_IP_Addresses 
                    (ip_addr, add_ip_addr_date_time)''')
        db_con.commit()
        db_con.close()
        logging.critical(f'Successfully created database {db_name}')
        return True
    except Exception as e:
        logging.critical('Error creating database')
        logging.debug(e)
        raise


# read_ip_address function
# Attempts to read from text file the last saved public IP address
def read_last_ip_address_from_db(db_name):
    try:
        logging.info(f'Attempting to connect and query {db_name} for last stored IP')
        db_con = sqlite3.connect(db_name)
        cur = db_con.cursor()
        res = cur.execute(f'''SELECT ip_addr, add_ip_addr_date_time
                            FROM Stored_IP_Addresses
                            ORDER BY add_ip_addr_date_time DESC
                            LIMIT 1
                        ''')
        res = res.fetchone()
        logging.info(f'Successfully connected to and queried the database')
        logging.info(f'Your most recently stored IP address fetched ' 
                     f'''{time.strftime('on %x at %X', convert_str_time_utc_to_local_time(res[1]))} ''' 
                     f'is: {res[0]}')
        db_con.close()
        return res
    except Exception as e:
        logging.critical('Database error')
        logging.debug(e)
        raise


# http_request_public_ip function
# This makes a request to a remote web server that will return your public IP address
# The response is a pointer for a memory location for an object that type is byte, so it must be decoded
# Function will decode response into a string and remove trailing new line characters
def http_request_public_ip():
    logging.info(f'Generating a request to server at http://checkip.amazonaws.com/ to determine current IP address')
    url = 'http://checkip.amazonaws.com/'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            # TODO Understand why response cannot be referenced twice
            pub_ib_addr = res.read().decode().removesuffix('\n')
            logging.info(f'''Request successful, your system's current public IP address is {pub_ib_addr}''')
            return pub_ib_addr
    except Exception as e:
        logging.critical(f'Request to http://checkip.amazonaws.com/ unsuccessful')
        logging.critical(e)
        raise


# get_current_date_time function
# gets the current date and time
def get_current_date_time():
    logging.info('Fetching the current time and date')
    current_date_time = datetime.now(timezone.utc)
    logging.info(f'''The current date and time is {datetime.strftime(datetime.today(), '%x %X')}''')
    return current_date_time


# find_time_delta_from_now function
# Function to find how long ago we last checked the public IP address to inform the user
def find_time_delta_from_now(last_date_time_ip_addr_changed):
    time_delta = datetime.now(timezone.utc) - datetime.strptime(last_date_time_ip_addr_changed,
                                                                '%Y-%m-%d %H:%M:%S.%f%z')
    calc_time_delta_hrs = math.floor(time_delta.seconds / 3600)
    calc_time_delta_mins = math.floor((time_delta.seconds % 3600) / 60)
    calc_time_delta_secs = math.ceil(((time_delta.seconds % 3600) % 60))
    return f'''{time_delta.days} day(s) {calc_time_delta_hrs} hour(s) {calc_time_delta_mins} minute(s)'''\
        f''' and {calc_time_delta_secs} second(s) ago'''


# store_ip_address function
# Writes the updated ip address to a text file called my ip
def store_ip_addr(ip_addr, date_time_of_ip_addr_fetch, db_name):
    logging.info(f'Attempting to store the current public IP address ({ip_addr}) '
                 f'and date and time of fetch ({date_time_of_ip_addr_fetch}) in the database')
    logging.info('Attempting to connect to database')
    try:
        db_con = sqlite3.connect(db_name)
        cur = db_con.cursor()
        cur.execute("INSERT INTO Stored_IP_Addresses VALUES(?, ?)", (ip_addr, date_time_of_ip_addr_fetch))
        db_con.commit()
        logging.info('Current public IP address and fetch date and time stored in the database '
                     'and will be tracked for changes')
    except Exception as e:
        logging.critical('Unable to connect to database')
        logging.debug(e)
        raise


# send_discord_notification function
# sends a notification using the webhook provided in the environment variables
def send_discord_notification(webhook_url, discord_id, message):
    # Extract webhook id and webhook token from provided url
    webhook_id_and_token = webhook_url.removeprefix('https://discord.com/api/webhooks/')
    webhook_id_and_token = webhook_id_and_token.partition('/')
    webhook_id = webhook_id_and_token[0]
    webhook_token = webhook_id_and_token[2]

    # Build request
    logging.info('Generating request to Discord API for webhook invocation')
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
            logging.info('Discord notification sent')
            return res.status
    except Exception as e:
        logging.critical('Request to send Discord notification was unsuccessful')
        logging.debug(e)
        raise


#########################################
#
# INITIALIZATION
#
#########################################
def init():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%x %X',
                        level=logging.INFO)
    logging.info('simple-py-ip-checker.py starting and now initializing')

    env_vars = read_env_vars()
    default_log_levels = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10, 'NOTSET': 0}

    if env_vars['log_level'] in default_log_levels:
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%x %X',
                            level=default_log_levels[env_vars['log_level']])
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%x %X',
                            level=logging.WARN)

    return env_vars


#########################################
#
# MAIN
#
#########################################
def main():
    init_vars = init()
    if check_db_exists(init_vars['db_name']) is True:
        try:
            last_ip_addr_with_date_time = read_last_ip_address_from_db(init_vars['db_name'])
        except Exception:
            logging.error('Exiting due to error reading from database')
            exit(1)
        try:
            curr_ip_addr_date_time = [http_request_public_ip(), get_current_date_time()]
        except Exception:
            logging.error('Exiting due to error fetching current public IP address')
            exit(1)

        if curr_ip_addr_date_time[0] in last_ip_addr_with_date_time:
            logging.info(f'''Your IP address has not changed since I checked''' 
                         f''' {find_time_delta_from_now(last_ip_addr_with_date_time[1])}''')
            try:
                store_ip_addr(curr_ip_addr_date_time[0], curr_ip_addr_date_time[1], init_vars['db_name'])
            except Exception:
                logging.error('Exiting due to error writing to database')
                exit(1)
        else:
            logging.info(f'Your IP address has changed! Your new address is: {curr_ip_addr_date_time[0]}')
            store_ip_addr(curr_ip_addr_date_time[0], curr_ip_addr_date_time[1], init_vars['db_name'])
            if init_vars['discord_notifications_enabled'] is True:
                message_to_send = 'Your IP Address has changed!'
                try:
                    send_discord_notification(os.environ['discord_webhook_url'], init_vars['discord_id'],
                                              message_to_send)
                except Exception:
                    logging.error('Exiting due to error sending Discord notification')
                    exit(1)

        logging.info(f'Script successfully executed, exiting...')
        exit(0)
    else:
        try:
            logging.info(f'''Database doesn't exist, creating one named {init_vars['db_name']}''')
            create_db(init_vars['db_name'])
        except Exception:
            logging.error('Exiting due to error creating Database')
            exit(1)
        try:
            first_ip_addr = http_request_public_ip()
        except Exception:
            logging.error('Exiting due to error fetching current public IP address')
            exit(1)

        date_time_ip_addr_fetch = get_current_date_time()

        try:
            store_ip_addr(first_ip_addr, date_time_ip_addr_fetch, init_vars['db_name'])
        except Exception:
            logging.error('Exiting due to error writing to database')
            exit(1)

        if init_vars['discord_notifications_enabled'] is True:
            message_to_send = 'Your current IP Address is now stored and being tracked for a change'
            send_discord_notification(init_vars['discord_webhook_url'], init_vars['discord_id'],
                                      message_to_send)

    logging.info(f'Script successfully executed, exiting...')
    exit(0)


main()
