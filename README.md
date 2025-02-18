# **JustPaste.py:** Simple JustPaste.py API Wrapper for Python

## Disclaimer:
Justpaste.py API requires captcha for creating new notes for accounts that have not purchased their Premium service. Once purchased, captchas will disappear even after the premium expires. 

## Installation:

```
pip install -U justpaste.py
```

## Usage:
```python
from justpaste import Justpaste

jp = Justpaste("<your email>", "<your password>")

# create new article
article = jp.new_article(
    title="Title of article",
    body="<p>Hello World</p>",
    privacy="public",
    tags=["test"],
    hide_views=True
)

# edit existing article

edited = jp.edit_article(
    article,
    title="New Title",
    body="<p>Hello, World!</p>"
    privacy="hidden"
)

# delete article (move to trash)

jp.delete_article(edited)

# get a user's public articles

user = jp.user_from_url("...")
user.public_articles # previews
[load_articles_from_preview(preview) for preview in user.public_articles] # full articles

```
