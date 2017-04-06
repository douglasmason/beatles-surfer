import mailbox, email, datetime, copy, json, re, pickle
#from PIL import Image
#from PIL.ExifTags import TAGS

def getMsgText(msg):
    #print msg.keys()
    msgtext = ''
    msgtext_tmp = ''
      
    for part in msg.walk():
      #print "content-type: ",part.get("content-type")
      if part.get_content_type() == "text/plain":
          if len(part.get_payload(decode=True).strip())>0:
            msgtext_tmp = part.get_payload(decode=True).decode('quopri')
          
    for line in msgtext_tmp.split('\n'):
      if line.strip().find(">") != 0:
        msgtext += line+'\n'
    msg_length = len(msgtext)
    if not opt_content:
      msgtext = ''
    return msgtext

opt_content = True


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

f = open(corpus_file,'w')

for msg in mb:
    date_str = msg['Date']
    date = None
    if date_str:
        date_tuple=email.utils.parsedate_tz(date_str)
        if date_tuple:
          date=datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
    msgtext = getMsgText(msg)
    
    if msg['Subject']==None:
        subject_list.append('')
        subject = None
    else:  
        subject_list.append(msg['Subject'])
        subject = msg['Subject'].decode('quopri')
    if msg['From']==None:
        sender_list.append([('','')])
        sender = None
    else:  
        sender_list.append(email.utils.getaddresses([msg['From']]))
        sender = msg['From'].decode('quopri')
        
    #Construct recipient list from To, Cc and Bcc
    rec_list = []
    cc_list = []
    if msg['To'] != None:
      if len(msg['To'])<200:
        rec_list.append(msg['To'].decode('quopri')) 
      else:
        cc_list.append(msg['To'].decode('quopri'))
    if msg['Cc'] != None:
      if len(msg['Cc'])<200:
        rec_list.append(msg['Cc'].decode('quopri')) 
      else:
        cc_list.append(msg['Cc'].decode('quopri'))
    if msg['Bcc'] != None:
      if len(msg['Bcc'])<200:
        rec_list.append(msg['Bcc'].decode('quopri')) 
      else:
        cc_list.append(msg['Bcc'].decode('quopri'))
        
    recipient = ", ".join(rec_list)
    cc_bcc = ", ".join(cc_list)
    msgid += 1
    
    if type(date) == type(None) or len(date_str.strip())==0 or date.year<1980:
      continue
          
    try:
      doc = {}
      #r = "=\n"
      #msgtext = re.sub(r,'',msgtext)
      
      r = "Sent from my [\w ]{5,25}?[^\w ]"
      msgtext = re.sub(r,'',msgtext)
      r = "Sent from my [\w ]{5,25}?$"
      msgtext = re.sub(r,'',msgtext)
      r = "Sent via my [\w ]{5,25}?[^\w ]"
      msgtext = re.sub(r,'',msgtext)
      r = "Sent via my [\w ]{5,25}?$"
      msgtext = re.sub(r,'',msgtext)
      r = "Begin forwarded message:"
      msgtext = re.sub(r,'',msgtext)
      
      r = "https?:\/\/[\w\.\/\%\&\?\=]{1,200}?[\s\"\']"
      msgtext = re.sub(r,'',msgtext)
      
      r = "On [\w:, ]{10,30}? at [0-9:APM ]{3,12}?, [\=\<\>\.\@\w\(\)\-\n\"\' ]{2,70}?wrote:"
      msgtext = re.sub(r,'',msgtext)
      #r = "On [\=\<\>\.,:\@\w\(\)\-\n\/\"\' ]{2,20}? wrote:"
      r = "On [\w\/ ]{2,30}?, [\=\<\>\.\@\w\(\)\-\n\"\' ]{2,70}? wrote:"
      msgtext = re.sub(r,'',msgtext)
      
      
      #msgtext = str.replace(msgtext,'Sent from my iPhone','')
      #msgtext = str.replace(msgtext,'Sent from my iPhatigue','')
      
      snippet = msgtext[0:500]
      
      doc['id']=unicode(str(msgid))
      doc['document']=unicode(msgtext)
      doc['subject']=unicode(subject)
      doc['sender']=unicode(sender)
      doc['recipient']=unicode(recipient)
      doc['cc and bcc']=unicode(cc_bcc)
      doc['date']=unicode(date.strftime('%Y-%m-%dT%H:%M:%S'))
      doc['snippet']=unicode(snippet)
      '''
      doc['id']=(str(msgid))
      doc['document']=(msgtext)
      doc['subject']=(subject)
      doc['sender']=(sender)
      doc['recipient']=(recipient)
      doc['date']=(date.strftime('%Y-%m-%dT%H:%M:%S'))
      doc['snippet']=(snippet)
      '''
      
      #date_list.append(date.strftime('%Y-%m-%dT%H:%M:%S'))
      if ( sender.find("kenneth.lay@enron.com")>-1 or sender.find(" klay@enron.com")>-1 or sender.find("Douglas Mason")>-1 or sender.find("douglasmason") >-1 or sender.find('dmason') > -1):
        doc['outgoing'] = 1
      else:
        doc['outgoing'] = 0
      
      f.write(str(doc)+'\n')
    except:
      continue
    
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
    