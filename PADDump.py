'''
SETUP:
make sure the variables below are correct. If usernames are blank output will be written to files instead of automatically uploaded.

On first run, visit mitm.it on your phone and install the certificate.

===== YOU MUST DO THE BELOW STEP *BEFORE* RUNNING THIS SCRIPT =====(could probably be made automatic in network.py)
On your iphone wifi settings, change ip from DHCP to static and manually fill the fields to match the settings under DHCP
You will need to change the "router" field to the ip address of this computer if you aren't jailbroken.

IMPORTANT: if you are using ssh to switch your phones gateway automatically, you must install the network commands app in cydia

share your google sheet with the email of your drive api account (give edit permission)
(the data will be put into the first worksheet, so make sure theres nothing important in there)



If you want a nice summary of your mailbox put this in another worksheet (change the "Mails" reference as needed)
in cell A1:
=SORT(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))),LEN(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A="")))),True)
in cell B1:
=ARRAYFORMULA(COUNTIF(Mails!A:A,OFFSET(A1,0,0,COUNTA(A:A),1)))
for a total:
=SUM(B:B)&" Unopened Mails"
for pal points sum:
=SUM(ARRAYFORMULA(B:B*VALUE(IFERROR(REGEXEXTRACT(A:A,"^Pal Points \((\d*)")))))&" Pal Points"
for tamadra count:
=COUNTIF(Mails!A:A,"TAMADRA*")&" TAMADRA"
jewels count:
=COUNTIF(Mails!A:A,"Jewel of*")&" Jewels"
py count:
=COUNTIF(Mails!A:A,"*py")&" Pys"

If you want them to be more sorted, put this in A1 instead:
=SORT(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))),LEN(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))),"y","")),False,LEN(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))),"J","")),False,LEN(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))),"T","")),False,LEN(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(Mails!A:A,NOT(Mails!A:A="")))," ","")),True)
'''
'''
dependencies: mitmproxy, gspread
'''
try:
    import win32api
    win32api.SetDllDirectory(sys._MEIPASS)
except:
    pass


from mitmproxy.platform import windows
import time
import subprocess
import os
##mitmdump -T -s exploit.py
from mitmproxy.models import decoded
##from libmproxy.script import concurrent
import cffi#added just for pyinstaller's sake

import network
import re
from requests import session

import json
from oauth2client.client import SignedJwtAssertionCredentials
import _winreg as wr
import signal
import ConfigParser
from contextlib import closing
import socket

# extra modules
import gspread
import parsemails
import admin


####################################################
################### CONFIG SETUP ###################
####################################################
Gateway = socket.gethostbyname(socket.gethostname()) # ip of this computer
# actually that method might fail if you have multi network adapters (including virtual ones)
# this should be more reliable:
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('1.1.1.1', 0))
Gateway = s.getsockname()[0]

config_essentials = 'PADHerder Credentials (REQUIRED)'
config_gsheets='Google Sheets Integration'
config_jailbreak = 'Automatic iPhone Gateway Setup'
def set_defaults(config):
    
    config.add_section(config_essentials)
    config.set(config_essentials,'padherder_username','yourusernamehere')
    config.set(config_essentials,'padherder_password','yourpasswordhere')
    
    config.add_section(config_gsheets)
    config.set(config_gsheets,'json_key_file','')#oauth2 credentials for google drive http://gspread.readthedocs.org/en/latest/oauth2.html
    config.set(config_gsheets,'spreadsheet_name','') # spreadsheet that will be automatically updated (the first worksheet will be overwritten)

    
    config.add_section(config_jailbreak)
    config.set(config_jailbreak,'ssh_username','')#needs su privileges (i.e. root)
    config.set(config_jailbreak,'ssh_password','')
    config.set(config_jailbreak,'iphone_ip','')
    config.set(config_jailbreak,'router_ip','')# ip of your default gateway, probably your router, probably already correct.

def get_dict(config):
    return dict(config.items(config_essentials)+config.items(config_gsheets)+config.items(config_jailbreak))

Config = ConfigParser.ConfigParser()
configfile='PADDumpConfig.ini'
if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)),configfile)):
    with closing(open(os.path.join(os.path.dirname(os.path.realpath(__file__)),configfile),'r')) as f:
        Config.readfp(f)
