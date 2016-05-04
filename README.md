# PADDump
mitmproxy script for windows that collects puzzle and dragons monster box and mailbox data


####First Time Setup
  1. Run PadDump once to create the config file.
  2. Fill in as much as you want (description in config options below)
  3. Restart PADDump
  4. Set up your phone (see the below section)

####Initial Phone Setup
These instructions are for iPhone but should be similar on android devices
  1. Go to Settings > Wifi > click the i > write down all the information you see.
  2. Switch from "DHCP" to "Static" and fill all the fields in with the information you recorded.
  3. Change the "Router" field to the IP of your computer (PADDump should display this for you)
  4. Open Safari (non-default browsers may fail) and visit http://mitm.it
  5. Install the certificate for your device.
  6. After using PADDump you must go back to Wifi settings and change the "Router" field back to its default.
    (You don't have to switch back to DHCP every time.)
	
For future runs all you need to do is step 3 and step 6 afterwards. This can also be automated if your phone is jailbroken (see below).

####Config Options:
######[PADHerder Credentials (REQUIRED)]
Simple, just put in your padherder username and password.
This will allow paddump to automatically update your padherder.

######[Google Sheets Integration]
If set up, PADDump can automatically fill in a google sheets spreadsheet with your mailbox data.
you can get the json file here: http://gspread.readthedocs.org/en/latest/oauth2.html
The config requires the name of the file (of course put it in the same directory as PADDump)
You will also need to share your spreadsheet with the email of the drive account you made to get this key.
The mailbox data will go into the first worksheet so make sure theres nothing important there.

######[Automatic iPhone Gateway Setup]
If your phone is jailbroken you can have PADDump automatically change the wifi settings for you.
The one requirement is that you install "Network Commands" from cydia. (uses ifconfig)
You may also need to use an account with root access (not tested)

####Tips
You can paste/import hte contents of pad_mails.csv into any spreadsheet program (including online ones)
You can also manually import padherder.json to padherder.
