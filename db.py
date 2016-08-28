import pymongo
from nltk.util import AbstractLazySequence, LazyMap, LazyConcatenation
from nltk.tokenize import TreebankWordTokenizer
from nltk.data import LazyLoader

#start mongodb connect
class MongoDBLazySequence(AbstractLazySequence):

  def __init__(self, host, port, db, collection, field):
    self.conn = pymongo.MongoClient(host, port)
    self.collection = self.conn[db][collection]
    self.field = field

  def get_db(self):
      return self.collection

  def iterate_from(self, start):
    f = lambda d: d.get(self.field, '')
    return iter(LazyMap(f, self.collection.find()))

  def getCreatedAt(self, tweet):
      for doc in self.collection.find({'text' : tweet},{'created_at':1, '_id': 0}):
          return doc

class MongoDBCorpusReader():

  def __init__(self, collection):
    word_tokenizer=TreebankWordTokenizer()
    sent_tokenizer=LazyLoader('tokenizers/punkt/PY3/english.pickle')
    self._seq = MongoDBLazySequence('localhost', 27017, 'test', collection, 'text')
    self._word_tokenize = word_tokenizer.tokenize
    self._sent_tokenize = sent_tokenizer.tokenize

  def words(self):
    return LazyMap(self._word_tokenize, self.text())

  def text(self):
    return self._seq

  def getCreatedAt(self, tweet):
    return self._seq.getCreatedAt(tweet)

def insert(data, collection):
    result = MongoDBLazySequence('localhost', 27017, 'test', collection, 'text').get_db().insert_one(data)
    return result