else:
    set_defaults(Config)
    with closing(open(os.path.join(os.path.dirname(os.path.realpath(__file__)),configfile),'w')) as f:
        Config.write(f)
    print("Please enter your padherder username and password in the %s file and restart this script."%configfile)
    time.sleep(10)
    exit(0)

CREDENTIALS = get_dict(Config)

####################################################
############### PROXY FUNCTIONS ####################
####################################################
def update_mails(mails):
    if CREDENTIALS['json_key_file']:
        with closing(open(os.path.join(os.path.dirname(os.path.realpath(__file__)),CREDENTIALS['json_key_file']),'r')) as f:
            json_key = json.load(f)
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)
        gc = gspread.authorize(credentials)
        wks = gc.open(CREDENTIALS['spreadsheet_name']).sheet1

        # "blank" existing cells as much as google will let us
        cell_list = wks.range('A1:D256')#A256 if you please
    ##    cell_list+=wks.range('C1:D256')
        for cell in cell_list:
            cell.value = ''
        wks.update_cells(cell_list)
        
        # use this arrayformula to generate the "x days old" for each mail
    ##    wks.update_cell(1,2,'=ARRAYFORMULA(FLOOR(NOW()-INDIRECT("D1:D"&COUNTA(D:D)),1))')

        #insert the mails
        data = parsemails.parse_mail(mails)
        flat = [item for sublist in data for item in sublist]
        cell_list = wks.range('A1:'+wks.get_addr_int(len(data),4))

        for i in range(len(cell_list)):
            cell_list[i].value = flat[i]

        wks.update_cells(cell_list)
        wks.update_acell("E1",'''=SORT(UNIQUE(FILTER(A:A,NOT(A:A=""))),LEN(UNIQUE(FILTER(A:A,NOT(A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(A:A,NOT(A:A=""))),"y","")),False,LEN(UNIQUE(FILTER(A:A,NOT(A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(A:A,NOT(A:A=""))),"J","")),False,LEN(UNIQUE(FILTER(A:A,NOT(A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(A:A,NOT(A:A=""))),"T","")),False,LEN(UNIQUE(FILTER(A:A,NOT(A:A=""))))-LEN(SUBSTITUTE(UNIQUE(FILTER(A:A,NOT(A:A="")))," ","")),True)''')
        wks.update_acell("F1",'''=ARRAYFORMULA(COUNTIF(A:A,OFFSET(E1,0,0,COUNTA(E:E),1)))''')
        
##    else:
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pad_mails.csv'),'w') as f:
        f.write('\n'.join([','.join(line) for line in parsemails.parse_mail(mails)]))


def update_padherder(json_data):
    if CREDENTIALS['padherder_username']:
        login_url = ur'https://www.padherder.com/auth/login'
        json_upload_url = ur'https://www.padherder.com/account/import_json/'
        csrf_token = re.compile("name='csrfmiddlewaretoken' value='([^']*)")
    ##    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36',
    ##                 'Referer':url}
        s = session()
        s.headers.update({'Referer':login_url})
        
        response = s.get(login_url)
        csrf = csrf_token.findall(response.text)[0]
        
        forms = {'username':CREDENTIALS['padherder_username'], 'password':CREDENTIALS['padherder_password'],'csrfmiddlewaretoken':csrf}
        response = s.post(login_url, data=forms)
        csrf = csrf_token.findall(response.text)[0]

        forms = {'add_new':'on',
                 'delete_old':'on',
                 'friends':'off',
                 'csrfmiddlewaretoken':csrf,
                 'ignore_below':'off',
                 'ignore_value':'4'}

        response = s.post(json_upload_url, data=forms, files={'json_file':('json.json',json_data)})
        s.close()
    else:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'padherder.json'),'w') as f:
            f.write(json_data)

####################################################
################ UTIL FUNCTIONS ####################
####################################################
def launchWithoutConsole(command, args):
    """Launches 'command' windowless and waits until finished"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
##    with open(os.devnull,'w') as devnull:
    return subprocess.Popen([command] + args, startupinfo=startupinfo).wait()



"""http://code.activestate.com/recipes/491264-mini-fake-dns-server/"""

import socket, sys
import binascii,copy,struct, time
from dnslib import DNSRecord,RR,QTYPE,RCODE,parse_time,A
from dnslib.server import DNSServer,DNSHandler,BaseResolver,DNSLogger
from dnslib.label import DNSLabel
import re

from mitmproxy import controller, proxy, flow, dump, cmdline, contentviews
from mitmproxy.proxy.server import ProxyServer
import thread

