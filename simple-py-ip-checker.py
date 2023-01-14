# This script checks your public IP and notifies you if it changes

#########################################
#
# IMPORTS
#
#########################################

import urllib.request
import sqlite3
import os
from datetime import datetime, date, time, timezone

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
def read_ip_address():
    db_con = sqlite3.connect("ip_addrs.db")
    cur = db_con.cursor()


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
    current_date_time = datetime.now(timezone.utc).strftime('%G-%m-%d %H:%M:%S.%f%z')
    return current_date_time

# store_ip_address function
# Writes the updated ip address to a text file called my ip
def store_ip_addr(new_ip_addr, date_time_of_ip_addr_fetch):
    db_con = sqlite3.connect("ip_addrs.db")
    cur = db_con.cursor()
    cur.execute("INSERT INTO Stored_IP_Addresses VALUES(?, ?)", (new_ip_addr, date_time_of_ip_addr_fetch))
    db_con.commit()
    res = cur.execute("SELECT * FROM Stored_IP_Addresses")


#########################################
#
# MAIN
#
#########################################
def main():
    if check_db_exists() is True:
        first_ip_addr = http_request_public_ip()
        store_ip_addr(first_ip_addr)

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
