import nltk
from gensim import corpora, models, similarities
import json, ast
import pickle
import sys
import math, re, random
import numpy as np
import cProfile

set_file = "back-end/settings.pkl"
f = open(set_file,'rb')
(corpus_file,pkl_file,index_file,min_date,max_date,opt_lyrics) = pickle.load(f) 
f.close()

if opt_lyrics == 0:
  all_str = "All Kenneth Lay Emails"
else: 
  all_str = "The Beatles"
  
def cleanDoc(doc):
    stopset = set(nltk.corpus.stopwords.words('english'))
    stemmer = nltk.PorterStemmer()
    r = "\<[\w\/ \"\'\=:\.\@]{1,100}\>"
    doc = re.sub(r,'',doc)
    doc = re.sub("[^\s]{17,}",'',doc)
    tokens = nltk.regexp_tokenize(doc, r"[a-zA-Z]+")
    clean = [token.lower() for token in tokens if token.lower() not in stopset and (len(token) > 2 and len(token)<15)]
    final = [stemmer.stem(word) for word in clean]
    if len(final)==0: final = ['']
    return final

def GetDocFromCorpus(index1):
    global corpus_index, opt_lyrics, corpus_file
    file = corpus_file
    f = open(file,'r')
    f.seek(corpus_index[index1])
    doc = ast.literal_eval(f.readline().strip())
    doc_string = doc['document']+(doc['subject']+'\n')*3
    return doc_string, doc

f = open(pkl_file,'rb')
(tfidf,dictionary,lsi,sim_index) = pickle.load(f) #be careful, there's a namespace conflict with the variable index
f.close()



file = corpus_file

corpus_index = {}
sim_to_id = []
doc_string = ''
f = open(file,'r')
prev_index = 0
import ast
while 1:
  try:
    cur_index = f.tell()
    line = f.readline()
    doc = ast.literal_eval(line.strip())
    corpus_index[int(doc['id'])] = cur_index
    sim_to_id.append(int(doc['id']))
  except:
    break

f.close()

def OutputJSON(query="",opt_fuzzy=0,id=-1,query_display="",brushmin="",brushmax="",incoming=1,outgoing=1):
  global sim_to_id, corpus_index, all_str, tfidf, dictionary, min_date, max_date
  if len(query)==0:
    query = all_str
  doc = query #get query from form
  if len(query_display)==0:
    query_display = query
  
  doc_bow = dictionary.doc2bow(cleanDoc(doc))
  doc_lsi = lsi[doc_bow] # convert the query to LSI space
  doc_lsi_array = np.array([item[1] for item in doc_lsi])
  
  sims = sim_index[doc_lsi] # perform a similarity query against the corpus
  sims = sorted(enumerate(sims), key=lambda item: -item[1])
  #print "sim_to_id:",sim_to_id
  #print "corpus_index:",corpus_index
  doc_match, metadata = GetDocFromCorpus(sim_to_id[sims[0][0]])
  
  output_json = []  
  
  if query.lower().strip() == all_str.lower().strip():
    sims = [(ind,0.2+random.random()*0.000001) for ind in range(len(sim_to_id))]
    print "number of documents:", len(sim_to_id)
    max_msg = 100
  else:
    max_msg = 30
  
  sims = sorted(sims,key=lambda sim: sim[1],reverse=True)
  n_msg = 0
  
  for sim in sims:
    if sim[1]<0.05:
      continue
    n_msg += 1
    if n_msg>max_msg: break
    doc_match, metadata = GetDocFromCorpus(sim_to_id[sim[0]])
    tmp_json = metadata
    '''
    print "i,c,v: ", incoming, outgoing, metadata['outgoing']
    if incoming==0 and metadata['outgoing']==0:
      print 'hit'
      continue
    if outgoing==0 and metadata['outgoing']==1:
      print 'hit'
      continue
    '''
    metadata['text'] = doc_match
    metadata['similarity'] = sim[1]
    metadata['plotdate'] = metadata['date']
    