parse_host_header = re.compile(r"^(?P<host>[^:]+|\[.+\])(?::(?P<port>\d+))?$")

class PadMaster(flow.FlowMaster):
    def __init__(self, server, main_window, region):
        flow.FlowMaster.__init__(self, server, flow.State())
##        self.status_ctrl = main_window.main_tab
##        self.mail_tab = main_window.mail_tab
        self.region = region
        self.monster_data = self.mailbox_data = None
        #self.start_app('mitm.it', 80)


    def run(self):
        try:
            return flow.FlowMaster.run(self)
        except KeyboardInterrupt:
            self.shutdown()

    def handle_request(self, f):
        if f.client_conn.ssl_established:
            f.request.scheme = "https"
            sni = f.client_conn.connection.get_servername()
            port = 443
        else:
            f.request.scheme = "http"
            sni = None
            port = 80

        host_header = f.request.pretty_host
        m = parse_host_header.match(host_header)
        if m:
            host_header = m.group("host").strip("[]")
            if m.group("port"):
                port = int(m.group("port"))

        f.request.host = sni or host_header
        f.request.port = port
        print("Got HTTPS request, forwarding")
##        evt = custom_events.wxStatusEvent(message="Got HTTPS request, forwarding")            
##        wx.PostEvent(self.status_ctrl,evt)
        
        flow.FlowMaster.handle_request(self, f)
        if f:
            f.reply()
        return f
        
    def handle_response(self, f):
        flow.FlowMaster.handle_response(self, f)
        if f:
            f.reply()
            if f.request.path.startswith('/api.php?action=get_player_data'):
                print("Got box data, processing...")
                resp = f.response.content
                type, lines = contentviews.get_content_view(
                    contentviews.get("Raw"),
                    f.response.content,
                    headers=f.response.headers)

                def colorful(line):
                    for (style, text) in line:
                        yield text
                        
                content = u"\r\n".join(
                    u"".join(colorful(line)) for line in lines
                )
                
                cap = open('captured_data.txt', 'w')
                cap.write(content)
                cap.close()
                self.monster_data = content
                
                update_padherder(content)

            if f.request.path.startswith('/api.php?action=get_user_mail'):
                resp = f.response.content
                type, lines = contentviews.get_content_view(
                    contentviews.get("Raw"),
                    f.response.content,
                    headers=f.response.headers)

                def colorful(line):
                    for (style, text) in line:
                        yield text
                        
                content = u"\r\n".join(
                    u"".join(colorful(line)) for line in lines
                )
                
                cap = open('captured_mail.txt', 'w')
                cap.write(content)
                cap.close()
                
                self.mailbox_data = content
##                mails = parse_mail(content)
##                mails.reverse()
                print("Got mail data, processing...")
##                evt = custom_events.wxMailEvent(mails=mails)
##                wx.PostEvent(self.mail_tab, evt)
##                evt = custom_events.wxStatusEvent(message="Got mail data, processing...")            
##                wx.PostEvent(self.status_ctrl,evt)
            if self.mailbox_data and self.monster_data:
                thread.start_new_thread(lambda: [update_padherder(self.monster_data),update_mails(self.mailbox_data),sys.exit()],())
                
        return f



class InterceptResolver(BaseResolver):

    """
        Intercepting resolver 
        
        Proxy requests to upstream server optionally intercepting requests
        matching local records
    """

    def __init__(self,address, port, ttl, hostaddr):
        """
            address/port    - upstream server
            ttl             - default ttl for intercept records
        """
        self.address = address
        self.port = port
        self.ttl = parse_time(ttl)
        self.hostaddr = hostaddr
        self.proxy_master = None

    def onDNSEvent(self, message):
        if self.proxy_master is not None:
            self.proxy_master.shutdown()
        
        if message.startswith('api-na'):
            region = 'NA'
        else:
            region = 'JP'
        
##        config = wx.ConfigBase.Get()
        host = self.hostaddr
        httpsport = "443"

        try:
            proxy_config = proxy.ProxyConfig(port=int(httpsport), host=host, mode='reverse', upstream_server=cmdline.parse_server_spec('https://%s:443/' % message))
            proxy_server = ProxyServer(proxy_config)
        except Exception as e:
            raise

        self.proxy_master = PadMaster(proxy_server, self, region)
        thread.start_new_thread(self.proxy_master.run, ())

    def resolve(self,request,handler):
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        if qname.matchGlob("api-*padsv.gungho.jp."):
##            config = wx.ConfigBase.Get()
            host = self.hostaddr
            reply.add_answer(RR(qname,QTYPE.A,rdata=A(host)))
