import pickle, email, re, sys
sys.setrecursionlimit(100000)

json_file = "Beatles Lyrics/lyrics_smaller.pkl"
#corpus_file = "/Volumes/Macintosh HD/Users/douglasmason/Documents/Insight/Python WebApp/back-end/corpus.txt"
corpus_file = "back-end/beatles_corpus.txt"
pkl_file = "back-end/beatles_dict_lsi_index.pkl"
msg_file = "back-end/messages.pkl"
set_file = "back-end/settings.pkl"
index_file = "back-end/beatles"

n_msg = 0
msg_string = ''
mb = []
msg_list = []


f = open(json_file,'rb')
mb = pickle.load(f) 
f.close()


min_date = 0
max_date = 0
opt_lyrics = 1

f = open(msg_file,'wb')
pickle.dump(mb,f)
f.close()
f = open(set_file,'wb')
pickle.dump((corpus_file,pkl_file,index_file,min_date,max_date,opt_lyrics),f)
f.close()