To run the code, you first need to set up all the API configurations,

- which need to go into a config.py file

# Twitter/Tweepy Secrets

- consumer_key
- consumer_secret
- access_key
- access_secret

# AWS Secrets

- awsDBHost
- awsDBPort
- awsDBUser
- awsDBPasswd
- awsDBDatabase

- awsRegion

- ACCESS_KEY
- SECRET_KEY

# Google Secrets

- googleClientKey

Then you can run the "index.py" code file by using the following commands in the command console (or terminal)

`python.exe .\index.py` => defaults the city to Atlanta Georgia

`python.exe .\index.py "CITY" "STATE"`

The code will call the following 3 methods from the main function:

    print("\n Fetching the Tweets!\n")
    get_tweets(location, city, state)

    print("\nSending to Database!\n")
    loadToMySQL()

    print("\Analyzing Sentiments of Tweets!\n")
    analyzeTweetForSentiment()

The code will generate a CSV file called `results.csv`, which will contain the cleaned tweets and location in which they came from

It will also print to the console screen the following:

    print("Location of Tweets: ", location)

    print("\n Printing the tweets \n")

    print("\n SENTIMENT DATA \n")

The code will push the `results.csv` into a AWS RDS Databases called `StreamData`,
then it will query the database to analysis sentiments,
then it will create a new table with sentiments for each tweet, the table will be called `SentimentData`
