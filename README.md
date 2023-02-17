# JustPaste.py
### A simple Python library for JustPaste.it API.
## Disclaimer
Creating notes with non-premium JustPaste accounts are problematic due to the website doing a Captcha check when creating a new note. The captcha WILL be triggered if an account is not used and there is a great chance that the captcha will be triggered if a non-premium account is used. The captcha will not be triggered for premium JustPaste accounts.

 **The captcha is ONLY triggered when creating notes!!!**

*There is not much we can do about this situation.*

## Installation
### *For Windows*:
```py -m pip install -U justpaste.py```
### *For Linux*:
```pip3 install -U justpaste.py```

## Usage

    from justpaste import Justpaste

    j = Justpaste("email_address","password")
    print(j.new_note(title="Test",body="Demonstration,password="12345"))

### *Output*:
    https://justpaste.it/c5j3o

## Methods

### Creating a new note:
    j.new_note(title="Test",body="Demonstration,password="12345")

    >> https://justpaste.it/c5j3o

### Editing a note:
    j.edit_note("https://justpaste.it/c5j3o",title="Edited Title",body="Something that replaces the old text",password="12345")

    >> True

**Note:** The new parameters will *overwrite* the old note altogether, please pass the existing parameters if you wish to keep them unchanged.

### Deleting a note:
    j.delete_note(https://justpaste.it/c5j3o)

    >> True