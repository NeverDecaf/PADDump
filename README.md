# PADDump

####First Time Setup
  1. Run PadDump once to create the config file.
  2. Fill in as much of the config as you want (description in config options below)
  3. Restart PADDump
  4. Set up your phone (see the below section)

####Initial Phone Setup
These instructions are for iPhone but should be similar on android devices
  1. Go to Settings > Wifi > click the i > set HTTP PROXY to manual and enter your IP under server and 8080 under Port (PADDump will display your IP)
  2. Open Safari and navigate to http://mitm.it (you must use safari, other browsers probably won't work.)
  3. Install the certificate for your device.
  4. Go back to wifi settings and turn off the HTTP Proxy.
  5. Change the DNS field to the IP address of your computer, but take a note of what it was before.
  6. Change the DNS field back to the default once you finish using PADDump

**You will need to repeat steps 5 and 6 every time you run PADDump**
See _Automatic iPhone DNS Setup_ in the config to automate this process.  
An easy way of automating this (with pretty severe consequences) is to *add* your computer's IP to the DNS field, rather than replacing it entirely.   
For example, if your IP is 192.168.1.20 and the default DNS was 192.168.1.1 you want the field to read "192.168.1.20, 192.168.1.1"  
Make sure your computer's IP is first or it won't work.  
This method is not recommended unless you only use your device for PAD, and even then it can cause inconveniences.



####Config Options:
######[PADHerder Credentials]
Simple, just put in your padherder username and password.  
This will allow paddump to automatically update your padherder.  
if run_continously is 0, PADDump will exit after the first successful update of your mail(box).  
For most cases you'll want to leave this at 0.  

######[Google Sheets Integration]
If set up, PADDump can automatically fill in a google sheets spreadsheet with your mailbox data.  
you can get the json file here: http://gspread.readthedocs.org/en/latest/oauth2.html  
The config requires the name of the file (of course put it in the same directory as PADDump)  
You will also need to share your spreadsheet with the email of the drive account you made to get this key.  
The mailbox data will go into the first worksheet so make sure theres nothing important there.  

######[Automatic iPhone DNS Setup]
If your phone is jailbroken you can have PADDump automatically change the wifi settings for you.  
The one requirement is that you install "Network Commands" from cydia. (uses ifconfig)  
You may also need to use an account with root access (not tested)  

####Tips
You can paste/import the contents of pad_mails.csv into any spreadsheet program (including online ones)
