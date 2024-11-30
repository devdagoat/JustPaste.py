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

    import justpaste

    j = justpaste.Justpaste("email_address","password")
    print(j.new_note(title="Test",body="Demonstration,password="12345"))

### *Output*:
    https://justpaste.it/c5j3o

## Couple methods as example:

### Creating a new note:
    j.new_note(title="Test",body="Demonstration,password="12345") # Every possible parameter is present in the doc-string

    >> https://justpaste.it/c5j3o

### Editing a note*:
    j.edit_note("https://justpaste.it/c5j3o",title="Edited Title",body="Something that replaces the old text",password="12345") # Every possible parameter is present in the doc-string

    >> True

*__Note:__ The new parameters will *overwrite* the old note altogether, please pass the existing parameters if you wish to keep them unchanged.

### Deleting a note:
    j.delete_note("https://justpaste.it/c5j3o")

    >> True

### Restoring note from trash:
    j.restore_note("https://justpaste.it/c5j3o")

    >> {"status":"success"}

### Getting account info:
    j.fetch_info("userEmail")

    >> example@example.com

### Fetching all notes**:
    j.fetch_notes()

    >> list({title*:url})

    j.fetch_notes(verbose=True)

    >> list(dict(...))

### Fetching all notes from trash**:
    j.fetch_notes(trash=True)

    >> list({title*:url})

    j.fetch_notes(trash=True,verbose=True)

    >> list(dict(...))

### Finding a note by title**:
    j.find_by_title("string")

    >> list({title*:url})

**__Note:__ If a note has no title, its first ~60 characters of body is returned as title instead. (The reason is the API returns it as title.)

### Sending message to user:
    j.send_msg("https://justpaste.it/u/Justpaste","Hello")

    >> True

### Checking messages from user:
    j.check_msgs("https://justpaste.it/u/Justpaste")

    >> dict()

### Getting user information:
    j.get_user_info("https://justpaste.it/u/Justpaste")

    >> dict()

### Muting conversation:
    j.mute_conv("https://justpaste.it/u/Justpaste")

    >> {'muted': True}

### Unmuting conversation:
    j.unmute_conv("https://justpaste.it/u/Justpaste")

    >> {'muted': False}

### Subscribing to user:
    j.subscribe_to_user("https://justpaste.it/u/Justpaste")

    >> {'isSubscribed': True}

### Adding note to favorites:
    j.fav_note("https://justpaste.it/c5j3o")

    >> {'isFavouirte': True}

*Check the code yourself to see more methods*

## Settings

Now there is a way to change the account settings with this library. It is done by the justpaste.Settings class.

    settings = justpaste.Settings(j)
    
    settings.change("name","Example")
    settings.change("newArticleRequireCaptcha",True) # Every possible setting is present in the doc-string
    settings.change_bulk([{"location":"Anywhere"},{"allowMessages":"everyone"},{"sharedArticleEmailNotification":"only_contacts"}])

    # In fact it's possible to even change profile pictures

    with open("/path/to/the/image.jpg","rb") as buf:
        profile_picture = buf.read()
    with open("/path/to/the/background.png","rb") as buf:
        background_picture = buf.read()

    settings.change("photo",("image.jpg",profile_picture))
    # The exact filename is not needed, it works as long as the extension matches.
    settings.change("background",("tmp.png",background_picture)) 

    j.apply_settings(settings) # returns {url:response} for further possible debugging

