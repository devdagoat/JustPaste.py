import requests
import re
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
import warnings

from .consts import *
from .exceptions import *
from .objects import *
from .utils import *

class JustpasteBase:

    def __init__(self, email:str|None=None, password:str|None=None, session:requests.Session|None=None):
        self.email = email
        self.password = password
        self.session = self._login(session)
        self.session.headers['accept'] = "application/json, text/plain, */*"

    def _login(self, session:requests.Session|None=None) -> requests.Session:
        headers = {"User-Agent": USER_AGENT}
        if not session:
            sess = requests.Session()
        else:
            sess = session
        sess.headers.update(headers)

        if self.email and self.password:

            payload = {
                "email":self.email,
                "password":self.password,
                "rememberMe":True
                }
            resp = sess.post(APIEndpoints.LOGIN.value, json=payload)
            data = resp.json()

            if "success" in data:
                if data["success"]:
                    self.logged_in = True
                    return sess
            if "password" in data:
                if data["email"] == "userNotFound":
                    raise UserNotFound("User not found.", response=resp)
                if data["password"] == "invalidPassword":
                    raise InvalidPassword("Invalid password.", response=resp)
                elif data["password"] == "wrongLengthMin":
                    raise PasswordTooShort("Password is too short.", response=resp)

            raise APIError("Unknown Error", response=resp)
        
        else:
            self.logged_in = False
            
            return sess

    def article_from_url(self, url:str) -> Article | OwnArticle:
        resp = self.session.get(url)
        check_response(resp, ArticleError, f"Error while getting article")
        try:
            return extract_article(url, resp.text)
        except RequireDynamicLoading as e:
            return extract_article(url, resp.text, self._load_content_dynamic(e.article_id))

    def _load_content_dynamic(self, article_id:int) -> str:
        resp = self.session.post(APIEndpoints.ARTICLE_DYNAMIC.value, json={'articleId':article_id})
        check_response(resp, APIError, "Error while getting dynamic content", (lambda r: r.ok, lambda r: r.json().get('action', None) == 'display'))

        return resp.json()['articleContent']

    def _paginate_raw(self, start_url:str, page_buffer:int=1, first_page_source:str|None=None, total_pages:int|None=None):
        if first_page_source is not None:
            first_page = first_page_source
        else:
            resp = self.session.get(start_url)
            check_response(resp, APIError, "Error while getting start URL")
            first_page = resp.text

        if total_pages is not None:
            total = total_pages
        else:
            total = json.loads(scrape_from_script_tags(RegexPatterns.PAGINATION.value, first_page).group(1))['totalPages']

        if total > 1:
            prepared_requests = [self.session.prepare_request(requests.Request('GET', f"{start_url}/{i}")) for i in range(2, total+1)]
            buf_counter = 1
            buffer_pages = [first_page]
            for prep in (pbar := tqdm(prepared_requests, desc="Getting pages", unit='page', leave=False)):

                if buf_counter % page_buffer == 0:
                    yield from extract_public_articles(*buffer_pages)
                    buffer_pages.clear()

                resp = self.session.send(prep, verify=False)
                check_response(resp, APIError, f"Error while fetching page number {buf_counter+1}")
                buffer_pages.append(resp.text)
                buf_counter += 1

            if len(buffer_pages) > 0:
                yield from extract_public_articles(*buffer_pages)
        
        elif total == 1:
            yield from extract_public_articles(first_page)

    def _new_article(self, **kwargs) -> OwnArticle:
        new_article_resp = self.session.post(APIEndpoints.NEW_ARTICLE.value, json={})
        check_response(new_article_resp, ArticleError, "Error while getting new article editor page")
        new_article = new_article_resp.json()
        article_id = new_article["article"]['id']
        secure_code = new_article['article']['secureCode']
        kwargs['logged_in'] = self.logged_in

        if kwargs.get('privacy', None) is None:
            if self.logged_in:
                kwargs['privacy'] = 'hidden'
            else:
                kwargs['privacy'] = 'public'

        payload = construct_save_json(article_id, secure_code, **kwargs).model_dump()

        resp = self.session.post(APIEndpoints.SAVE_ARTICLE.value, json=payload)
        ret_data = resp.json()

        check_response(resp, CaptchaRequired, "Captcha verification while creating article", (lambda r: r.ok, lambda r: r.json().get('action', None) != 'captcha'))
        check_response(resp, ArticleError, "Error while creating article", (lambda r: r.ok, lambda r: r.json().get('action', None) == 'redirect'))
        
        return self.article_from_url(ROOT+ret_data['url']) #type: ignore

    def _delete_article(self, article:OwnArticle):

        if not article.is_owner:
            raise ArticleError("Can't delete someone else's article")

        resp = self.session.post(APIEndpoints.DELETE_ARTICLE.value.format(article.id, article.secure_code))
        check_response(resp, ArticleError, "Error while deleting article", (lambda r: resp.ok, lambda r: r.json()['status'] == "success"))

    def _edit_article(self, article:OwnArticle, /, **kwargs):

        if not article.is_owner:
            raise ArticleError("Can't edit someone else's article")

        article_properties = {
            "articleId" : article.id, 
            "secureCode" : article.secure_code,
        }
        
        kwargs['logged_in'] = self.logged_in

        resp = self.session.post(APIEndpoints.EXISTING_ARTICLE.value, json=article_properties)
        check_response(resp, APIError, "Requesting edit info failed")

        new_body = copy_save_json(resp.json(), kwargs).model_dump()

        resp = self.session.post(APIEndpoints.SAVE_ARTICLE.value, json=new_body)
        check_response(resp, CaptchaRequired, "Captcha verification while editing article", (lambda r: r.ok, lambda r: r.json().get('action', None) != 'captcha'))
        check_response(resp, ArticleError, "Error while editing article", (lambda r: r.ok, lambda r: r.json().get('action', None) == 'redirect'))

        return self.article_from_url(ROOT+resp.json()['url'])

    def get_user_article_previews(self, user_profile_url:str, page_buffer:int=1, first_page_source:str|None=None):
        if first_page_source is not None:
            first_page = first_page_source
        else:
            resp = self.session.get(user_profile_url)
            check_response(resp, APIError, "Error while getting user profile URL: "+ user_profile_url)
            first_page = resp.text

        total_pages = json.loads(scrape_from_script_tags(RegexPatterns.PAGINATION.value, first_page, 1).group(1))['totalPages']

        return self._paginate_raw(user_profile_url, page_buffer, first_page, total_pages)

    def get_own_article_previews(self, trash=False, page_buffer:int=1, first_page_source:str|None=None):
        if trash:
            url = APIEndpoints.TRASH.value
        else:
            url = APIEndpoints.NOTES.value

        if first_page_source is not None:
            first_page = first_page_source
        else:
            resp = self.session.get(url)
            check_response(resp, APIError, "Error while getting notes: "+ url)
            first_page = resp.text

        total_pages = json.loads(scrape_from_script_tags(RegexPatterns.PAGINATION.value, first_page, 5).group(1))['totalPages']

        return self._paginate_raw(url, page_buffer, first_page, total_pages)

    def load_article_from_preview(self, preview:PublicArticlePreview | ArticlePreview) -> Article | OwnArticle:
        return self.article_from_url(str(preview.url))

    def fetch_user(self, user_profile_url:str) -> User:
        resp = self.session.get(user_profile_url)
        check_response(resp, APIError, "Error while getting user profile URL: "+ user_profile_url)
        profile_page = resp.text

        public_articles = [*self.get_user_article_previews(user_profile_url, 3, profile_page)]
        
        return extract_user(profile_page, public_articles)

        
    def shred_article(self, article:OwnArticle):
        
        resp = self.session.post(APIEndpoints.SHRED_ARTICLE.value.format(article.id, article.secure_code))
        check_response(resp, 
                       ArticleError, 
                       "Error while trying to shred article", 
                       (lambda r: r.ok, lambda r: r.json()['status'] == 'success'))
        
    def restore_article(self, article:OwnArticle):
        
        resp = self.session.post(APIEndpoints.RESTORE_ARTICLE.value.format(article.id, article.secure_code))
        check_response(resp, 
                       ArticleError, 
                       "Error while trying to restore article", 
                       (lambda r: r.ok, lambda r: r.json()['status'] == 'success'))


    def subscribe_to_user(self, user:User):
        """
        Subscribes to user
        ### Parameters:
        - user (User): User object
        """
        data = {"premiumUserId":user.id}
        resp = self.session.post(APIEndpoints.SUBSCRIBE_USER.value, json=data)
        check_response(resp, APIError, "Error while subscribing to user")
        
    def unsubscribe_from_user(self, user:User):
        """
        Unsubscribes from user
        ### Parameters:
        - user (User): User object
        """
        resp = self.session.post(APIEndpoints.UNSUBSCRIBE_USER.value.format(user.id))
        check_response(resp, APIError, "Error while unsubscribing from user")

    def favorite_article(self, article:Article|OwnArticle):
        """
        Adds article to favorites
        ### Parameters:
        - article (Article|OwnArticle): Article
        """
        payl = {"articleId":article.id}
        resp = self.session.post(APIEndpoints.FAVORITE_ARTICLE.value, json=payl)
        check_response(resp, ArticleError, "Error while trying to favorite article")

    def unfavorite_article(self, article:Article|OwnArticle):
        """
        Adds article to favorites
        ### Parameters:
        - article (Article|OwnArticle): Article
        """
        resp = self.session.post(APIEndpoints.FAVORITE_ARTICLE.value.format(article.id))
        check_response(resp, ArticleError, "Error while trying to unfavorite article")

    def get_subscribed_articles(self) -> list[PublicArticlePreview]:
        """
        Returns articles from subscribed users.
        """
        
        resp = self.session.get(APIEndpoints.SUBSCRIBED.value)
        check_response(resp, APIError, "Error while getting subscribed accounts")

        return [*extract_public_articles(resp.text)]
    
    def get_total_stats(self):
        """
        Returns total stats for profile.
        """
        resp = self.session.get(APIEndpoints.STATS.value)
        check_response(resp, APIError, "Error while getting stats page")

        return extract_total_stats(resp.text)


    def new_article(self, **kwargs):

        """Creates a new JustPaste.it page (article).
        ### Parameters:
            - title (str): Title of the article.
            - body (str): Content of the article in HTML.
            - description (str): Description of the article. (deprecated in the website but still accessible by the API) Default=""
            - privacy ("public","hidden","private"): Visibility level of the article. Default="hidden" if logged, else "public"
            - password (str): Password of the article. Default=None
            - require_captcha (bool): State of the captcha status, Captcha will be needed before viewing if set to True. Default=False
            - hide_views (bool): State of the views counter, the counter will be hidden if set to True. Default=False
            - anon_owner (bool): State of the profile link, the article will look anonymous if set to True. Default=False
            - viewonce (bool): State of the article persistence, the article will expire after read once. Default=False
            - tags (list): Tags that will be assigned to the article. Default=[]
            - shared_users (list): If set, only the accounts that are specified will be able to see the article. Default=[] 
            - expiry_date (yyyy-mm-ddTHH-MM-SSZ format e.g: "2023-03-02T00:00:00Z"): If set, the article will be expired after given date. Default=None
        ### Returns: 
            (OwnArticle)
        """

        if isinstance(kwargs.get('expiry_date', None), datetime.datetime):
            kwargs['expiry_date'] = kwargs['expiry_date'].isoformat()+'Z'

        return self._new_article(**kwargs)

    def edit_article(self, article:OwnArticle, /, **kwargs):

        """Edits an existing JustPaste.it page (article).
        ### Parameters:
            - article (OwnArticle): Article to delete
            - title (str): Title of the article.
            - body (str): Content of the article in HTML.
            - description (str): Description of the article. (deprecated in the website but still accessible by the API) Default=""
            - privacy ("public","hidden","private"): Visibility level of the article. Default="hidden" if logged, else "public"
            - password (str): Password of the article. Default=None
            - require_captcha (bool): State of the captcha status, Captcha will be needed before viewing if set to True. Default=False
            - hide_views (bool): State of the views counter, the counter will be hidden if set to True. Default=False
            - anon_owner (bool): State of the profile link, the article will look anonymous if set to True. Default=False
            - viewonce (bool): State of the article persistence, the article will expire after read once. Default=False
            - tags (list): Tags that will be assigned to the article. Default=[]
            - shared_users (list): If set, only the accounts that are specified will be able to see the article. Default=[] 
            - expire_date (yyyy-mm-ddTHH-MM-SSZ format e.g: "2023-03-02T00:00:00Z"): If set, the article will be expired after given date. Default=None"""

        return self._edit_article(article, **kwargs)

    def delete_article(self, article:OwnArticle):
        """Deletes an existing JustPaste.it page (article).
        ### Parameters:
            - article (OwnArticle): Article to delete"""
        
        if article.is_in_trash:
           warnings.warn(f"Article {article.url} is already in trash. Did you mean to restore or shred it?", UserWarning)

        return self._delete_article(article)

    def logout(self):
        
        resp = self.session.post(APIEndpoints.LOGOUT.value)
        check_response(resp, APIError, "Could not logout")


