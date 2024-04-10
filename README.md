# YaSeeker

<p align="center">
  <img src="./pictures/logo.jpg" />
</p>

## Description

YaSeeker - an OSINT tool to get info about any Yandex account using email or login.

It can find:
- Fullname
- Photo
- Gender
- Yandex UID
- Yandex Public ID
- Linked social accounts
- Activity (count of reviews, comments; subscribers and subscriptions)
- Account features (is it verified, banned, deleted, etc.)

Tool checks the following Yandex services: Music, Collections, Bugbounty, Reviews, Q (Znatoki), O (Classified), Zen, Market, Messenger.

**Results are saved in the file `IDENTIFIER.txt` in JSON format.**

## Installation

Python 3.6+ and pip are required.

    pip3 install -r requirements.txt

## Usage

```bash
$ python3 ya_seeker.py login  # only for usernames
# or 
$ python3 ya_seeker.py c48fhxw0qppa50289r5c9ku4k4 yandex_public_id
# identifier can have one of these types: username, yandex_public_id, id, yandex_messenger_guid
```

## Example

```bash
$ python3 ya_seeker.py login
[*] Get info by username `login`...

[+] Yandex.Collections
	URL: https://yandex.ru/collections/user/login/
	Yandex_public_id: c48fhxw0qppa50289r5c9ku4k4
	Fullname: haxxor elite
	Image: https://avatars.mds.yandex.net/get-yapic/24700/enc-0f504b0d68d5f6fb0d336e2157b44e88ef2225aff6a621016f4dccad990b5d3e/islands-200
	Likes: 0
	Cards: 0
	Boards: 0
	Is_passport: True
	Is_restricted: False
	Is_forbid: False
	Is_km: False
	Is_business: False

[+] Yandex.Music
	URL: https://music.yandex.ru/users/login/playlists
	Yandex_uid: 266797119
	Username: login
...

$ python3 ya_seeker.py c48fhxw0qppa50289r5c9ku4k4 yandex_public_id
[*] Get info by yandex_public_id `c48fhxw0qppa50289r5c9ku4k4`...

[+] Yandex.Collections API
	URL: https://yandex.ru/collections/user/c48fhxw0qppa50289r5c9ku4k4/
	Yandex_public_id: c48fhxw0qppa50289r5c9ku4k4
	Fullname: haxxor elite
	Image: https://avatars.mds.yandex.net/get-yapic/24700/enc-0f504b0d68d5f6fb0d336e2157b44e88ef2225aff6a621016f4dccad990b5d3e/islands-200
	Likes: 0
	Cards: 0
	Boards: 0
	Is_passport: True
	Is_restricted: False
	Is_forbid: False
	Is_km: False
	Is_business: False

[+] Yandex.Reviews
	URL: https://reviews.yandex.ru/user/c48fhxw0qppa50289r5c9ku4k4
	Yandex_public_id: c48fhxw0qppa50289r5c9ku4k4
...
```

### SOWEL classification

This tool uses the following OSINT techniques:
- [SOTL-1.4. Analyze Internal Identifiers](https://sowel.soxoj.com/internal-identifiers)
- [SOTL-2.2. Search For Accounts On Other Platforms](https://sowel.soxoj.com/other-platform-accounts)
- [SOTL-6.1. Check Logins Reuse To Find Another Account](https://sowel.soxoj.com/logins-reuse)
- [SOTL-6.2. Check Nicknames Reuse To Find Another Account](https://sowel.soxoj.com/nicknames-reuse) 

## Cookies

Some services are required cookies for API requests. Follow next steps to use your cookies for YaSeeker:
1. Login into Yandex through your browser.
1. Install any extension to download all the Ya cookies in Netscape format aka cookies.txt  ([Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid), [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)).
1. Save it to the directory of YaSeeker in file `cookies.txt`.
1. Run script and enjoy!
