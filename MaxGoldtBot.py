#!/usr/bin/env python3
# Max Goldt Bot -- a Reddit bot that responds to bild.de links in comments
# with a quote from writer Max Goldt and an archive.is version of the linked
# bild.de article(s)
#
# Version:      0.4.0
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
import os

class MaxGoldtBotCommentParser:
    processed_comments = []
    processed_comments_file = ""
    config = None
    reddit = None
    subreddit = ""
    sleeptime = 0
    regex = '(?<!/)(http[s]?://(?:www|m).bild.de/(?:[-a-zA-Z0-9/_\.\?=,])+)'

    def __init__(self, arguments):
        self.config = configparser.ConfigParser()
        logging.debug('[comments] Reading configuration file %s', arguments.config_file)
        self.config.read(arguments.config_file)
        logging.debug('[comments] Creating Reddit instance for username %s', self.config['MaxGoldtBot']['username'])
        self.reddit = praw.Reddit(client_id=self.config['MaxGoldtBot']['client_id'],
                                  client_secret=self.config['MaxGoldtBot']['client_secret'],
                                  user_agent=self.config['MaxGoldtBot']['user_agent'],
                                  username=self.config['MaxGoldtBot']['username'],
                                  password=self.config['MaxGoldtBot']['password'])
        self.sleeptime = arguments.sleeptime
        self.subreddit = arguments.subreddit
        if arguments.procfile:
            self.processed_comments_file = arguments.procfile
        else:
            self.processed_comments_file = 'processed_comments_%s.txt' % arguments.subreddit
        logging.debug('[comments] Storing processed comments in %s', self.processed_comments_file)
        try:
            with open(self.processed_comments_file) as file:
                for line in file:
                    line = line.strip()
                    self.processed_comments.append(line)
            logging.debug('[comments] Read %d processed comments in total', len(self.processed_comments))
        except (FileNotFoundError, IOError):
            logging.warning('[comments] File %s could not be read', self.processed_comments_file)

    def run(self):
        while True:
            try:
                for comment in self.reddit.subreddit(self.subreddit).stream.comments():
                    if comment.id not in self.processed_comments:
                        self.handle_comment(comment)
                        self.processed_comments.append(comment.id)
                        try:
                            with open(self.processed_comments_file, 'a') as file:
                                file.write(comment.id + '\n')
                        except IOError as e:
                            logging.error('[comments] IO error while writing to %s: %s', self.processed_comments_file, e)
                        if len(self.processed_comments) > 600:
                            logging.info('[comments] Pruning %s to 500 comments', self.processed_comments_file)
                            try:
                                with open(self.processed_comments_file, 'w') as file:
                                    for comment in self.processed_comments[-500:]:
                                        file.write(comment + '\n')
                                self.processed_comments = self.processed_comments[-500:]
                            except IOError as e:
                                logging.error('[comments] IO error while writing to %s: %s', self.processed_comments_file, e)
            except (praw.exceptions.APIException,
                    praw.exceptions.ClientException,
                    prawcore.exceptions.RequestException) as e:
                logging.warning('[comments] Got an exception: %s', e)
                logging.warning('[comments] Will go to sleep for %d seconds', self.sleeptime)
                time.sleep(self.sleeptime)
            except KeyboardInterrupt:
                logging.critical('[comments] Bot has been killed by keyboard interrupt. Exiting')
                sys.exit(0)

    def handle_comment(self, comment):
        logging.debug('[comments] Processing new comment %s', comment.id)
        urls = re.findall(self.regex, comment.body)
        if urls:
            logging.info('[comments] New comment %s with bild.de URLs found', comment.id)
            archive_urls = []
            for url in urls:
                logging.info('[comments] Capturing %s', url)
                archive_url = archiveis.capture(url)
                if archive_url:
                    archive_urls.append(archive_url)
                    logging.info('[comments] Captured: %s', archive_url)
                else:
                    logging.warning('[comments] Got an empty archive.is URL back. Something is wrong')
            if len(urls) != len(archive_urls):
                logging.warning('[comments] Found %d bild.de URLs, but got only %d archive.is links', len(urls), len(archive_urls))
            if archive_urls:
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
                logging.info('[comments] Replied to %s with %d links', comment.id, len(archive_urls))
            else:
                logging.warning('[comments] No reply to %s: %d bild.de links found, none archived', comment.id, len(urls))
        else:
            logging.debug('[comments] No relevant URLs found in %s', comment.id)

