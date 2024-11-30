from bs4 import BeautifulSoup
import re
import json
import html
import base64
import datetime

from urllib.parse import urlparse

from .objects import *
from .consts import *
from .exceptions import RequireDynamicLoading

from typing import Any, Generator, Iterable, TypeVar
from bs4 import NavigableString, Tag

_T = TypeVar('_T')

def without_key(d:dict[_T, Any], *ks:_T) -> dict:
    d_copy = {}
    for k, v in d.items():
        if k not in ks:
            d_copy[k] = v
    return d_copy

def camel_case_to_snake_case(string:str) -> str:
    matches : list[str] = CAMEL_TO_SNAKE_REGEX.findall(string)
    return '_'.join(m.lower() for m in matches)

def scrape_from_tags(tag:str, regex:re.Pattern, page_source:str, index:int|None=None) -> re.Match:
    soup = BeautifulSoup(page_source,"html.parser")
    scripts = soup.find_all(tag)
    results = None

    if index:
        script = str(scripts[index])
        results = regex.search(script)
    else:
        for _script in scripts:
            match = regex.search(_script)
            if match is not None:
                results = match

    if results is None:
        raise RuntimeError(f"Regex ({repr(regex)}) returned 0 results")

    return results

def scrape_from_script_tags(regex:re.Pattern, page_source:str, index:int|None=None) -> re.Match:
    return scrape_from_tags("script", regex, page_source, index)

def determine_filetype(b:bytes):
    _hex = b.hex().upper()
    for k,v in FILE_MAGIC_BYTES.items():
        if _hex.startswith(v):
            return k
    raise RuntimeError("File type not found")

class ModelInitializer:

    @classmethod
    def article(cls, raw:dict[str, Any]) -> Article | OwnArticle:
        cleaned = {}
        if raw['isArticleOwner'] == True:
            clss = OwnArticle
        else:
            clss = Article

        for k, v in raw.items():
            match k:
                case 'qrCodeData':
                    v = base64.b64decode(v.partition('base64,')[2])
                case 'createdText' | 'modifiedText':
                    k = k.strip('Text') + 'At'
                    v = datetime.datetime.fromisoformat(v)
                case 'viewsText' | 'onlineText':
                    k = k.strip('Text')
                    if isinstance(v, str):
                        v = int(v.replace(',', ''))
                case 'premiumUserData':
                    if v is not None:
                        k = "publisher"
                        v['userLink'] = ROOT+v['userLink']
                        v = {camel_case_to_snake_case(_k) : _v for _k, _v in v.items()}
                case 'isArticleOwner':
                    k = 'isOwner'

                case 'premiumUserData':
                    k = 'publisher'
                    v = cls.user_short(v)

            cleaned[camel_case_to_snake_case(k)] = v

        return clss(**cleaned)

    @classmethod
    def public_article_preview(cls, raw:dict[str, Any]) -> PublicArticlePreview:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case 'createdDate':
                    k = 'createdAt'
                    if v.count(' ') == 1:
                        # Jun 7
                        month, day = v.split(' ')
                        year = datetime.datetime.now().year
                    elif v.count(' ') == 2:
                        # Jun 7, 2022
                        month, day, year = v.split(' ')
                        day = day.strip(',')
                    else:
                        raise NotImplementedError(f"Cannot parse {v}")
                    
                    if len(day) == 1:
                        day = '0'+day
                    # Jun 07 2022
                    v = datetime.datetime.strptime(f"{month} {day} {year}", '%b %d %Y')
                case 'visits' | 'favouriteCount':
                    if v is not None:
                        v = int(v.replace(',', ''))
                case 'positive' | 'negative':
                    k += 'Votes'

            cleaned[camel_case_to_snake_case(k)] = v

        return PublicArticlePreview(**cleaned)

    @classmethod
    def user_short(cls, raw:dict[str, Any]) -> UserShort:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case 'userLink':
                    v = ROOT+v
            
            cleaned[camel_case_to_snake_case(k)] = v
        
        return UserShort(**cleaned)

    @classmethod
    def user(cls, raw:dict[str, Any]) -> User:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case 'qrCodeData':
                    v = base64.b64decode(v.partition('base64,')[2])
                case 'joinedHowLongAgo':
                    k = 'joinDate'
                    # Jun 7, 2022
                    month, day, year = v.split(' ')
                    day = day.strip(',')
                    if len(day) == 1:
                        day = '0'+day
                    # Jun 07 2022
                    v = datetime.datetime.strptime(f"{month} {day} {year}", '%b %d %Y')

            cleaned[camel_case_to_snake_case(k)] = v

        return User(**cleaned)

    @classmethod
    def article_preview(cls, raw:dict[str, Any]) -> ArticlePreview:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case 'uniqueViews' | 'online' | 'favouriteCount':
                    v = int(v.replace(',', ''))
                case 'created':
                    k = 'createdAt'
                    # Jun 7, 2022
                    month, day, year = v.split(' ')
                    day = day.strip(',')
                    if len(day) == 1:
                        day = '0'+day
                    # Jun 07 2022
                    v = datetime.datetime.strptime(f"{month} {day} {year}", '%b %d %Y')
                case 'positive' | 'negative':
                    k += 'Votes'
            cleaned[camel_case_to_snake_case(k)] = v

        return ArticlePreview(**cleaned)

    @classmethod
    def message(cls, raw:dict[str, Any]) -> Message:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case 'lastUpdateDate' | 'creationDate':
                    v = datetime.datetime.fromisoformat(v)
                case 'content':
                    if "<span" in v:
                        match = RegexPatterns.MESSAGE_EMOJI_ONLYEMOJI.value.fullmatch(v)
                        if match:
                            v = match.group(3)
                        else:
                            match = RegexPatterns.MESSAGE_EMOJI_ANYEMOJI.value.fullmatch(v)
                            if match:
                                v = match.group(1) + match.group(3) + match.group(5)
            cleaned[camel_case_to_snake_case(k)] = v

        return Message(**cleaned)

    @classmethod
    def conversation(cls, raw:dict[str, Any], user:User|None=None, messages:list[Message]=[]) -> Conversation:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case "lastMessageDate":
                    v = datetime.datetime.fromisoformat(v)

            cleaned[camel_case_to_snake_case(k)] = v

        cleaned['user'] = user
        cleaned['messages'] = messages

        return Conversation(**cleaned)

    @classmethod
    def total_stats(cls, raw:dict[str, Any]) -> TotalStats:
        cleaned = {}

        for k, v in raw.items():
            match k:
                case 'totalViews':
                    v = v.replace(',', '')
                case 'totalFavourite':
                    k = 'totalFavorite'

            cleaned[camel_case_to_snake_case(k)] = int(v)

        return TotalStats(**cleaned)

