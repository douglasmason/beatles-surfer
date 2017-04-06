import os, glob, pickle, email

path = "back-end/enron_mail_20110402/maildir" 
#corpus_file = "/Volumes/Macintosh HD/Users/douglasmason/Documents/Insight/Python WebApp/back-end/enron_corpus.txt"
corpus_file = "back-end/enron_corpus.txt"
pkl_file = "back-end/enron_dict_lsi_index.pkl"
msg_file = "back-end/messages.pkl"
set_file = "back-end/settings.pkl"
index_file = "back-end/enron"

n_msg = 0
msg_string = ''
mb = []
msg_list = []

for infile in glob.glob( os.path.join(path, 'lay-k/*/*.') ):
   #print "current file is: " + infile
   f = open(infile,'r')
   msg_string = f.read()
   msg = email.message_from_string(msg_string)
   mb.append(msg)
   msg_string = ''
   n_msg += 1
   if n_msg>=10000:
     break

print "total number of messages: ", n_msg

min_date = 0
max_date = 0
opt_lyrics = 0

f = open(msg_file,'wb')
pickle.dump(mb,f)
f.close()
f = open(set_file,'wb')
pickle.dump((corpus_file,pkl_file,index_file,min_date,max_date,opt_lyrics),f)
f.close()