#    if metadata.has_key('document'):
#      metadata['document'] = None
#    if not metadata.has_key('date'):
#      continue
    output_json.append(metadata)
  
  if len(sims)==0:
    sorted_json = {'outgoing': 0, 'sender': u'No Result', 'snippet': u"No result", 'cc and bcc': u'', 'date': u'1970-05-08T00:00:00', 'document': u"No Result", 'recipient': u'The Beatles', 'id': u'0', 'subject': u'Null'}
  
  import datetime
  sorted_json = sorted(output_json, key=lambda item: item['similarity'],reverse=True)
  if len(sorted_json)>max_msg:
    output_json = sorted_json[:max_msg]
  
  
  if len(sorted_json) == 0:  
    mid_date = datetime.datetime.strftime(min_date+(max_date-min_date)/2,'%Y-%m-%dT%H:%M:%S')
    tmp = json.dumps([{'outgoing': 0, 'sender': u'No Result', 'snippet': u"No result", 'cc and bcc': u'', 'date': mid_date, 'plotdate':  mid_date, 'similarity': 0.0, 'document': u"No Result", 'recipient': u'Null', 'id': u'0', 'subject': u'Null'}, {'outgoing': 0, 'sender': u'No Result', 'snippet': u"No result", 'cc and bcc': u'', 'date':  mid_date, 'plotdate':  mid_date, 'similarity': 0.0, 'document': u"No Result", 'recipient': u'Null', 'id': u'0', 'subject': u'Null'}])
    f = open('static/test_data.js','w')
    f.write("var data = "+tmp+";")
    f.close()
    
    if id>-1:
      doc = ''
    tmp = json.dumps({  'query' : "No matches for \""+doc+"\"", 'id': id, 'brushmin': brushmin, 'brushmax':brushmax, 'incoming': incoming, 'outgoing': outgoing, 'min_date': datetime.datetime.strftime(min_date,'%Y-%m-%dT%H:%M:%SZ'), 'max_date': datetime.datetime.strftime(max_date,'%Y-%m-%dT%H:%M:%SZ'), 'opt_lyrics':opt_lyrics, 'opt_null': 1})
    f = open('static/test_data_header.js','w')
    f.write("var header = "+tmp+";")
    f.close()
    return
  
  sorted_json = sorted(output_json, key=lambda item: datetime.datetime.strptime(item['date'],'%Y-%m-%dT%H:%M:%S'),reverse=False)
  
  if opt_lyrics:
    nbin = 100
  else:
    nbin = 500
  date_range = datetime.datetime.strptime(sorted_json[0]['date'],'%Y-%m-%dT%H:%M:%S')-datetime.datetime.strptime(sorted_json[-1]['date'],'%Y-%m-%dT%H:%M:%S')
  date_bin = date_range/nbin
  
  datelist = [datetime.datetime.strptime(msg['date'],'%Y-%m-%dT%H:%M:%S') for msg in sorted_json]
  
  date_min = datelist[0]
  date_max = datelist[-1]
  bins = {}
  for ind, date in enumerate(datelist):
    #print date_bin.total_seconds()
    total_seconds = date_bin.days * 86400 + date_bin.seconds
    range_seconds = (date-date_min).days * 86400 + (date-date_min).seconds
    if abs(total_seconds)>0:
      bin_tmp = int(math.floor(range_seconds/float(total_seconds)))-1
    else:
      bin_tmp = 1
    if bins.has_key(bin_tmp):
      bins[bin_tmp].append(ind)
    else:
      bins[bin_tmp] = [ind]
  
  for bin, inds in bins.items():
    ndates = len(inds)
    for num, ind in enumerate(inds):
       datelist[ind] = date_min+bin*date_bin+(1+ndates-num)*date_bin/(ndates+2)
  
  for ind in range(len(datelist)):
    sorted_json[ind]['plotdate'] = datetime.datetime.strftime(datelist[ind],'%Y-%m-%dT%H:%M:%S')

  sorted_json = sorted(output_json, key=lambda item: datetime.datetime.strptime(item['plotdate'],'%Y-%m-%dT%H:%M:%S'),reverse=False)
  
  hi_rank_words_in_query = dict(sorted(tfidf[doc_bow],key=lambda item: item[1],reverse=True))
  overlapping_words = []
  keep_doc = set()  
  for doc_num, cur_doc_dict in enumerate(sorted_json):
    if query != all_str:
      dp_el = []      
      if opt_lyrics == 0:
        pass
      else:
        doc_string = cur_doc_dict['document']+(cur_doc_dict['subject']+'\n')*3
      cur_doc_bow = dictionary.doc2bow(cleanDoc(doc_string))
      hi_rank_words_in_cur_doc = sorted(tfidf[cur_doc_bow],key=lambda item: item[1],reverse=True)
      for pair in hi_rank_words_in_cur_doc:
        #continue
        word = pair[0]
        rank = pair[1]
        
        if opt_fuzzy==0 and word in hi_rank_words_in_query:
          keep_doc.add(doc_num)
        elif opt_fuzzy==1:
          keep_doc.add(doc_num)
        else:
          continue
        
        #conduct cosine similarity between each word and the query
        word_lsi = lsi[[(word,1)]] #Need a list of tuples for input
        word_lsi_array = np.array([item[1] for item in word_lsi])
        
        dp = word_sim_to_query = np.dot(word_lsi_array,doc_lsi_array)/np.sqrt(np.dot(word_lsi_array,word_lsi_array)*np.dot(doc_lsi_array,doc_lsi_array))
        
        if word_sim_to_query>0.1:
          dp_el.append((word,dp))
        if len(dp_el)>20:
          break
        #print word, rank
        
      dp_el = sorted(dp_el,key=lambda item: item[1], reverse=True)
      words_n_sims = []
      unique_words_n_sims = []
      actual_words_in_cur_doc = (doc_string).split()
      tokens_in_cur_doc = [cleanDoc(item)[0] for item in actual_words_in_cur_doc]
      token2word = dict()
      for token,tmp_word in zip(tokens_in_cur_doc,actual_words_in_cur_doc):
        tmp_word = re.sub("^[^A-Za-z0-9]+","",tmp_word.strip())
        tmp_word = re.sub("[^A-Za-z0-9]+$","",tmp_word.strip())
        tmp_word = re.sub("[\(\)\/\\\@\"]","",tmp_word)
        if token in token2word:
          if tmp_word not in token2word[token]:
            token2word[token].append(tmp_word)
        else:
          token2word[token] = [tmp_word]
          
      sim_cnt = 0
      for wordid,rank in dp_el:
        token = dictionary.id2token[wordid]
        if len(token)>0 and token in token2word: 
          sim_cnt += 1
          if sim_cnt > 10: break
          for tmp_word in [token2word[token][0]]:
            tmp_word = re.sub("^[^A-Za-z0-9]+","",tmp_word.strip())
            tmp_word = re.sub("[^A-Za-z0-9]+$","",tmp_word.strip())
            unique_words_n_sims.append((tmp_word,rank))
          iter_words = sorted(token2word[token],key=lambda item:len(item),reverse=True)
          for tmp_word in iter_words:
            tmp_word = re.sub("^[^A-Za-z0-9]+","",tmp_word.strip())
            tmp_word = re.sub("[^A-Za-z0-9]+$","",tmp_word.strip())
            words_n_sims.append((tmp_word,rank))
            
      docid=str(int(cur_doc_dict['id']))
      word_links = []
      for word, sim_tmp in unique_words_n_sims:
        if sim_tmp>0.5:
          word_links.append("<big><b><a href=\"/?query="+word+"&docid="+docid+"\">"+word+"</a></b></big>")
        elif sim_tmp>0.25:
          word_links.append("<a href=\"/?query="+word+"&docid="+docid+"\">"+word+"</a>")
        elif sim_tmp>0:
          word_links.append("<small><a href=\"/?query="+word+"&docid="+docid+"\">"+word+"</a></small>")
      for word, sim_tmp in words_n_sims:
        if sim_tmp>0.5:
          cur_doc_dict['subject'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<big><b><a href='/?query=\2&docid="+docid+r"'>\2</a></b></big>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<big><b><a href='/?query=\2&docid="+docid+r"'>\2</a></b></big>\3",cur_doc_dict['document'])
          cur_doc_dict['subject'] = re.sub("^()("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<big><b><a href='/?query=\2&docid="+docid+r"'>\2</a></b></big>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("^()("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<big><b><a href='/?query=\2&docid="+docid+r"'>\2</a></b></big>\3",cur_doc_dict['document'])
          cur_doc_dict['subject'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")()$",
          r"\1<big><b><a href='/?query=\2&docid="+docid+r"'>\2</a></b></big>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")()$",
          r"\1<big><b><a href='/?query=\2&docid="+docid+r"'>\2</a></b></big>\3",cur_doc_dict['document'])
        elif sim_tmp>0.25:
          cur_doc_dict['subject'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<a href='/?query=\2&docid="+docid+r"'>\2</a>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<a href='/?query=\2&docid="+docid+r"'>\2</a>\3",cur_doc_dict['document'])
          cur_doc_dict['subject'] = re.sub("^()("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<a href='/?query=\2&docid="+docid+r"'>\2</a>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("^()("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<a href='/?query=\2&docid="+docid+r"'>\2</a>\3",cur_doc_dict['document'])
          cur_doc_dict['subject'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")()$",
          r"\1<a href='/?query=\2&docid="+docid+r"'>\2</a>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")()$",
          r"\1<a href='/?query=\2&docid="+docid+r"'>\2</a>\3",cur_doc_dict['document'])
        elif sim_tmp>0:
          cur_doc_dict['subject'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<small><a href='/?query=\2&docid="+docid+r"'>\2</a></small>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<small><a href='/?query=\2&docid="+docid+r"'>\2</a></small>\3",cur_doc_dict['document'])
          cur_doc_dict['subject'] = re.sub("^()("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<small><a href='/?query=\2&docid="+docid+r"'>\2</a></small>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("^()("+word+")([^a-zA-Z0-9\<\"])",
          r"\1<small><a href='/?query=\2&docid="+docid+r"'>\2</a></small>\3",cur_doc_dict['document'])
          cur_doc_dict['subject'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")()$",
          r"\1<small><a href='/?query=\2&docid="+docid+r"'>\2</a></small>\3",cur_doc_dict['subject'])
          cur_doc_dict['document'] = re.sub("([^a-zA-Z0-9\>\"\=])("+word+")()$",
          r"\1<small><a href='/?query=\2&docid="+docid+r"'>\2</a></small>\3",cur_doc_dict['document'])
      word_links = [word.lower() for word in word_links]
      if len(words_n_sims)>0:
        overlapping_words = ", ".join(word_links)
      else:
        overlapping_words = "no results"
      cur_doc_dict['similar_words'] = overlapping_words
    else:
      cur_doc_dict['similar_words'] = "Not applicable"
      keep_doc = set(range(len(sorted_json)))
    cur_doc_dict['plotdate'] += "Z"
    cur_doc_dict['date'] += "Z"
  
  sorted_json = [i for j, i in enumerate(sorted_json) if j in keep_doc]
  
  tmp = json.dumps(ast.literal_eval(str(sorted_json)))
  f = open('static/test_data.js','w')
  f.write("var data = "+tmp+";")
  f.close()
  
  doc = query_display
  if len(doc)>25:
    doc = doc[:25]+'...'
  tmp = json.dumps({ 'query' : doc, 'id': id, 'brushmin': brushmin, 'brushmax':brushmax, 'incoming': incoming, 'outgoing': outgoing, 'min_date': datetime.datetime.strftime(min_date,'%Y-%m-%dT%H:%M:%SZ'), 'max_date': datetime.datetime.strftime(max_date,'%Y-%m-%dT%H:%M:%SZ'), 'opt_lyrics': opt_lyrics, 'opt_null': 1})
  f = open('static/test_data_header.js','w')
  f.write("var header = "+tmp+";")
  f.close()


########
#
# START Web.py stuff
#
########

import web
from web import form

render = web.template.render('templates/')

urls = ('/', 'index')
app = web.application(urls, globals())

if opt_lyrics:
  search_txt = "Search Beatles lyrics for:"
else:
  search_txt = "Search Enron email for:"
  
        
class index: 
    def GET(self):
      from web import form
      
      global form_str, myform
      something_worked = 0
      brushmin = ''
      brushmax = ''
      incoming = 1
      outgoing = 1
      searchbox_txt = ''
      query_display = ''
      opt_fuzzy=0
      try:
        incoming = int(web.input().incoming)
      except:
        pass
      try:
        outgoing = int(web.input().outgoing)
      except:
        pass
      if incoming==0 and outgoing==0:
        incoming = 1
        outgoing = 1
      try:
        brushmin = web.input().brushmin
        brushmax= web.input().brushmax
      except:
        pass
      try:
        docid = int(web.input().docid)
      except:
        docid=-1
      try: #Do query first before docid query
        if something_worked==0:
          query = web.input().query
          something_worked = 1
          searchbox_txt = query
          opt_fuzzy = 0
      except:
        pass
      try:
        if something_worked==0:
          query, query_metadata = GetDocFromCorpus(docid)
          something_worked = 1
          query_display=query_metadata['subject']
          opt_fuzzy = 1
      except:
        pass
      if something_worked == 0:
        query = all_str
        
      OutputJSON(query, id=docid, opt_fuzzy=opt_fuzzy, query_display=query_display, brushmin=brushmin, brushmax=brushmax, incoming=incoming, outgoing=outgoing)
        
      myform = form.Form( 
      form.Textbox(search_txt,style="width:400px;",pre=search_txt,value=searchbox_txt),
      form.Button("Visualize"),)

      form = myform()
      # make sure you create a copy of the form by calling it (line above)
      # Otherwise changes will appear globally
      #return render.formtest(form)
      #form_str = search_txt + " " + myform[search_txt].render() + myform["Visualize"].render()
      form_str = myform[search_txt].render()
      return render.formtest(form_str)
      #return myform[search_txt].render() + myform["Visualize"].render()
      #render.formtest(form[search_txt])
      #render.formtest(form["Visualize"])
    
    def POST(self): 
      #try:
        global myform
      
        form = myform() 
        brushmin = ""
        brushmax = ""
        try:
          brushmin = web.input().brushmin
          brushmax= web.input().brushmax
        except:
          pass
        print repr(form[search_txt].value)
        if not form.validates():  #Must validate form before checking value
            query = all_str
        else:
            query = form[search_txt].value
       
        raise web.seeother('/?query='+query)#+'&brushmin='+brushmin+"&brushmax="+brushmax)

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
    
    
########
#
# END Web.py stuff
#
########