import mailbox, email, datetime, copy, json, re, pickle, sys, datetime, time
sys.setrecursionlimit(100000)
#from PIL import Image
#from PIL.ExifTags import TAGS

#Load messages
msg_file = "back-end/messages.pkl"
set_file = "back-end/settings.pkl"
f = open(msg_file,'rb')
mb = pickle.load(f) #be careful, there's a namespace conflict with the variable index
f.close()
f = open(set_file,'rb')
(corpus_file,pkl_file,index_file,min_date,max_date,opt_lyrics) = pickle.load(f) #be careful, there's a namespace conflict with the variable index
f.close()

subject_list = []
sender_list = []
recipient_list = []
content_list = []
length_list = []
date_list = []
msgtext = ''
msgid = -1


file = "Beatles Lyrics/singles.txt"
f = open(file,'r')
singles_str = f.read()
f.close()
singles_table = singles_str.split('\r')
singles = []
for row in singles_table:
  columns = row.split('\t')
  names = columns[0].split('/')
  date = datetime.datetime.strptime(columns[1].strip()[1:-1],"%Y, %B %d")
  singles.append((names[0].strip(),date,columns[0].strip()))
  singles.append((names[1].strip(),date,columns[0].strip()))

f = open(corpus_file,'w')

for msg in mb:
    date = None
    try:
      date = msg['date']
    except:
      pass
    msgtext = msg['text']
    subject = msg['title']
    recipient = "The Beatles" #Later specify McCartney/Lennon
    sender = msg['album'] 
    cc_bcc = "" #dunno what to do with this one
    msgid += 1
    
    if sender.find("Beatles VI")>-1:
      sender = ("Help!")
    if sender.find("Yesterday")>-1:
      sender = ("Revolver")
    if sender.find("Something New")>-1:
      sender = ("A Hard Day's Night")
    if sender.find("Meet the Beatles")>-1:
      sender = ("A Hard Day's Night")
    if sender.find("Beatles '65")>-1:
      sender = ("Beatles For Sale")
    if sender.find("Beatles 65")>-1:
      sender = ("Beatles For Sale")
    
    
    if sender.find("Help!")>-1:
      date = datetime.date(1965,8,6)
    elif sender.lower().find("with the beatles")>-1:
      date = datetime.date(1963,11,22)
    elif sender.find("Please Please Me")>-1:
      date = datetime.date(1963,3,22)
    elif sender.find("A Hard Day's Night")>-1:
      date = datetime.date(1964,7,10)
    elif sender.lower().find("beatles for sale")>-1:
      date = datetime.date(1964,12,4)
    elif sender.find("Rubber Soul")>-1:
      date = datetime.date(1965,12,3)
    elif sender.find("Revolver")>-1:
      date = datetime.date(1966,8,5)
    elif sender.find("Lonely Hearts Club Band")>-1:
      date = datetime.date(1967,6,1)
    elif sender.find("The Beatles")>-1 and sender.find("The Beatles' Second Album")==-1 and subject.find("With")==-1:
      date = datetime.date(1968,11,12)
    elif sender.find("Yellow Submarine")>-1:
      date = datetime.date(1969,1,17)
    elif sender.find("Abbey Road")>-1:
      date = datetime.date(1969,9,26)
    elif sender.find("Let It Be")>-1:
      date = datetime.date(1970,5,8)
    else:
      sender = "Single"
      
    for single in singles:
      if single[0].lower().find(subject.lower())>-1:
        date = single[1]
        sender = single[2]
    
    if type(date) == type(None) or date.year>1970:
      continue
    
    date = datetime.datetime.combine(date, datetime.time())
    
    #try:
    doc = {}
    
    snippet = msgtext[0:min(500,len(msgtext)-1)]
    
    print subject
    
    doc['id']=unicode(str(msgid))
    doc['document']=unicode(msgtext)
    doc['subject']=unicode(subject)
    doc['sender']=unicode(sender)
    doc['recipient']=unicode(recipient)
    doc['cc and bcc']=unicode(cc_bcc)
    doc['date']=unicode(datetime.datetime.strftime(date,'%Y-%m-%dT%H:%M:%S'))
    doc['snippet']=unicode(snippet)
    
    #date_list.append(date.strftime('%Y-%m-%dT%H:%M:%S'))
    doc['outgoing'] = 0
    
    f.write(str(doc)+'\n')
    #except:
     # continue
    
    #print date.year
    date_list.append(date)


f.close()

date_list = sorted(date_list)
min_date = date_list[0]
max_date = date_list[-1]

nbin = 100
date_range = max_date-min_date
date_bin = date_range/nbin
min_date += -date_bin
max_date += date_bin


f = open(set_file,'wb')
pickle.dump((corpus_file,pkl_file,index_file,min_date,max_date,opt_lyrics),f)
f.close()
    