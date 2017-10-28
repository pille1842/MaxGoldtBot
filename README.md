# MaxGoldtBot

This is a Reddit bot. It reads all comments from a subreddit and checks if they
contain any links to bild.de. If so, the bot responds with the following quote
from German writer Max Goldt:

> Diese Zeitung ist ein Organ der Niedertracht. Es ist falsch, sie zu lesen.
> Jemand, der zu dieser Zeitung beiträgt, ist gesellschaftlich absolut
> inakzeptabel. Es wäre verfehlt, zu einem ihrer Redakteure freundlich oder auch
> nur höflich zu sein. Man muß so unfreundlich zu ihnen sein, wie es das Gesetz
> gerade noch zuläßt. Es sind schlechte Menschen, die Falsches tun.

The response comment will also contain archive.is versions of the linked bild.de
articles, so that future readers are not forced to visit bild.de if they want
to read the article.

This program is licensed under the MIT license, see the LICENSE file. To see what
has changed over time, have a look at
[CHANGELOG.md](https://github.com/pille1842/MaxGoldtBot/blob/master/CHANGELOG.md).

## Prerequisites

To run this bot, you will need:

- Python 3 (tested with 3.5.2 and 3.4.2 on Ubuntu and Debian)
- The following packages (install via `pip` / `pip3`):
    - `archiveis` (a simple wrapper for archive.is)
    - `praw` (the Python Reddit wrapper)

## Setup

Rename the `MaxGoldtBot.ini.sample` file to `MaxGoldtBot.ini`. In this file,
store the configuration values for your bot (you can obtain the client ID and
secret via reddit.com > Preferences > Applications).

## Running the Bot

To run the bot, simply call it with the name of a subreddit as an argument:

```
$ ./MaxGoldtBot.py MySubreddit
```

### Options

#### Configuration file

By default, the bot reads its configuration from `MaxGoldtBot.ini`. However,
you can pass any configuration file name you like to the `--config` option.

#### Logging

By default, the bot will log to standard output and only display messages with
a loglevel of WARNING or above. Use `--loglevel` to change the minimum loglevel
(possible values are DEBUG, INFO, WARNING, ERROR, CRITICAL).

If you wish to log messages into a file instead of standard output, you can pass
a filename to the `--logfile` option.

### Configuration

The sample configuration file (`MaxGoldtBot.ini.sample`) should give you a good
idea of what you need to configure to make this bot work. The configuration file
should contain the following items in a section called `[MaxGoldtBot]`:

- **`client_id`** -- this is the ID of your Reddit application. To obtain one,
  go to reddit.com > preferences > apps and create a new app of type "script".
  The client ID is displayed beneath your application's name.
- **`client_secret`** -- this is the secret key of your Reddit application.
  Never let anyone see this! You can find it in the details of your app under
  reddit.com > preferences > apps.
- **`user_agent`** -- this is a User-Agent string that the bot will provide to
  Reddit when making requests. The default sample is a good idea. Generally, the
  User-Agent string should have the following format:
  `platform:tld.yourhostname.yourapp:vX.Y.Z (by /u/YourUsername)`
- **`username`** -- this is the username of your Reddit bot.
- **`password`** -- this is your Reddit bot's password. Without it, the bot can
  read Reddit comments, but cannot reply to them.

## Subreddit

This bot has its own subreddit where you can ask questions and make requests:
[/r/MaxGoldtBot](https://www.reddit.com/r/MaxGoldtBot)