def extract_article_metadata(page_source:str) -> dict[str, Any]:
    article_metadata = {}
    article_metadata.update(json.loads(scrape_from_script_tags(RegexPatterns.ARTICLE.value, page_source, 1).group(1)))
    article_metadata.update(json.loads(scrape_from_script_tags(RegexPatterns.BAR_OPTIONS.value, page_source, 1).group(1)))
    return article_metadata

def extract_article_content(page_source:str, article_id:int, dynamic_content:str|None=None) -> dict[str, Any]:
    soup = BeautifulSoup(page_source, 'html.parser')
    article_title_tag = soup.find('h1', {'class' : "articleFirstTitle"})
    assert not (isinstance(article_title_tag, NavigableString))

    if article_title_tag:
        article_title = html.unescape(str(article_title_tag.contents[0]))
    else:
        article_title = None

    if dynamic_content:
        article_content = dynamic_content
    else:
        article_content_tag = soup.find('div', {'id' : "articleContent"})
        assert not (isinstance(article_content_tag, NavigableString))

        if article_content_tag:
            article_content_tag.attrs = {}
            article_content = article_content_tag.contents[0]
        else:
            raise RequireDynamicLoading(article_id)

    return {'title':article_title, 'body':article_content}

def extract_user_metadata(page_source:str) -> dict[str, Any]:
    raw = {}
    raw.update(json.loads(scrape_from_script_tags(RegexPatterns.PAGE_PREMIUM_USER.value, page_source, 1).group(1)))
    raw.update(json.loads(scrape_from_script_tags(RegexPatterns.SHOW_PREMIUM_USER.value, page_source, 1).group(1)))
    return raw

