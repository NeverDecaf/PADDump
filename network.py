''' THIS WILL NOT WORK UNLESS YOU INSTALL "NETWORK COMMANDS" IN CYDIA'''



'http://www.priyaontech.com/2012/01/ssh-into-your-jailbroken-idevice-without-a-password/'
'/private/var/preferences/SystemConfiguration'
import paramiko
import biplist
from pprint import pprint
import base64
from StringIO import StringIO

def change_router_ip(cip,newip,username,password):
    t = paramiko.Transport(cip,22)
    t.connect(None, username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(t)
    with sftp.open('/private/var/preferences/SystemConfiguration/preferences.plist','r') as f:
        data=f.read()
    tempFile = StringIO(data)
    plist = biplist.readPlist(tempFile)
    current_network = plist['CurrentSet'].split('/')[-1]
    current_services = plist['Sets'][current_network]['Network']['Global']['IPv4']['ServiceOrder']
    for service in current_services:
        if 'IPv4' in plist['NetworkServices'][service]:
            plist['NetworkServices'][service]['IPv4']['Router'] = newip
            break
    else:
        print "Your phone is using DHCP, please switch to Static IP (just copy over the dhcp settings)"
        raise Exception("Phone network settings could not be changed successfully")
    tempFile = StringIO()
    biplist.writePlist(plist,tempFile)
    with sftp.open('/private/var/preferences/SystemConfiguration/preferences.plist','w') as f:
        f.write(tempFile.getvalue())
    t.close()
    reset_wifi(cip,username,password)

def reset_wifi(cip,username,password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(cip, username=username, password=password)
    stdin, stdout, stderr = client.exec_command('ifconfig en0 down && ifconfig en0 up')
    exit_status = stdout.channel.recv_exit_status()
    client.close()
