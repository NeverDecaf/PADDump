"""http://code.activestate.com/recipes/491264-mini-fake-dns-server/"""
from __future__ import print_function

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
##                evt = custom_events.wxStatusEvent(message="Got box data, processing...")            
##                wx.PostEvent(self.status_ctrl,evt)
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
##                thread.start_new_thread(padherder_sync.do_sync, (content, self.status_ctrl, self.region))
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
                
##                mails = parse_mail(content)
##                mails.reverse()
                print("Got mail data, processing...")
##                evt = custom_events.wxMailEvent(mails=mails)
##                wx.PostEvent(self.mail_tab, evt)
##                evt = custom_events.wxStatusEvent(message="Got mail data, processing...")            
##                wx.PostEvent(self.status_ctrl,evt)
                
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
