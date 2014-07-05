import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import dateutil.relativedelta
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = "hitlerbot"
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = "am56nesia"
#This is the bot's Password. 
USERAGENT = "Hitler counter by /u/SirCaptain"
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
PARENTSTRING = ["hitler"]
#These are the words you are looking for
REPLYSTRING = "Way to go, Reddit was Hitler free for "
#This is the word you want to put in reply
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

'''All done!'''

WAITS = str(WAIT)

# Connect to DB, create if its not there
sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

#create table to posts we've replied to
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT, timestamp DATE, permalink TEXT)')
print('Loaded Completed table')

sql.commit()

# log the bot into reddit
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

# Main loop
def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    # Get the latest timestamp in our database for comparison
    lastrecent = cur.execute("SELECT * FROM oldposts WHERE timestamp = (SELECT MAX(timestamp) from oldposts)")
    lastrecent = float(cur.fetchone()[1])
    lastpermalink = cur.fetchone()[2]
    for post in posts:
        pid = post.id
        pts = post.created
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            permalink = post.permalink
            cur.execute('INSERT INTO oldposts VALUES(?, ?, ?)', [pid, pts, permalink])
            # Get the time since last comment about Hitler
            current_timestamp = datetime.datetime.fromtimestamp(pts)
            first_timestamp = datetime.datetime.fromtimestamp(lastrecent)
            tl = dateutil.relativedelta.relativedelta(current_timestamp, first_timestamp)
            ##############################################
            pbody = post.body.lower()
            if any(key.lower() in pbody for key in PARENTSTRING):
                if pauthor != USERNAME:
                    print('Replying to ' + pid + ' by ' + pauthor + ' at ' + str(pts))
                    print(REPLYSTRING + ('%d hours %d minutes %d seconds ' % (tl.hours, tl.minutes, tl.seconds)) + '<br> ' + lastpermalink)
                    post.reply(REPLYSTRING + ('%d hours %d minutes %d seconds ' % (tl.hours, tl.minutes, tl.seconds)) + '<br> ' + lastpermalink)

    # commit matched posts to db
    sql.commit()

# Run loop, wait, run loop
while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
