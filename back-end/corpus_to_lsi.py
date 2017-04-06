import mailbox, email, nltk, ast, sys, pickle, re

set_file = "back-end/settings.pkl"

set_file = "back-end/settings.pkl"
f = open(set_file,'rb')
(corpus_file,pkl_file,index_file,min_date,max_date,opt_lyrics) = pickle.load(f) 
f.close()

def cleanDoc(doc):
    stopset = set(nltk.corpus.stopwords.words('english'))
    stemmer = nltk.PorterStemmer()
    r = "\<[\w\/ \"\'\=:\.\@]{1,100}\>"
    doc = re.sub(r,'',doc)
    doc = re.sub("[^\s]{17,}",'',doc)
    tokens = nltk.regexp_tokenize(doc, r"[a-zA-Z]+")
    clean = [token.lower() for token in tokens if token.lower() not in stopset and (len(token) > 2 and len(token)<15)]
    try:
      final = [unicode(stemmer.stem(word)) for word in clean]
    except:
      final = []
    return final

class MyCorpusDocs(object):
  global corpus_file, opt_lyrics
  def __iter__(self):
    import ast
    file = corpus_file
    #print file
    f = open(file,'r')
    while 1:
      #print f.tell()
      try:
        doc = ast.literal_eval(f.readline().strip())
        doc_string = doc['document']+(doc['subject']+'\n')*3
        yield cleanDoc(doc_string)
      except:
        break


class MyCorpus(object):
  def __iter__(self):
    for doc in MyCorpusDocs():
      yield dictionary.doc2bow(doc)

def GetSimsFromLSI(doc,dictionary,lsi,index):
  doc_bow = dictionary.doc2bow(cleanDoc(doc))
  doc_lsi = lsi[doc_bow] # convert the query to LSI space
  sims = index[doc_lsi] # perform a similarity query against the corpus
  #print list(enumerate(sims)) # print (document_number, document_similarity) 2-tuples
  sims = sorted(enumerate(sims), key=lambda item: -item[1])
  #print sims[1:10] # print sorted (document number, similarity score) 2-tuples
  #print sims[-10:-1] # print sorted (document number, similarity score) 2-tuples
  
  return sims
  
  #corpus_index = GetCorpusIndex()
  #print '###########BEST MATCH###############\n'
  #print GetDocFromCorpus(corpus_index[sims[0][0]])
  #print '##########WORST MATCH###############\n'
  #print GetDocFromCorpus(corpus_index[sims[-1][0]])

def GetJSONFromLSI(doc,corpus_index,dictionary,lsi,index):
  sims = GetSimsFromLSI(doc,dictionary,lsi,index)
  for sim in sims:
    doc = GetDocFromCorpus(corpus_index[sim[0]])

#######################
##EXAMPLE
#######################


import nltk
from gensim import corpora, models, similarities

nfeatures = 300

dictionary = corpora.Dictionary(doc for doc in MyCorpusDocs())
corpus = MyCorpus()
print dictionary

#Print vectors that describe each piece of the corpus
#for doc in corpus:
#  print dictionary.doc2bow(doc)

if opt_lyrics == 0:
  stoplist = stopset = set(nltk.corpus.stopwords.words('english'))#set('for a of the and to in'.split())
  stoplist.add("re")
  stoplist.add("fwd")
  stop_ids = [dictionary.token2id[stopword] for stopword in stoplist
              if stopword in dictionary.token2id]
  once_ids = [tokenid for tokenid, docfreq in dictionary.dfs.iteritems() if docfreq < 2]
  dictionary.filter_tokens(stop_ids + once_ids) # remove stop words and words that appear only once or twice
  print "filtered dictionary"
  print dictionary
else:
  once_ids = [tokenid for tokenid, docfreq in dictionary.dfs.iteritems() if docfreq < 2]
  dictionary.filter_tokens(once_ids) # remove stop words and words that appear only once or twice
  print "filtered dictionary"
  print dictionary

