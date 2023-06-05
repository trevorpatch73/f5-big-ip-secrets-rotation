import csv
import random
import string
from getpass import getpass
import paramiko
import time

# Global Variables
break_glass_account_name = 'admin'

# Prompt user for TACACS+ credentials
username = input("Enter TACACS+ Username: ")
password = getpass("Enter TACACS+ Password: ")

# Prompt user for password requirements
length = int(input("Enter the desired length of the password: "))
special_chars = input("Enter the special characters to include (leave empty for no special characters): ")

# Generate a random password
characters = string.ascii_letters + string.digits + special_chars
new_password = ''.join(random.choice(characters) for _ in range(length))

# Define the CSV file path
csv_file = 'F5_BIG_IP_INVENTORY.csv'

# Initialize a list to store the device names and corresponding password change status
password_changes = []

# Connect to the F5 Big-IP device
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Connect to the F5 Big-IP device
            try:
                ssh.connect(row['DEVICE_IP_ADDRESS'], username=username, password=password)
                print(f"\nConnecting to F5 Big-IP device at {row['DEVICE_IP_ADDRESS']}")

                # Create an SSH shell
                shell = ssh.invoke_shell()

                # Send commands to rotate the password
                shell.send("tmsh\n")
                time.sleep(1)  # Delay to allow the command to execute
                if break_glass_account_name == 'admin':
                    shell.send(f"modify auth user {break_glass_account_name} prompt-for-password\n")
                    time.sleep(1)  # Delay to allow the command to execute
                if break_glass_account_name == 'root':
                    shell.send(f"modify auth password {break_glass_account_name}\n")
                    time.sleep(1)  # Delay to allow the command to execute
                shell.send(f"{new_password}\n")  # When prompted, enter the new password.
                time.sleep(1)  # Delay to allow the command to execute
                shell.send(f"{new_password}\n")  # When prompted, reenter the new password to confirm.
                time.sleep(1)  # Delay to allow the command to execute
                shell.send("save sys config\n")
                time.sleep(3)  # Delay to allow the command to execute
                shell.send("quit\n")

                # Wait for the commands to execute
                while not shell.recv_ready():
                    pass

                # Close the SSH connection
                ssh.close()

                # Re-establish SSH connection with the updated credentials
                updated_ssh = paramiko.SSHClient()
                updated_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                updated_ssh.connect(row['DEVICE_IP_ADDRESS'], username=username, password=new_password)

                # If the connection is successful, password change is considered successful
                updated_ssh.close()
                password_changes.append((row['DEVICE_NAME'], True))
                print(f"Password change successful for {row['DEVICE_NAME']}")

            except paramiko.AuthenticationException:
                password_changes.append((row['DEVICE_NAME'], False))
                print(f"Authentication failed for {row['DEVICE_NAME']}. Please check the username and password.")
            except paramiko.SSHException as ssh_exception:
                password_changes.append((row['DEVICE_NAME'], False))
                print(f"SSH error occurred for {row['DEVICE_NAME']}: {str(ssh_exception)}")

except FileNotFoundError:
    print(f"CSV file '{csv_file}' not found.")

# Print the final password applied to all devices
print(f"\nFinal password applied to all F5 Big-IP devices: {new_password}")

# Print the password change status for each device
print("\nPassword change status:")
for device_name, status in password_changes:
    print(f"Device Name: {device_name}, Status: {'Success' if status else 'Failed'}")