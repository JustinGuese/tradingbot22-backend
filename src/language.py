import datetime as dt
from hashlib import sha256

import nltk
import pandas as pd
from GoogleNews import GoogleNews
from newspaper import Article, Config
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session

from db import News

now = dt.date.today()
now = now.strftime('%m-%d-%Y')
yesterday = dt.date.today() - dt.timedelta(days = 1)
yesterday = yesterday.strftime('%m-%d-%Y')

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0'
config = Config()
config.browser_user_agent = user_agent
config.request_timeout = 10

def percentage(part,whole):
    return 100 * float(part)/float(whole)

def summarize(df: pd.DataFrame):
    try:
        list =[] #creating an empty list 
        for i in df.index:
            dict = {} #creating an empty dictionary to append an article in every single iteration
            article = Article(df['link'][i],config=config) #providing the link
            try:
                article.download() #downloading the article 
                article.parse() #parsing the article
                article.nlp() #performing natural language processing (nlp)
            except:
                pass 
            #storing results in our empty dictionary
            dict['Date']=df['date'][i] 
            dict['Media']=df['media'][i]
            dict['Title']=article.title
            dict['Article']=article.text
            dict['Summary']=article.summary
            dict['Key_words']=article.keywords
            list.append(dict)
        check_empty = not any(list)
        # print(check_empty)
        if check_empty == False:
            news_df=pd.DataFrame(list) #creating datafr
            return news_df

    except Exception as e:
        #exception handling
        print("exception occurred:" + str(e))
        print('Looks like, there is some error in retrieving the data, Please try again or try with a different ticker.' )

def extractDate(datestring: str) -> dt.datetime:
    # 24 hours ago
    # 8 hours ago
    try:
        if "hour" in datestring:
            hoursago = datestring.replace(' hours ago', '')
            hoursago = float(hoursago.replace(' hour ago', ''))
            if hoursago == 0:
                return dt.datetime.utcnow()
            timestamp = dt.datetime.utcnow() - dt.timedelta(hours=hoursago)
            return timestamp
        elif "day" in datestring:
            daysago = datestring.replace(' days ago', '')
            daysago = float(daysago.replace(' day ago', ''))
            timestamp = dt.datetime.utcnow() - dt.timedelta(days=daysago)
            return timestamp
        else:
            print("couldnt get date from %s, using now" % datestring)
            return dt.datetime.utcnow()
    except Exception as e:
        # print("exception: couldnt get date from %s, using now" % datestring)
        return dt.datetime.utcnow()

def getSentiment(ticker: str, news_df: pd.DataFrame) -> pd.DataFrame:
    #Assigning Initial Values
    positive = 0
    negative = 0
    neutral = 0
    #Creating empty lists
    full = []
    analyzer = SentimentIntensityAnalyzer()
    #Iterating over the tweets in the dataframe
    for index, news in news_df.iterrows():
        summary = news["Summary"]
        scr = analyzer.polarity_scores(summary)
        neg = scr['neg']
        neu = scr['neu']
        pos = scr['pos']
        comp = scr['compound']
        timestamp = extractDate(news['Date'])
        full.append([ticker, timestamp, news["Title"], pos, neu, neg, comp])

        if neg > pos:
            negative += 1 #increasing the count by 1
        elif pos > neg:
            positive += 1 #increasing the count by 1
        elif pos == neg:
            neutral += 1 #increasing the count by 1 

    positive = percentage(positive, len(news_df)) #percentage is the function defined above
    negative = percentage(negative, len(news_df))
    neutral = percentage(neutral, len(news_df))

    #Converting lists to pandas dataframe
    full = pd.DataFrame(full, columns = ['ticker', "timestamp", 'title', 'positive', 'neutral', 'negative', 'compound'])
    totalscore = (full["positive"].mean() - full["negative"].mean())/2
    full["total_score"] = totalscore
    # create a column uuid which combines title and ticker
    full["uuid"] = full["title"].map(str) + full["ticker"]
    full["uuid"] = full["uuid"].apply(lambda x: sha256(str(x).encode('utf-8')).hexdigest())
    full["uuid"] = full["uuid"].apply(lambda x: x[:8] + x[-8:])
    # drop duplicates based on title
    full = full.drop_duplicates(subset=['title', 'ticker'], keep='first')
    return full

def updateNews(ticker: str, db: Session):
    #Extract News with Google News
    googlenews = GoogleNews(start=yesterday,end=now)
    googlenews.search(ticker)
    result = googlenews.result()
    #store the results
    df = pd.DataFrame(result)
    news_df = summarize(df)
    if news_df is None:
        print("No news found for %s" % ticker)
        return None
    fullDf = getSentiment(ticker, news_df)
    # next write 2 db
    for index, row in fullDf.iterrows():
        if db.query(News).filter(News.uuid == str(row["uuid"])).first() is None:
            newsObj = News(
                uuid = str(row["uuid"]),
                timestamp = row["timestamp"],
                ticker = str(row["ticker"]),
                title = str(row["title"]),
                total_score = float(row["total_score"]),
                pos_score = float(row["positive"]),
                neg_score = float(row["negative"]),
                )
            db.add(newsObj)
    db.commit()