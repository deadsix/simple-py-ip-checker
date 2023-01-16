# simple-py-ip-checker

## Intro

Python script that checks your public IP via AWS and stores it in a SQLite3 database for tracking changes.

Currently simple-py-ip-checker can notify you if your public IP changes via a Discord webhook. 
Only a webhook url is required, which are available to non-developers. 

## Table of Contents

- [Prerequisites](#prerequisites)
- [Planned Features](#planned-features)

### Prerequisites

Please open the included `env.json` file and add values to the fields

#### Required Values
- `db_name` - name of the database that will be created to store IP address, the inserted value must be a `str` and include 
`.db` as the file type. Default value is `ip_addrs.db`.
- `discord_noticiations_enabled` - toggle to enable or disable the sending of Discord notifications. Inserted value must
be a `bool`. Default value is `false`

#### Optional Values
- `log_level` - level of logging the script will adhere to, learn more about log levels via the official Python logging 
[tutorial](https://docs.python.org/3/howto/logging.html#when-to-use-logging). 
The script will automatically default log level `WARN`
- `discord_webhook_url` - the webhook url provided by Discord. This value must be provided if Discord notifications are 
enabled. Learn more about Discord webhooks via Discord's 
[Intro to Webhooks ](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

### Planned Features
- Gotify Integration - https://gotify.net/