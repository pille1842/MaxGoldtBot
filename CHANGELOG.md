# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased
### Added
- Added an option `--procfile` to control where the bot stores the IDs of
  processed comments. The default is `processed_comments_SUBREDDIT.txt` in the
  bot's working directory.
- Added an option `--sleeptime` to control how long the bot will go to sleep
  in case there is an API exception (default: 15 minutes).

### Changed
- The bot will now keep a maximum of 600 processed comments in storage. When
  more than 600 processed comment IDs are stored, the procfile is pruned down
  to 500 comments.
- The bot will now log a message when it is quit via keyboard interrupt (Ctrl-C).

## [0.1.1] - 2017-10-28
- Fixed a bug where the bot would spontaneously halt due to a RequestException.
  This exception is now handled.

## [0.1.0] - 2017-10-27
This is the initial release.
