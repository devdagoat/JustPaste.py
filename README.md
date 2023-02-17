# JustPaste.py
### A simple Python library for JustPaste.it API.
---
## Disclaimer
---
Creating notes with non-premium JustPaste accounts are problematic due to the website doing a Captcha check when creating a new note. The captcha WILL be triggered if an account is not used and there is a great chance that the captcha will be triggered if a non-premium account is used. The captcha will not be triggered for premium JustPaste accounts.

 **The captcha is ONLY triggered when creating notes!!!**

There is not much we can do about this situation.

## Installation
---
### *For Windows*:
```py -m pip install -U justpaste.py```
### *For Linux*:
```pip3 install -U justpaste.py```

## Usage
---
    from justpaste import Justpaste

    j = Justpaste("email address","password")
    print(j.new_note(title="Test",body="Demonstration,password="12345"))
### *Output*:
    https://justpaste.it/XXXXX

    