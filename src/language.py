from datetime import datetime

import yfinance as yf
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from requests import get
from sqlalchemy.orm import Session

from db import News

# example_url = "https://finance.yahoo.com/m/28ef3dbd-9b3d-3b05-a012-3ef5da9f6305/al-gore%E2%80%99s-firm-dumps-intel.html"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
SID = SentimentIntensityAnalyzer()

def getArticleText(url):
    global headers
    html = get(url, headers=headers).text
    soup = BeautifulSoup(html, features="lxml")

    if "finance.yahoo" in url:
        # print("loading sub-domain...")
        # grab class "link caas-button" in a link
        mydivs = soup.find_all("a", {"class": "link caas-button"})
        if len(mydivs) > 0:
            continue_link = mydivs[0].get('href')
            html = get(continue_link, headers=headers).text
            soup = BeautifulSoup(html, features="lxml")
        # else continue with main soup
    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()
    return text

def getNewsSentiment(title, article):
    
    sent_title = SID.polarity_scores(title)
    if len(article) > 10:
        sent_article = SID.polarity_scores(article)
    else:
        sent_article = {"pos": 0, "neg": 0, "neu": 0, "compound": 0}
    
    return sent_title, sent_article

def updateNews(ticker: str, db: Session):
    try:
        tickObj = yf.Ticker(ticker)
        allnews = tickObj.news
    except Exception as e:
        # TODO: this fails for some reason
        print("could not get news for ticker: ", ticker, str(e))
        allnews = []
    for news in allnews:
        if news is not None:
            # first check in db
            if db.query(News).filter(News.uuid == news.get('uuid', "none")).first() is None:
                try:
                    title =  news['title']
                    link = news['link']
                    article = getArticleText(link)
                    # now calculate sentiment
                    sent_title, sent_article = getNewsSentiment(title, article)
                    totalScore = ((sent_title["pos"]-sent_title["neg"]) * 2 + (sent_article["pos"]-sent_article["neg"])) / 3
                    newsObj = News(
                        uuid = news['uuid'],
                        timestamp = datetime.fromtimestamp(int(news['providerPublishTime'])),
                        ticker = ticker,
                        title = news['title'],
                        publisher = news['publisher'],
                        related_tickers = news.get('relatedTickers'),
                        total_score = totalScore,
                        title_pos_score = sent_title["pos"],
                        title_neg_score = sent_title["neg"],
                        article_pos_score = sent_article["pos"],
                        article_neg_score = sent_article["neg"],
                    )
                    db.add(newsObj)
                except Exception as e:
                    print("error in getting news data: ", ticker, str(e), news)
                    raise
    if len(allnews) > 0:
        db.commit()
        
        