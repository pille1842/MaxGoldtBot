#!/usr/bin/env python3
# Max Goldt Bot -- a Reddit bot that responds to bild.de links in comments
# with a quote from writer Max Goldt and an archive.is version of the linked
# bild.de article(s)
#
# Version:      0.1.0
# Author:       Eric Haberstroh <eric@erixpage.de>
# License:      MIT <https://opensource.org/licenses/MIT>

import archiveis
import argparse
import configparser
import logging
import praw
import prawcore.exceptions
import re
import sys
import time

def handle_comment(comment):
    logging.debug('Processing new comment %s', comment.id)
    urls = re.findall('(http[s]?://(?:www|m).bild.de/(?:[-a-zA-Z0-9/_\.])+)',
                      comment.body)
    if urls:
        # There are bild.de URLs in this comment. Let's archive them.
        logging.info('New comment %s with bild.de URLs found', comment.id)
        archive_urls = []
        for url in urls:
            logging.info('Capturing %s', url)
            archive_url = archiveis.capture(url)
            if archive_url:
                archive_urls.append(archive_url)
                logging.info('Captured: %s', archive_url)
            else:
                logging.warning('Got an empty archive.is URL back. Something is wrong')
        if len(urls) != len(archive_urls):
            logging.warning('Found %d bild.de URLs, but got only %d archive.is links', len(urls), len(archive_urls))
        if archive_urls:
            # Now let's reply to the comment
            links = "\n- ".join(archive_urls)
            body = ("> Diese Zeitung ist ein Organ der Niedertracht. Es ist falsch, sie zu lesen.\n"
                    "> Jemand, der zu dieser Zeitung beiträgt, ist gesellschaftlich absolut inakzeptabel.\n"
                    "> Es wäre verfehlt, zu einem ihrer Redakteure freundlich oder auch nur höflich zu sein.\n"
                    "> Man muß so unfreundlich zu ihnen sein, wie es das Gesetz gerade noch zuläßt.\n"
                    "> Es sind schlechte Menschen, die Falsches tun.\n\n"
                    "[Max Goldt](https://de.wikipedia.org/wiki/Max_Goldt), deutscher Schriftsteller\n\n"
                    "Du kannst diesen Artikel auf archive.is lesen, wenn du nicht auf bild.de gehen willst:\n\n- " \
                    + links + \
                    "\n\n"
                    "----\n\n"
                    "^^[Info](https://www.reddit.com/r/MaxGoldtBot)&nbsp;|&nbsp;"
                    "[Autor](https://www.reddit.com/u/pille1842)&nbsp;|&nbsp;"
                    "[GitHub](https://github.com/pille1842/MaxGoldtBot)&nbsp;|&nbsp;"
                    "[Warum&nbsp;die&nbsp;Bild&nbsp;schlecht&nbsp;ist]"
                    "(http://www.bildblog.de/62600/warum-wir-gegen-die-bild-zeitung-kaempfen/)")
            comment.reply(body)
            logging.info('Replied to %s with %d links', comment.id, len(archive_urls))
        else:
            logging.warning('No reply to %s: %d bild.de links found, none archived', comment.id, len(urls))
    else:
        logging.debug('No relevant URLs found in %s', comment.id)

# First, let's parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', action='store', dest='config_file', default='MaxGoldtBot.ini',
                    help='a configuration file to read from (default: MaxGoldtBot.ini)')
parser.add_argument('--logfile', action='store', dest='logfile',
                    help='a logfile to write to (default: stdout)')
parser.add_argument('--loglevel', action='store', dest='loglevel', default='WARNING',
                    help='a loglevel (default: WARNING)')
parser.add_argument('subreddit', action='store',
                    help='subreddit to process comments from')

arguments = parser.parse_args()

# Set loglevel and (optionally) logfile
numeric_level = getattr(logging, arguments.loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % arguments.loglevel)
logformat = '[%(asctime)s] %(levelname)s: %(message)s'
if arguments.logfile:
    logging.basicConfig(level=numeric_level, format=logformat, filename=arguments.logfile)
    logging.debug('Logging configuration: loglevel %s, logfile %s', arguments.loglevel, arguments.logfile)
else:
    logging.basicConfig(level=numeric_level, format=logformat)
    logging.debug('Logging configuration: loglevel %s, display output', arguments.loglevel)

# Now, let's read the configuration file
config = configparser.ConfigParser()
logging.debug('Reading configuration file %s', arguments.config_file)
config.read(arguments.config_file)

# Next, let's create a Reddit instance
logging.debug('Creating Reddit instance for username %s', config['MaxGoldtBot']['username'])
reddit = praw.Reddit(client_id=config['MaxGoldtBot']['client_id'],
                     client_secret=config['MaxGoldtBot']['client_secret'],
                     user_agent=config['MaxGoldtBot']['user_agent'],
                     username=config['MaxGoldtBot']['username'],
                     password=config['MaxGoldtBot']['password'])

# We won't be processing any comments twice. Therefore we create a list of
# comment IDs we already processed from a file in the current directory.
# This list will later be extended and written to that file as we process
# new comments.
processed_comments = []
# Processed comments are read from a file per subreddit. This way, multiple
# instances of the bot can run for multiple subreddits without getting in
# each other's way.
processed_comments_file = 'processed_comments_%s.txt' % arguments.subreddit
logging.debug('Storing processed comments in %s', processed_comments_file)
try:
    with open(processed_comments_file) as file:
        for line in file:
            line = line.strip()
            processed_comments.append(line)
    logging.debug('Read %d processed comments in total', len(processed_comments))
except (FileNotFoundError, IOError):
    logging.warning('File %s could not be read', processed_comments_file)

# Main loop. Iterate through a stream of comments from the subreddit this
# bot was called with. Try to find bild.de URLs in these comments and, if
# any are found, reply with a quote from Max Goldt and an archive.is link
# to an archived version of the bild.de article.
while True:
    try:
        for comment in reddit.subreddit(arguments.subreddit).stream.comments():
            if comment.id not in processed_comments:
                handle_comment(comment)
                # Append the comment to the list of processed comments
                processed_comments.append(comment.id)
                try:
                    with open(processed_comments_file, 'a') as file:
                        file.write(comment.id + '\n')
                except IOError as e:
                    logging.error('IO error while writing to %s: %s', processed_comments_file, e)
    except (praw.exceptions.APIException,
            praw.exceptions.ClientException,
            prawcore.exceptions.RequestException) as e:
        logging.warning('Got an exception. Will go to sleep for 15 minutes')
        if hasattr(e, 'message'):
            logging.warning('Exception was: %s', e.message)
        time.sleep(15 * 60)
