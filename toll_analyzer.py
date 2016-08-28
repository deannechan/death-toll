import re
import csv
import nltk
import db
import collections
import string
from nltk.tokenize import TreebankWordTokenizer
from nltk.corpus import stopwords
import downloadTweets

def processTweet(tweet):
    #Convert to lower case
    tweet = tweet.lower()
    #Convert www.* or https?://* to URL
    tweet = re.sub('((www\.[\s]+)|(https?://[^\s]+))','URL',tweet)
    #Convert @username to AT_USER
    tweet = re.sub('@[^\s]+','AT_USER',tweet)
    #Remove additional white spaces
    tweet = re.sub('[\s]+', ' ', tweet)
    #Replace #word with word
    tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
    #Remove ,
    tweet = re.sub(',','',tweet)
    tweet = re.sub(r'[0-9]+mph', 'mph', tweet)
    tweet = re.sub(r'[0-9]+kph', 'kph', tweet)
    #trim
    tweet = tweet.strip('\'"')
    return tweet

# Create stop words list
def getStopWordList():
    # read the stopwords file and build a list
    punctuation = list(string.punctuation)
    stopWords = []
    stopWords = stopwords.words('english') + punctuation + ['rt', 'via', 'RT', 'url', 'URL', 'AT_USER', 'at_user']
    return stopWords

# tokenize only important words
def tokenize(tweet, stopWords):
    tokens = []
    #split tweet into words
    words = tweet.split()
    for w in words:
        #strip punctuation
        w = w.strip('\'"?,.')
        #check if the word stats with an alphabet or number
        val = re.search(r"^[a-zA-Z0-9][a-zA-Z0-9]*$", w)
        #ignore if it is a stop word
        if(w in stopWords or val is None):
            continue
        else:
            tokens.append(w.lower())
    return tokens

#  A feature extractor for document classification, whose features indicate whether or not individual words are present in a given document.
def extract_features(tweet):
    tweet_words = set(tweet)
    features = {}
    for word in tokenizeTrainingList:
        features['contains(%s)' % word] = (word in tweet_words)
    return features

# get POS tags
def GetTagWords(tweetTokenPairs, tagPrefix):
    return [word for (word, tag) in tweetTokenPairs if tag.startswith(tagPrefix)]

#start number normalizer
def num_normalize(number):
    number = re.sub('million', '1000000', number)
    number = re.sub('hundred', '100', number)
    number = re.sub('thousand', '1000', number)
    number = re.sub('billion', '1000000', number)
    number = re.sub('k', '000', number)
    number = re.sub('m', '000000', number)
    number = re.sub('\+', '', number)
    number = re.sub('th', '', number)
    number = re.sub('one', '1', number)
    number = re.sub('two', '2', number)
    number = re.sub('three', '3', number)
    number = re.sub('four', '4', number)
    number = re.sub('five', '5', number)
    number = re.sub('six', '6', number)
    number = re.sub('seven', '7', number)
    number = re.sub('eight', '8', number)
    number = re.sub('nine', '9', number)
    number = re.sub('zero', '0', number)

    number = re.sub('\.[0-9]+', '', number)

    return number

if __name__ == '__main__':
    outfile = downloadTweets.startDownload()

    #Read the tweets one by one and process it
    inpTweets = csv.reader(open('data/training.csv', 'r', encoding="utf8"), delimiter=',', quotechar='|')
    stopWords = getStopWordList()
    tokenizeTrainingList = []
    tokenizeTweetsList = []

    # Get tweets words
    trainingTweets = []
    for row in inpTweets:
        sentiment = row[0]
        tweet = row[1]
        processedTweet = processTweet(tweet)
        tokenizeTraining = tokenize(processedTweet, stopWords)
        tokenizeTrainingList.extend(tokenizeTraining)
        trainingTweets.append((tokenizeTraining, sentiment));

    # Remove tokenizeTrainingList duplicates
    tokenizeTrainingList = list(set(tokenizeTrainingList))

    # Extract feature vector for all tweets in one shot
    training_set = nltk.classify.util.apply_features(extract_features, trainingTweets)

    # Train the classifier
    NBClassifier = nltk.NaiveBayesClassifier.train(training_set)

    # print("Accuracy:",nltk.classify.accuracy(NBClassifier, training_set))
    # print(NBClassifier.show_most_informative_features(5))

    # Access MongoDB
    reader = db.MongoDBCorpusReader(outfile)

    numCollected = []

    withTollRaw = []
    withTollTweets = []

    for text in reader.text():
        testTweet = text
        processedTestTweet = processTweet(testTweet)
        tokenizeTweet = tokenize(processedTestTweet, stopWords)
        tokenizeTweetsList.extend(tokenizeTweet)

        result = NBClassifier.classify(extract_features(tokenizeTweet))
        if result == 'withToll':
            withTollRaw.append(testTweet)
            withTollTweets.append(' '.join(word for word in tokenizeTweet))

    # get bigrams
    terms_bigram = tokenizeTweetsList

    posTags = []
    y = 0

    for withTollTweet in withTollTweets:
        temp = TreebankWordTokenizer().tokenize(withTollTweet)
        posTags.append(nltk.pos_tag(temp))
        numCollected.append(GetTagWords(posTags[y], 'CD'))
        y = y+1

    # print(numCollected)
    for x in range(0, len(numCollected)):
        for y in range(0, len(numCollected[x])):
            numCollected[x][y] = num_normalize(numCollected[x][y])

    listNum = []

    for sublist in numCollected:
        for x in sublist:
            listNum.append(x)

    getCount = collections.Counter(listNum)
    print("Death Toll: ", getCount.most_common(1)[0][0])

    count_all = collections.Counter()
    # Update the counter
    count_all.update(terms_bigram)
    # Print the most frequent words
    print(count_all.most_common(10))
