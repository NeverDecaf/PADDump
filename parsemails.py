from datetime import datetime,timedelta
import json
import pytz
from dateutil.tz import tzlocal
import requests
import pickle
import time
import os
import re
#pip install python-dateutil pytz

MONSTER_BOOK={
261:'Super King Metal Dragon',
309:'Super King Gold Dragon',
429:'Queen Metal Dragon',
430:'Queen Gold Dragon',
520:'Snow Globe Dragon Rouge',
521:'Snow Globe Dragon Bleu',
522:'Snow Globe Dragon Vert',
617:'Super King Ruby Dragon',
618:'Super King Sapphire Dragon',
619:'Super King Emerald Dragon',
797:'TAMADRA',
1005:'Snow Globe Dragon Blanc',
1006:'Snow Globe Dragon Noir',
1323:'King DeviTAMA',
1325:'Jewel of Fire',
1326:'Jewel of Water',
1327:'Jewel of Wood',
1328:'Jewel of Light',
1329:'Jewel of Darkness',
1547:'Flampy',
1548:'Bubpy',
1549:'Woodpy',
1550:'Shynpy',
1551:'Badpy',
1702:'Memorial TAMADRA',
2207:'Latent TAMADRA (HP)',
2208:'Latent TAMADRA (ATK)',
2209:'Latent TAMADRA (RCV)',
2210:'Latent TAMADRA (Auto-Heal)',
2211:'Latent TAMADRA (Time Ext)',
2212:'Latent TAMADRA (Fire Res)',
2213:'Latent TAMADRA (Water Res)',
2214:'Latent TAMADRA (Wood Res)',
2215:'Latent TAMADRA (Light Res)',
2216:'Latent TAMADRA (Dark Res)',
2250:'PreDRA (3000MP)',
2251:'Grand PreDRA (10000MP)',
2299:'MP Bag (500MP)',
2300:'MP Bag (500MP)',
2301:'MP Bag (500MP)',
2302:'MP Bag (500MP)',
2303:'MP Bag (500MP)',
9900:'Coins',
9901:'Magic Stone',
9902:'Pal Points',
}
# On a normal system message (type 1) I had a bonus_id of 9999 amt 1, though it has no attachment

amount_case = {
1:          '',
25:         ' (Lv.25)',
40:         ' (Lv.40)',
50:         ' (Lv.50)',
100000:     ' (100M)',
200000:     ' (200M)',
500000:     ' (500M)',
1000000:    ' (1MM)',
2000000:    ' (2MM)',
10000000:   ' (10MM)',
} # Don't need a case for 1000, 2000 as the default is just (xxxx), the MM cases are just here to shorten the text length



# the times for these exceptions should be in PDT (the original pad times)
# no longer needed due to mail update.
##TAMADRA_EXCEPTIONS = (
##    (datetime(2015, 11, 20), datetime(2015, 11, 29, 23, 59, 59), ' +0/30'),
##    (datetime(2015, 11, 30), datetime(2015, 12, 7,  23, 59, 59), ' +9/50'),
##    (datetime(2016, 4, 15), datetime(2016, 4, 24,  23, 59, 59), ' +18'),
##    (datetime(2016, 5, 27), datetime(2016, 6, 5,  23, 59, 59), ' +12'),
##    )

'\+\d+$'

PAD_TZ = pytz.timezone('US/Pacific')
PAD_TZ = pytz.timezone('Etc/GMT+8') # PAD NA has chosen to ignore DST so we'll just use this static timezone until they fix it.
LOCAL_TZ = tzlocal() # you may need to manually put your local timezone here in case your system isn't correct.
# you also need to configure the spreadsheet you are using to match your local timezone (the one specified here)

def get_monster_book():
    try:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'monster_book'),'rb') as f:
            names = pickle.load(f)
            if names['date'] == time.strftime("%x"):
                return names
    except:
        pass
    try:
        r=requests.get('https://www.padherder.com/api/monsters/')
        book = r.json()
    except:
        return MONSTER_BOOK
    
    names = {}
    for mon in book:
        names[mon['id']] = mon['name'] + (' (%iMP)'%mon['monster_points'] if mon['monster_points']>100 else '')
    names['date'] = time.strftime("%x")
    names[9900] = 'Coins'
    names[9901] = 'Magic Stone'
    names[9902] = 'Pal Points'
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'monster_book'),'wb') as f:
        pickle.dump(names,f)
    return names


def parse_mail(mail_json):
    j=json.loads(mail_json)
    res = []
    # keys are id, from, date, fav, sub, type, offered, bonus_id, amount
    # heres roughly what they mean:
    '''
        id: internal server id
        from: player id if friend request or mail, 0 if system
        date: ddmmyyhhmmss date format, PDT
        fav: protected mail (star) (this is just my guess)
        sub: Text that is visible in mailbox
        type: 3 if reward, 0 if friend request, not sure what the others are
        offered: 1 if reward has been claimed, otherwise 0.
        bonus_id: the monster id of the reward contained (with special exceptions for pal points and I assume $$$, though I haven't verified that yet)
        amount: indicates various things, pal point amt, snowglobe level, does not affect + on tamadras though
    '''
    monster_names = get_monster_book()
    for v in [i for i in j[u'mails'] if i[u'type']==3 and i[u'offered']==0]: # filter out everything except type 3 mails (assumed to be rewards), also filter out opened mailed ("offered=1")
        item = '%s'
        if re.search('\+\d+$',v[u'sub']):
            item += v[u'sub'][v[u'sub'].rfind('+'):]
        item = item % monster_names.get(v[u'bonus_id'],'No.'+str(v[u'bonus_id']))
        item += amount_case.get(v[u'amount'],' (%s)'%(v[u'amount'],))
        date = PAD_TZ.localize(datetime.strptime(v[u'date'],'%y%m%d%H%M%S')).astimezone(LOCAL_TZ)#+timezone_shift
        res.append([item,'=FLOOR(NOW()-INDIRECT("RC[1]";0);1)',date.strftime("%m/%d/%y %H:%M:%S")])
    return res



if __name__=='__main__':
    print 'Converting to',datetime.now(LOCAL_TZ).tzname()
    f=open('captured_mail.txt','r')
    a=f.read()
    f.close()
    res = parse_mail(a)
    outstr=''
    for line in res:
        s='\t'.join(line)
        outstr+=s+'\r\n'
    f=open('out.txt','wb')
    f.write(outstr)
    f.close()
