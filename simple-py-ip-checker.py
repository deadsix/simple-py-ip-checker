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
from datetime import datetime, timezone

#########################################
#
# FUNCTIONS
#
#########################################


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
    http_request = urllib.request.urlopen('http://checkip.amazonaws.com/')

    return http_request.read().decode().removesuffix('\n')


# get_current_date_time function
# gets the current date and time
def get_current_date_time():
    current_date_time = datetime.now(timezone.utc)
    return current_date_time


# find_time_delta_from_now function
# Function to find how long ago we last checked the public IP address to inform the user
def find_time_delta_from_now(last_date_time_ip_addr_changed):
    time_delta = datetime.now(timezone.utc) - datetime.strptime(last_date_time_ip_addr_changed, '%Y-%m-%d %H:%M:%S.%f%z')
    calc_time_delta_hrs = math.floor(time_delta.seconds / 3600)
    calc_time_delta_mins = math.floor((time_delta.seconds % 3600) / 60)
    calc_time_delta_secs = math.ceil(((time_delta.seconds % 3600) % 60))
    return f'''{time_delta.days} days {calc_time_delta_hrs} hours {calc_time_delta_mins} minutes and {calc_time_delta_secs} seconds ago'''


# store_ip_address function
# Writes the updated ip address to a text file called my ip
def store_ip_addr(ip_addr, date_time_of_ip_addr_fetch):
    db_con = sqlite3.connect("ip_addrs.db")
    cur = db_con.cursor()
    cur.execute("INSERT INTO Stored_IP_Addresses VALUES(?, ?)", (ip_addr, date_time_of_ip_addr_fetch))
    db_con.commit()


#########################################
#
# MAIN
#
#########################################
def main():
    if check_db_exists() is True:
        last_ip_addr_with_date_time = read_last_ip_address_from_db()
        curr_ip_addr_date_time = [http_request_public_ip(), get_current_date_time()]

        if curr_ip_addr_date_time[0] in last_ip_addr_with_date_time:
            print(f'''Your IP address has not changed since I checked {find_time_delta_from_now(last_ip_addr_with_date_time[1])}''')
            store_ip_addr(curr_ip_addr_date_time[0], curr_ip_addr_date_time[1])

    else:
        print(f'''I don't have an IP address stored so creating a database now''')
        create_db()

        print(f'''Fetching your IP!''')
        first_ip_addr = http_request_public_ip()

        date_time_ip_addr_fetch = get_current_date_time()

        print(f'''Storing your first fetched IP address in the database!''')
        store_ip_addr(first_ip_addr, date_time_ip_addr_fetch)

        print(f'''Your current IP Address of {first_ip_addr} is stored!''')


main()
