import boto3
import config
import csv
import googlemaps
import json
import mysql.connector
import preprocessor as p
import re
import sys
import tweepy

from datetime import datetime
from monkeylearn import MonkeyLearn


# Fill the X's with the credentials obtained by
# following the above mentioned procedure.
consumer_key = config.consumer_key
consumer_secret = config.consumer_secret
access_key = config.access_key
access_secret = config.access_secret


dropAndRecreateTable = False


def get_tweets(location, city, state):

    # Authorization to consumer key and consumer secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    # Access to user's access key and access secret
    auth.set_access_token(access_key, access_secret)

    # Calling api
    api = tweepy.API(auth)

    # 200 tweets to be extracted
    number_of_tweets = 2000
    # tweets = api.user_timeline(screen_name=username)

    tweets = api.search(
        q="weather", geocode=location, count=500)

    # print(tweets)

    # Empty Array
    tmp = []

    # create array of tweet information: username,
    # tweet id, date/time, text
    # CSV file created
    # tweets_for_csv = [(tweet.text, tweet.created_at) for tweet in tweets]

    # Open/create a file to append data to
    csvFile = open('result.csv', 'w')

    # Use csv writer
    csvWriter = csv.writer(csvFile, delimiter=',')

    for tweet in tweets:

        # Appending tweets to the empty array tmp

        cleaned_tweet = p.clean(tweet.text.encode('utf-8'))

        tweet.text = cleaned_tweet

        tmp.append(tweet.text)
        csvWriter.writerow(
            [tweet.text.encode('utf-8'),
             city,
             state])

    csvFile.close()

    # Printing the tweets

    print("\n Printing the tweets \n")
    print(tmp)


def loadToMySQL():

    conn = mysql.connector.connect(
        host=config.awsDBHost,
        port=config.awsDBPort,
        user=config.awsDBUser,
        passwd=config.awsDBPasswd,
        database=config.awsDBDatabase
    )

    print("\n Connected to DB \n")
    print(conn)

    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()

    if (dropAndRecreateTable == True):
        # Dropping StreamedData table if already exists.
        cursor.execute("DROP TABLE IF EXISTS StreamedData")

        # Creating table as per requirement
        sqlCreateTable = '''CREATE TABLE StreamedData(
                                ID int NOT NULL AUTO_INCREMENT, 
                                TWEET TEXT(1000) NOT NULL,
                                CITY CHAR(100),
                                STATE CHAR(100),
                                PRIMARY KEY (ID)
                            )'''
        cursor.execute(sqlCreateTable)

    file = open('result.csv', 'rb')

    csv_data = csv.reader(file)

    for row in csv_data:
        cursor.execute('INSERT INTO StreamedData(TWEET, CITY, STATE)'
                       'VALUES(%s, %s, %s)',
                       row)

    conn.commit()

    # Closing the connection
    conn.close()


def analyzeTweetForSentiment():

    conn = mysql.connector.connect(
        host=config.awsDBHost,
        port=config.awsDBPort,
        user=config.awsDBUser,
        passwd=config.awsDBPasswd,
        database=config.awsDBDatabase
    )

    print("Connected to Database: ", conn)

    # Creating a cursor object using the cursor() method
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM StreamedData")

    result = cursor.fetchall()

    comprehend = boto3.client(
        service_name='comprehend',
        region_name=config.awsRegion,
        aws_access_key_id=config.ACCESS_KEY,
        aws_secret_access_key=config.SECRET_KEY
    )

    sentimentResults = []

    for tweetObject in result:
        primaryId = tweetObject[0]
        tweetText = tweetObject[1].encode('utf-8')

        print(tweetText)

        jsonStringSentiment = json.dumps(comprehend.detect_sentiment(
            Text=tweetText, LanguageCode='en'), sort_keys=True, indent=4)

        jsonObjectSentiment = json.loads(jsonStringSentiment)

        sentimentTitle = jsonObjectSentiment["Sentiment"].title()
        sentimentExactScore = jsonObjectSentiment["SentimentScore"][sentimentTitle]

        sentimentResults.append(
            (primaryId, sentimentTitle, sentimentExactScore))

        # print(sentimentResults)

    # Dropping SentimentData table if already exists.
    cursor.execute("DROP TABLE IF EXISTS SentimentData")

    # Creating table as per requirement
    sqlCreateTable1 = '''CREATE TABLE SentimentData(
                            ID int NOT NULL,
                            TAG_NAME TEXT(10) NOT NULL,
                            CONFIDENCE FLOAT NOT NULL,
                            PRIMARY KEY (ID)
                        )'''
    cursor.execute(sqlCreateTable1)

    print("\n SENTIMENT DATA \n")

    for row in sentimentResults:
        cursor.execute('INSERT INTO SentimentData(ID, TAG_NAME, CONFIDENCE)'
                       'VALUES(%s, %s, %s)',
                       row)

        print(row)

    conn.commit()

    # Closing the connection
    conn.close()


# Driver code
if __name__ == '__main__':

    gmaps = googlemaps.Client(key=config.googleClientKey)
    if len(sys.argv) < 2:
        city = "Atlanta"
        state = "Ga"
    else:
        city = sys.argv[1]
        state = sys.argv[2]

    # Geocoding an address
    geocode_result = gmaps.geocode(
        '' + city + ',' + state + '')

    jsonString = json.dumps(geocode_result[0])
    jsonObject = json.loads(jsonString)

    lat = str(jsonObject['geometry']['location']['lat'])
    lng = str(jsonObject['geometry']['location']['lng'])

    location = lat + ',' + lng + ',' + '50mi'
    print("Location of Tweets: ", location)

    print("\n Fetching the Tweets!\n")
    get_tweets(location, city, state)

    print("\nSending to Database!\n")
    loadToMySQL()

    print("\Analyzing Sentiments of Tweets!\n")
    analyzeTweetForSentiment()
