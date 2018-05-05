# e97

&copy; 2018 SiLeader.

## Overview
e97 is Wiki like system.

## Features
+ Create and rewrite pages
+ Search posted pages (AND, NOT)
+ Download as PDF document
+ Recent n-page (default: n=20)
+ Index of pages
+ Login system
+ CSRF Protect (Flask-WTF CSRFProtect)
+ Backup all old pages

## Setup
1. Clone this repository
1. Create initial user
1. Start server

### Create initial user
1. Move to `models`
1. Run `users.py` as script
1. Enter E-mail, user name and password

```
cd models
path/to/python3 users.py
```

## Settings
If you want to change e97 behavior, update `settings.py`.

| Name | Meaning |
|:----:|:--------|
| SEPARATE_PAGE_TITLE_AND_ID | Separate title and page ID (If set True, page ID is UUID.) |
| SAVE_TO_ARCHIVE | Save old pages to `archive` collection |
| TOP_PAGE_REST | Location of top page's reST source file |
| ERROR_PAGE_DIRECTORY | Directory of error page |

### Error page file name
ERROR_PAGE_DIRECTORY + error_code + ".rst"

## Dependencies
+ MongoDB
+ Python packages in `requirements.txt`

## License
Apache License 2.0