#Get list of common words in dictionary
token_list = []
for tokenid, docfreq in dictionary.dfs.iteritems():
  token_list.append({'token': dictionary[tokenid], 'docfreq': docfreq})

#plot them
tmp = sorted(token_list, key = lambda token: token['docfreq']) #Here the lambda selects an element from the list and temporarily refers to as token
df_list = []
for tokenthing in tmp:
  df_list.append(tokenthing['docfreq'])

'''
import matplotlib
import matplotlib.pyplot as pyplot
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange
fig = pyplot.figure()
ax = fig.add_subplot(111)
ax.scatter(range(len(df_list)),df_list)
for ind, couplet in enumerate(tmp):
  ax.text(ind,couplet['docfreq'],couplet['token'])

pyplot.semilogy()
pyplot.show()

import numpy as np
num_occur = np.zeros(1000)
for df in df_list:
  num_occur[df] += 1

#pyplot.hist(np.log(df_list),100)
pyplot.scatter(range(len(num_occur)),num_occur)
pyplot.semilogy()
pyplot.show()
'''

#dictionary.compactify() # remove gaps in id sequence after words that were removed
#Actually, this causes errors down the line
#print dictionary


tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]
lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=nfeatures) # initialize an LSI transformation
#corpus_lsi = lsi[corpus_tfidf] # create a double wrapper over the original corpus: bow->tfidf->fold-in-lsi

#lsi.show_topics()
#for doc in corpus_lsi: # both bow->tfidf and tfidf->lsi transformations are actually executed here, on the fly
#    print doc

####
# More model choices, although the tfidf+lsi is the preferred since it can be updated
####

#model = tfidfmodel.TfidfModel(bow_corpus, normalize=True)
#model = lsimodel.LsiModel(tfidf_corpus, id2word=dictionary, num_topics=300)
#model = rpmodel.RpModel(tfidf_corpus, num_topics=500)
#model = ldamodel.LdaModel(bow_corpus, id2word=dictionary, num_topics=100)
#model = hdpmodel.HdpModel(bow_corpus, id2word=dictionary)

#For adding more documents to the LSI model without having to recalculate it
#model.add_documents(another_tfidf_corpus) # now LSI has been trained on tfidf_corpus + another_tfidf_corpus
#lsi_vec = model[tfidf_vec] # convert some new document into the LSI space, without affecting the model

####
# End choices
####

index = similarities.Similarity(index_file,lsi[corpus],num_features=nfeatures) # transform 
#index = similarities.MatrixSimilarity(lsi[corpus],num_features=nfeatures) # transform 
#corpus to LSI space and index it
#FOR SOME REASON, USING ANY OTHER DIRECTORY FOR THE PREVIOUS LINE CAUSES ERRORS REGARDING A .0 FILE!

#index = similarities.MatrixSimilarity(lsi[corpus],num_features=nfeatures)


import pickle
f = open(pkl_file,'wb')
pickle.dump((tfidf,dictionary,lsi,index),f)
f.close()

###THIS STUFF BELOW IS OPTIONAL
'''
import sys
doc = sys.argv[1]
sims = GetSimsFromLSI(doc,dictionary,lsi,index)
corpus_index = GetCorpusIndex()
doc_match, metadata = GetDocFromCorpus(corpus_index[sims[0][0]],corpus_index[sims[0][0]+1])

output_json = []  
for sim in sims:
  if sim[1]<0.1:
    continue
  if sim[0]+1>=len(corpus_index):
    doc_match, metadata = GetDocFromCorpus(corpus_index[sim[0]],0)
  else:
    doc_match, metadata = GetDocFromCorpus(corpus_index[sim[0]],corpus_index[sim[0]+1])
  tmp_json = metadata
  metadata['text'] = doc_match
  metadata['similarity'] = sim[1]
  if not metadata.has_key('date'):
    continue
  output_json.append(metadata)


sorted_json = sorted(output_json, key=lambda item: item['date'],reverse=False)

'''