class MaxGoldtBotSubmissionParser:
    processed_submissions = []
    processed_submissions_file = ""
    config = None
    reddit = None
    subreddit = ""
    sleeptime = 0
    regex = '(?<!/)(http[s]?://(?:www|m).bild.de/(?:[-a-zA-Z0-9/_\.\?=,])+)'

    def __init__(self, arguments):
        self.config = configparser.ConfigParser()
        logging.debug('[submissions] Reading configuration file %s', arguments.config_file)
        self.config.read(arguments.config_file)
        logging.debug('[submissions] Creating Reddit instance for username %s', self.config['MaxGoldtBot']['username'])
        self.reddit = praw.Reddit(client_id=self.config['MaxGoldtBot']['client_id'],
                                  client_secret=self.config['MaxGoldtBot']['client_secret'],
                                  user_agent=self.config['MaxGoldtBot']['user_agent'],
                                  username=self.config['MaxGoldtBot']['username'],
                                  password=self.config['MaxGoldtBot']['password'])
        self.sleeptime = arguments.sleeptime
        self.subreddit = arguments.subreddit
        if arguments.prosfile:
            self.processed_submissions_file = arguments.prosfile
        else:
            self.processed_submissions_file = 'processed_submissions_%s.txt' % arguments.subreddit
        logging.debug('[submissions] Storing processed submissions in %s', self.processed_submissions_file)
        try:
            with open(self.processed_submissions_file) as file:
                for line in file:
                    line = line.strip()
                    self.processed_submissions.append(line)
            logging.debug('[submissions] Read %d processed submissions in total', len(self.processed_submissions))
        except (FileNotFoundError, IOError):
            logging.warning('[submissions] File %s could not be read', self.processed_submissions_file)

    def run(self):
        while True:
            try:
                for submission in self.reddit.subreddit(self.subreddit).stream.submissions():
                    if submission.id not in self.processed_submissions:
                        self.handle_submission(submission)
                        self.processed_submissions.append(submission.id)
                        try:
                            with open(self.processed_submissions_file, 'a') as file:
                                file.write(submission.id + '\n')
                        except IOError as e:
                            logging.error('[submissions] IO error while writing to %s: %s', self.processed_submissions_file, e)
                        if len(self.processed_submissions) > 600:
                            logging.info('[submissions] Pruning %s to 500 submissions', self.processed_submissions_file)
                            try:
                                with open(self.processed_submissions_file, 'w') as file:
                                    for submission in self.processed_submissions[-500:]:
                                        file.write(submission + '\n')
                                self.processed_submissions = self.processed_submissions[-500:]
                            except IOError as e:
                                logging.error('[submissions] IO error while writing to %s: %s', self.processed_submissions_file, e)
            except (praw.exceptions.APIException,
                    praw.exceptions.ClientException,
                    prawcore.exceptions.RequestException) as e:
                logging.warning('[submissions] Got an exception: %s', e)
                logging.warning('[submissions] Will go to sleep for %d seconds', self.sleeptime)
                time.sleep(self.sleeptime)
            except KeyboardInterrupt:
                logging.critical('[submissions] Bot has been killed by keyboard interrupt. Exiting')
                sys.exit(0)

    def handle_submission(self, submission):
        logging.debug('[submissions] Processing new submission %s', submission.id)
        if submission.selftext == '':
            urls = re.findall(self.regex, submission.url)
        else:
            urls = re.findall(self.regex, submission.selftext)
        if urls:
            logging.info('[submissions] New submission %s with bild.de URLs found', submission.id)
            archive_urls = []
            for url in urls:
                logging.info('[submissions] Capturing %s', url)
                archive_url = archiveis.capture(url)
                if archive_url:
                    archive_urls.append(archive_url)
                    logging.info('[submissions] Captured: %s', archive_url)
                else:
                    logging.warning('[submissions] Got an empty archive.is URL back. Something is wrong')
            if len(urls) != len(archive_urls):
                logging.warning('[submissions] Found %d bild.de URLs, but got only %d archive.is links', len(urls), len(archive_urls))
            if archive_urls:
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
                submission.reply(body)
                logging.info('[submissions] Replied to %s with %d links', submission.id, len(archive_urls))
            else:
                logging.warning('[submissions] No reply to %s: %d bild.de links found, none archived', submission.id, len(urls))
        else:
            logging.debug('[submissions] No relevant URLs found in %s', submission.id)

parser = argparse.ArgumentParser()
parser.add_argument('--config', action='store', dest='config_file', default='MaxGoldtBot.ini',
                    help='a configuration file to read from (default: MaxGoldtBot.ini)')
parser.add_argument('--logfile', action='store', dest='logfile',
                    help='a logfile to write to (default: stdout)')
parser.add_argument('--loglevel', action='store', dest='loglevel', default='WARNING',
                    help='a loglevel (default: WARNING)')
parser.add_argument('--procfile', action='store', dest='procfile',
                    help='a file to store processed comment IDs in')
parser.add_argument('--prosfile', action='store', dest='prosfile',
                    help='a file to store processed submission IDs in')
parser.add_argument('--sleeptime', action='store', dest='sleeptime', default=15 * 60, type=int,
                    help='number of seconds to sleep in case of an API exception')
parser.add_argument('subreddit', action='store',
                    help='subreddit to process comments from')
arguments = parser.parse_args()
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

logging.debug('Forking to let the child care about submissions')
newpid = os.fork()
if newpid == 0:
    logging.info('Started handling submissions')
    submission_parser = MaxGoldtBotSubmissionParser(arguments)
    submission_parser.run()
else:
    logging.info('Started handling comments (submissions given to PID %d)', newpid)
    comment_parser = MaxGoldtBotCommentParser(arguments)
    comment_parser.run()
