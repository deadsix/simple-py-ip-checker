# This script checks your public IP and notifies you if it changes

import urllib.request


#########################################
#
# FUNCTIONS
#
#########################################

# read_ip_address function
# Attempts to read from text file the last saved public IP address
def read_ip_address():
    try:
        with open('my_ip', 'r', encoding="utf-8") as ip_text_file:
            last_ip_addr = ip_text_file.read()
        return last_ip_addr
    except FileNotFoundError:
        print('Saved IP Address file not found, storing current IP address')
        return False


# http_request_public_ip function
# This makes a request to a remote web server that will return your public IP address
# The response is a pointer for a memory location for an object that type is byte so it must be decoded
# Function will decode response into a string and remove trailing new line characters
def http_request_public_ip():
    http_request = urllib.request.urlopen('http://checkip.amazonaws.com/')

    return http_request.read().decode().removesuffix('\n')


# store_ip_address function
# Writes the updated ip address to a text file called my ip
def store_ip_addr(new_ip_addr):
    with open('my_ip', 'w', encoding="utf-8") as ip_text_file:
        ip_text_file.write(new_ip_addr)


#########################################
#
# MAIN
#
#########################################
def main():
    saved_ip_addr = read_ip_address()

    if saved_ip_addr == False:
        first_ip_addr = http_request_public_ip()
        store_ip_addr(first_ip_addr)
        print(f'''I didn't have an IP address stored so I saved your current IP Address of {first_ip_addr}''')
    else:
        current_ip_addr = http_request_public_ip()

        if saved_ip_addr == current_ip_addr:
            print(f'Your IP Address of {saved_ip_addr} has not changed since I last checked')
        else:
            print(f'''Your IP Address changed! I'm saving your new IP Address: {current_ip_addr}''')
            store_ip_addr(current_ip_addr)
            print('Your new IP Address is saved!')


main()