##            evt = custom_events.wxStatusEvent(message="Got DNS Request")
##            evt = custom_events.wxDNSEvent(message=str(qname)[:-1])
            self.onDNSEvent(str(qname)[:-1])
            time.sleep(0.5) # we need to sleep until the proxy is up, half a second should do it...
        # Otherwise proxy
        if not reply.rr:
            if handler.protocol == 'udp':
                proxy_r = request.send(self.address,self.port)
            else:
                proxy_r = request.send(self.address,self.port,tcp=True)
            reply = DNSRecord.parse(proxy_r)
        return reply

def serveDNS(hostaddr):
    dnsport = 53
    resolver = InterceptResolver('8.8.8.8',
                                 dnsport,
                                 '60s',
                                 hostaddr)
    try:
        udp_server = DNSServer(resolver,
                           port=dnsport,
                           address=hostaddr)
    except Exception as e:
        raise
    
    udp_server.start_thread()
    
    try:
        while udp_server.isAlive():
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit()





    
if __name__=='__main__':
    if not admin.isUserAdmin():
        admin.runAsAdmin()
        
##    thread.start_new_thread(serveDNS, (Gateway,))
    serveDNS(Gateway)

##    app_config = proxy.ProxyConfig(port=8080, host=Gateway)
##    app_server = ProxyServer(app_config)
##    app_master = dump.DumpMaster(app_server, dump.Options(app_host='mitm.it', app_port=80, app=True))
##    thread.start_new_thread(app_master.run, ())

##    app_master.run()
    exit(0)
        
##    print(" * Setting up...")
    print("\nPerforming setup tasks, close PAD on your phone while you wait.\n")
    proxy = windows.TransparentProxy(mode='forward')
    proxy.start()
##    print(" * Transparent proxy active.")
##    print("   Filter: {0}".format(proxy.request_filter))
    try:
        aKey = wr.CreateKey(wr.HKEY_LOCAL_MACHINE, 'SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters')
        already_enabled = wr.QueryValueEx(aKey,'IPEnableRouter')[0]
        if not already_enabled:
            print("\n")
            print("Visit mitm.it on your phone and install the certificate\nif this is your first time running this script.")
            print("\n")
            wr.SetValueEx(aKey,'IPEnableRouter',0,wr.REG_DWORD,1)
            with open(os.devnull,'w') as devnull:
                subprocess.call('sc stop remoteaccess', stdout = devnull, stderr = subprocess.STDOUT)
                subprocess.call('sc config remoteaccess start= demand', stdout = devnull, stderr = subprocess.STDOUT)
        wr.CloseKey(aKey)
        with open(os.devnull,'w') as devnull:
            subprocess.call('sc start remoteaccess', stdout = devnull, stderr = subprocess.STDOUT)
        if CREDENTIALS['ssh_username']:
            print("Restarting your phone's network adapter, please wait...")
            network.change_router_ip(CREDENTIALS['iphone_ip'],Gateway,CREDENTIALS['ssh_username'],CREDENTIALS['ssh_password'])
        else:
            print("Change your phone's gateway to the ip of this computer (%s)."%Gateway)
            
        print("\nSetup complete! (re)Open PAD and press start now.\n")
        launchWithoutConsole("mitmdump",['-T', '-q', '-s', os.path.realpath(__file__)])
##        subprocess.call("mitmdump -T -s "+os.path.realpath(__file__))
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(5) # give your phone time to log into pad so you don't experience any errors
##        print(" * Shutting down...")
        try:
            proxy.shutdown()
        except Exception:
            'you tried'
        try:
            with open(os.devnull,'w') as devnull:
                subprocess.call('sc stop remoteaccess', stdout = devnull, stderr = subprocess.STDOUT)
        except Exception:
            'you tried'
        try:
            if CREDENTIALS['ssh_username']:
                network.change_router_ip(CREDENTIALS['iphone_ip'],CREDENTIALS['router_ip'],CREDENTIALS['ssh_username'],CREDENTIALS['ssh_password'])
            else:
                print("\nChange your phone's gateway back to its default.")
                time.sleep(10)
##            print(" * Shut down.")
        except Exception:
            'good enough'
