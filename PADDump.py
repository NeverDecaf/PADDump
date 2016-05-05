'''
SETUP:
install mitm cert.
add this computer's ip to dns list (must be first).

See README.md for more detail.


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
dependencies: mitmproxy, gspread, requests, dnslib, python-dateutil, pytz, paramiko, biplist
'''
import time
import os
##import cffi#added just for pyinstaller's sake
import re
from requests import session
import json
from oauth2client.client import SignedJwtAssertionCredentials
import ConfigParser
from contextlib import closing
import socket
# extra modules
import gspread
import parsemails
import network
import atexit
"""http://code.activestate.com/recipes/491264-mini-fake-dns-server/"""

import sys
##import binascii,copy,struct, time
from dnslib import DNSRecord,RR,QTYPE,RCODE,parse_time,A
from dnslib.server import DNSServer,DNSHandler,BaseResolver,DNSLogger
from dnslib.label import DNSLabel
##import re

from mitmproxy import controller, proxy, flow, dump, cmdline, contentviews
from mitmproxy.proxy.server import ProxyServer
import thread


####################################################
################### CONFIG SETUP ###################
####################################################
Gateway = socket.gethostbyname(socket.gethostname()) # ip of this computer
# actually that method might fail if you have multi network adapters (including virtual ones)
# this should be more reliable:
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('1.1.1.1', 0))
Gateway = s.getsockname()[0]



config_essentials = 'PADHerder Credentials'
config_gsheets='Google Sheets Integration'
config_jailbreak = 'Automatic iPhone DNS Setup'
def set_defaults(config):
    
    config.add_section(config_essentials)
    config.set(config_essentials,'padherder_username','yourusernamehere')
    config.set(config_essentials,'padherder_password','yourpasswordhere')
    config.set(config_essentials,'run_continuously','0') # if 0, will exit after first successful update. otherwise will just run forever
    
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

####################################################
############## UPDATE FUNCTIONS ####################
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
############### PROXY FUNCTIONS ####################
####################################################
parse_host_header = re.compile(r"^(?P<host>[^:]+|\[.+\])(?::(?P<port>\d+))?$")

class PadMaster(flow.FlowMaster):
    def __init__(self, server, main_window, region):
        flow.FlowMaster.__init__(self, server, flow.State())
        self.region = region
        self.monster_data = self.mailbox_data = None

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
##        print("Got HTTPS request, forwarding")        
        flow.FlowMaster.handle_request(self, f)
        if f:
            f.reply()
        return f

    def reset_data(self):
        print("Update complete, standing by...")
        self.mailbox_data=self.monster_data=None
        if not CREDENTIALS['run_continuously'] or CREDENTIALS['run_continuously'] == '0' or CREDENTIALS['run_continuously'] == 'false' or CREDENTIALS['run_continuously'] == 'False':
            print("Update complete, shutting down...")
            DNS_cleanup()
            os._exit(0)
        
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
                print("Got mail data, processing...")
                
            if self.mailbox_data and self.monster_data:
                thread.start_new_thread(lambda: [update_padherder(self.monster_data),update_mails(self.mailbox_data),self.reset_data()],())
        return f


####################################################
################ DNS FUNCTIONS #####################
####################################################
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
            
        host = self.hostaddr
        httpsport = 443

        try:
            proxy_config = proxy.ProxyConfig(port=httpsport, host=host, mode='reverse', upstream_server=cmdline.parse_server_spec('https://%s:443/' % message))
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
            host = self.hostaddr
            reply.add_answer(RR(qname,QTYPE.A,rdata=A(host)))
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
                           address=hostaddr,
                           logger = DNSLogger("-send,-recv,-request,-reply,-truncated,-error", False))
    except Exception as e:
        raise
    
    udp_server.start_thread()
    
    try:
        while udp_server.isAlive():
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit()

def DNS_cleanup():
    if CREDENTIALS['ssh_username']:
        print("Fixing your iPhone's DNS (requires network restart).")
        network.change_router_ip(CREDENTIALS['iphone_ip'],CREDENTIALS['router_ip'],CREDENTIALS['ssh_username'],CREDENTIALS['ssh_password'])
    else:
        print("Change your phone's gateway back to its default.")
        time.sleep(7)

if __name__=='__main__':
    print('Your IP is %s'%Gateway)
    
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

    if CREDENTIALS['ssh_username']:
        print("Restarting your phone's network adapter, please wait...")
        network.change_router_ip(CREDENTIALS['iphone_ip'],Gateway,CREDENTIALS['ssh_username'],CREDENTIALS['ssh_password'])
        print("Setup complete! (re)Open PAD and press start now.\n")
    else:
        print("Change your phone's gateway to the ip of this computer (%s), then (re)open PAD and press start."%Gateway)
    
    app_config = proxy.ProxyConfig(port=8080, host=Gateway)
    app_server = ProxyServer(app_config)
    app_master = dump.DumpMaster(app_server, dump.Options(app_host='mitm.it', app_port=80, app=True))
    thread.start_new_thread(app_master.run, ())
    atexit.register(DNS_cleanup)
    serveDNS(Gateway)
    
