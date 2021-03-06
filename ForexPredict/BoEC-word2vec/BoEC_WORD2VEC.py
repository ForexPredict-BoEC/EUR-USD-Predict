from gensim.models import Word2Vec
import gensim
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
import re
from sklearn.cluster import KMeans
import numpy as np

#step 1 build word2vec model 
nltk.download('punkt')

#preprocess step for removing tags and numberes
def preprocess_text(sen):
    # Removing html tags
    sentence = remove_tags(sen)

    # Remove punctuations and numbers
    sentence = re.sub('[^a-zA-Z]', ' ', sentence)

    # Single character removal
    sentence = re.sub(r"\s+[a-zA-Z]\s+", ' ', sentence)

    # Removing multiple spaces
    sentence = re.sub(r'\s+', ' ', sentence)

    return sentence
TAG_RE = re.compile(r'<[^>]+>')


#remove tags regular expression
def remove_tags(text):
    return TAG_RE.sub('', text)

#for preparing courpus we eliminate numbers and tags 
def prepareCourpus(corpusPath):
    dataframe = pd.read_excel(corpusPath)
    for item  in dataframe.iterrows():
        text = item[1]['title'] +'.' +item[1]['articleBody']
        sentences = sent_tokenize(text)
        preprocess_sent = [preprocess_text(sen) for sen in sentences]
        for item in preprocess_sent:
            text = text + item
    return text

#for word2vec model we use Gensim library 
def createW2VModel(path , embeddingDim = 210 , windowSize = 3):
    text = prepareCourpus(path)
    model = Word2Vec(text, size=embeddingDim, window=windowSize , min_count=3, workers=4 )
    model.save('forex.embeddings');
    model.wv.save_word2vec_format('ForexNews.txt', binary=False)
    return model

#create latent concept space
def conceptModeling(w2vModel , conceptNumbers , conceptPath):
    vectors = w2vModel.wv
    X = w2vModel[w2vModel.wv.vocab]
    kmeans_model = KMeans(conceptNumbers, init='k-means++', max_iter=100)  
    Z = kmeans_model.fit(X)
    labels=kmeans_model.labels_.tolist()
    kmeans_model.fit_predict(X)
    words = list(w2vModel.wv.vocab)
    clusterWords = {'word':words,'cluster':labels}
    clusterWordsData = pd.DataFrame(clusterWords)
    clusterWordsData.to_excel(conceptPath)
    return


def tokenize(text):
    text = preprocess_text(text)
    words = word_tokenize(text)
    return words
    
#create embedding vector for news documents
def BoEC_w2v(doc,conceptNumbers,clusters , topK):
    if doc.loc['articleBody'] :
         text = doc['title'] + doc.loc['articleBody']
    else :
         text = doc['title']
    
    vec = pd.Series(np.zeros(conceptNumbers))
    words = tokenize(text)
    for word  in words:
            vec [clusters[clusters['word'] == word]['cluster']] = vec [clusters[clusters['word'] == word]['cluster']] +1
    if topK > 0:
        expandVec = titleExpansion( doc['title'] , topK ,clusters)
        extende_vec  = np.add(vec ,expandVec)    
    else:
        extende_vec = vec
    return extende_vec

# title expansion subroutine
def titleExpansion( docTitle , topK ,clusters , conceptNumbers ,w2vModel ):
    
    expanded_words = tokenize (docTitle)
    vec = pd.Series(np.zeros(conceptNumbers))
    
    for word in expanded_words:
        if word in w2vModel.wv.vocab :
           synset = w2vModel.most_similar(word, topn = topK)
          
           for s in synset:
               
               vec [clusters[clusters['word'] == s[0]]['cluster']] = vec [clusters[clusters['word'] == s[0]]['cluster']] +1
      
    return vec

#BoEC-word2vec create embedded document vectors for all of news in corpus
def BoEC_word2vec (corpusPath , outputFileName ,conceptNumbers ,topK =7 , embeddingDim = 100 , windowSize = 3 ):
    
    w2vModel = createW2VModel(corpusPath , embeddingDim = 210 , windowSize = 3)
    conceptModeling(w2vModel , conceptNumbers , 'topicInfo.xlsx')
    dfClusters = pd.read_excel('topicInfo.xlsx')
    dfDocuments = pd.read_excel(corpusPath)
    df = pd.Series(np.zeros(dfDocuments['title'].count()))
   
    for rowIndex,row in dfDocuments.iterrows():
          vec = BoEC_w2v(row['title'], conceptNumbers, dfClusters, topK )
          df[rowIndex] =  str([w for w in vec])
    
    dfDocuments['vector'] = df
    dfDocuments.to_excel(outputFileName)      
    return dfDocument


    

    
    

    


