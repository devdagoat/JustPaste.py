import datetime
from typing_extensions import Literal, Any, Protocol, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from pydantic.networks import HttpUrl

from requests import Session

from .consts import *

sentinel = object()

class JustpasteSessionProto:
    if TYPE_CHECKING:
        session : Session
        email : str
        password : str

        def user_from_url(self, user_profile_url:str) -> "User": ...
        def __init__(self, email:str|None=None, password:str|None=None): ...
        def logout(self) -> None: ...

class SaveArticleData(BaseModel):
    articleId : int
    secureCode : str
    content : str
    captcha : Any | None
    path : str
    visibilityLevel : Literal['public','hidden','private'] 
    password : str | None 
    repeatPassword : str | None
    tags : list[str]
    sharedUsers : list[str]
    title : str
    linkSharingAllowed : bool 
    description : str 
    articleViewRequiresCaptcha : bool 
    hideViews : bool = False
    anonymizeOwner : bool 
    expireAfterDate : str | None 
    expireAfterRead : bool 
    isLoggedUser : bool
    

class PublicArticlePreview(BaseModel, extra='ignore'):
    id : int
    note_header : str
    url : HttpUrl
    short_content : str
    tags : list
    created_at : datetime.datetime
    visits : int | None
    favourite_count : int | None
    positive_votes : int 
    negative_votes : int
    pinned : bool

class ArticlePreview(BaseModel, extra='ignore'):
    id : int
    secure_code : str
    url : HttpUrl
    title : str
    is_password_protected : bool
    is_public : bool
    visibility_level : Literal['public','hidden','private']
    unique_views : int
    online : int
    created_at : datetime.datetime
    favourite_count : int
    positive_votes : int
    negative_votes : int
    tags : list

class UserShort(BaseModel, extra='ignore'):
    avatar : HttpUrl | None
    user_name : str
    permalink : str
    user_link : HttpUrl

class User(BaseModel, extra='ignore'):
    id : int
    name : str
    permalink : str
    url : HttpUrl
    active : bool
    avatar : HttpUrl | None
    avatar_large : HttpUrl | None
    background : HttpUrl | None
    can_be_messaged : bool
    description : str | None
    website : HttpUrl | None
    short_website : str | HttpUrl | None
    location : str | None
    articles_count : int
    join_date : datetime.datetime
    qr_code_data : bytes
    visiting_user_is_public : bool
    visitor_is_logged : bool
    public_articles : list[PublicArticlePreview]

class Article(BaseModel, extra='ignore'):
    id : int
    title : str | None
    body : str
    url : HttpUrl
    short_url : HttpUrl
    pdf_url : HttpUrl
    path : str
    qr_code_data : bytes
    positive_votes : int
    negative_votes : int
    content_lang : str
    visibility_level : Literal['public','hidden','private']
    created_at : datetime.datetime
    modified_at : datetime.datetime
    views : int | None
    online : int | None = None
    is_owner : bool
    is_password_protected : bool
    is_captcha_required : Any | None
    is_in_trash : bool
    publisher : UserShort | None = None

class OwnArticle(Article):
    secure_code : str
    edit_url : str
    is_owner : Literal[True]

class Message(BaseModel, extra='ignore'):
    content : str
    creation_date : datetime.datetime
    id : int
    is_rtl : bool
    is_sender : bool
    last_update_date : datetime.datetime
    unread : bool

class Conversation(BaseModel, extra='ignore'):
    id : int
    user : User
    last_message_date : datetime.datetime
    last_message_text : str
    last_message_unread : bool
    muted : bool
    starred : bool
    total_messages : int
    messages : list[Message]

class TotalStats(BaseModel, extra='ignore'):
    total_views : int
    total_favorite : int
    total_online : int
    total_positive_votes : int
    total_negative_votes : int