def extract_article(url:str | HttpUrl, page_source:str, dynamic_content:str|None=None) -> Article | OwnArticle:
    raw = {}
    if isinstance(url, str):
        raw['path'] = urlparse(url).path
    elif hasattr(url, 'path'):
        raw['path'] = url.path
    else:
        raise TypeError('URL should either be a string or support path extraction')
    raw.update(extract_article_metadata(page_source))

    raw.update(extract_article_content(page_source, raw['id'], dynamic_content))

    return ModelInitializer.article(raw)

def extract_public_articles(*page_sources:str) -> Generator[PublicArticlePreview, None, None]:
    for page_source in page_sources:
        for article_raw in json.loads(scrape_from_script_tags(RegexPatterns.PUBLIC_ARTICLES_DATA.value, page_source, 1).group(1)):
            yield ModelInitializer.public_article_preview(article_raw)

def extract_user(page_source:str, public_articles:list[PublicArticlePreview]) -> User:
    raw = {'public_articles':public_articles, **extract_user_metadata(page_source)}
    return ModelInitializer.user(raw)

def extract_total_stats(page_source:str) -> TotalStats:
    raw = json.loads(scrape_from_script_tags(RegexPatterns.ARTICLES_STATS_DATA.value, page_source, 5).group(1))
    return ModelInitializer.total_stats(raw)

SAVE_ARTICLE_CONSTRUCTOR_MAP = [
    ("article_id", "articleId"),
    ("secure_code", "secureCode"),
    ("body", "content"),
    ("privacy", "visibilityLevel"),
    ("password", "repeatPassword"),
    ("anon_owner", "anonymizeOwner"),
    ("hide_views", "hideViews"),
    ("require_captcha", "articleViewRequiresCaptcha"),
    ("shared_users", "sharedUsers"),
    ("expiry_date", "expireAfterDate"),
    ("viewonce", "expireAfterRead"),
    ("logged_in", "isLoggedUser"),
    ("allow_link_sharing", "linkSharingAllowed")
]

def _parse_existing_response(existing:dict[str, Any]) -> dict[str, Any]:
    new = {}

    for k in ('id', 'title', 'description', 'path', 'visibilityLevel', 'secureCode', 'password'):
        if k == 'id':
            new['articleId'] = existing['article']['id']
        else:
            new[k] = existing['article'][k]

    new['content'] = existing['articleContent']
    new['tags'] = existing['articleTags']
    new['sharedUsers'] = existing['articleSharedUsers']

    new['linkSharingAllowed'] = existing['linkSharingAllowed']
    new['articleViewRequiresCaptcha'] = existing['articleViewRequiresCaptcha']
    new['hideViews'] = existing['hideViews']
    new['anonymizeOwner'] = existing['anonymizeOwner']
    new['expireAfterDate'] = existing['expireAfterDate']
    new['expireAfterRead'] = existing['expireAfterRead']

    return new

def construct_save_json(article_id:int,
                   secure_code:str,
                   *,
                   title:str='',
                   body:str='',
                   privacy:Literal['public','hidden','private'],
                   path="",
                   password=None,
                   anon_owner=False,
                   hide_views=False,
                   require_captcha=False,
                   shared_users:list=[],
                   tags:list=[],
                   description="",
                   expiry_date:str|None=None,
                   viewonce=False,
                   logged_in:bool=False,
                   allow_link_sharing=False,
                   **kwargs):
        
        if not privacy:
            if logged_in:
                privacy = "hidden"
            else:
                privacy = "public"

        return SaveArticleData(
            articleId=article_id,
            secureCode=secure_code,
            title=title,
            content=body,
            captcha=kwargs.get('captcha', None),
            path=path,
            password=password,
            repeatPassword=password,
            tags=tags,
            sharedUsers=shared_users,
            anonymizeOwner=anon_owner,
            expireAfterDate=expiry_date,
            expireAfterRead=viewonce,
            isLoggedUser=logged_in,
            articleViewRequiresCaptcha=require_captcha,
            description=description,
            hideViews=hide_views,
            visibilityLevel=privacy,
            linkSharingAllowed=allow_link_sharing)

def copy_save_json(existing:dict[str, Any], new_info:dict[str, Any]) -> SaveArticleData:

    data = new_info.copy()

    for k, v in _parse_existing_response(existing).items():

        for _ckey, _skey in SAVE_ARTICLE_CONSTRUCTOR_MAP:
            if k == _skey:
                ckey = _ckey
                break
        else:
            ckey = k
    
        if ckey not in new_info:
            data[ckey] = v

    return construct_save_json(**data)