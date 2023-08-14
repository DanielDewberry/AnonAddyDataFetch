# Addy.io Data Fetch


Backup Addy.io email address data with ease.


## Features

- Configurable columns and ordering
- Logging level and file destination


## License

All rights reserved, not for forking and/ or redistribution without prior written consent.


## Maintenance policy

I will fix bugs as soon as possible after they have been reported to me.
Please note that the tool relies on upstream stability.


## Contributions

Please contact me before dedicating any time to creating merge requests. Let's talk about the changes you'd like to offer.


## Installation

```
sudo cp addyio-data-fetch.py /usr/local/bin/
sudo chmod 555 /usr/local/bin/addyio-data-fetch.py
```


## Usage

See the usage information:

```
# addyio-data-fetch.py --help

usage: addyio-data-fetch.py [-h]
                              [--log-level {debug,info,warning,error,critical}]
                              [--columns COLUMNS]
                              token filename

positional arguments:
  token                 The addy.io API token, or the file in which the token is the first line
  filename              The filename to overwrite with CSV data

optional arguments:
  -h, --help            show this help message and exit
  --log-level {debug,info,warning,error,critical}
                        The logging level which will affect reporting
                        information
  --columns COLUMNS     Comma-separated list of column names to use. All
                        columns selected by default.
```


### Recommendation: backup runner script

It is recommended that you create a backup runner:


```bash
mkdir -p "${HOME}/backups/addyio"
mkdir -p "${HOME}/.addyio"
echo 'YourToken' > "${HOME}/.addyio/token-file"
```

`"${HOME}/.addyio/token-file"`:

```
ashqeghehajhkjahdkjad
```


`${HOME}/.local/bin/backup-addyio`:

```bash
#!/bin/bash

if ! Now="$(date -Is)"; then
    echo 'Failed to get timestamp' >&2
    exit 1
fi
readonly Now

declare -r TokenFile="${HOME}/.addyio/token-file"
declare -r BackupFile="${HOME}/backups/addyio/addyio-mail-list-${Now}.csv"

addyio-data-fetch.py "${TokenFile}" "${BackupFile}"
exit
```


## Scheduling

If the host is a Linux system, scheduling can be performed with `cron` or `systemd.timers`.


### Crontab example

Crontab:

```bash
# Midnight every day  # help: https://crontab.guru/
0 0 * * * /home/username/.local/bin/backup-addyio
```


### Systemd Timer example


#### backup-addyio.service

```
[Unit]
Description=%i service
DefaultDependencies=no
Wants=multi-user.target

[Service]
Type=oneshot
ExecStart=/home/username/.local/bin/backup-addyio
```

#### backup-addyio.timer

```
[Unit]
Description=Fire the backup-addyio service
Requires=backup-addyio.service

[Timer]
Unit=backup-addyio.service
OnCalendar=*-*-* 00:00:00
AccuracySec=60s
Persistent=true

[Install]
WantedBy=timers.target
```


#### Install the service and timer

```bash
sudo cp backup-addyio.service /etc/systemd/system/
sudo cp backup-addyio.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now backup-addyio.timer
```


## Design choices and stability

To enable a simple interface, the tool accepts the token and the output file on the CLI.
This may be changed in the future to better protect the token. **Major semantic version changes should be considered as "breaking".**
