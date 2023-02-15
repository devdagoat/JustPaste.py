import requests
import re
from bs4 import BeautifulSoup


class Justpaste:
    """### A simple JustPaste.it API.
    
    Class args:
        email: Email address of the account,
        password: Password of the account.
    
    Methods:
        new_note(title,body,...): Creates new note (premium account only due to captcha check.)
        edit_note(url,title,body,...): Edits note in the URL
        delete_note(url): Deletes note in the URL

For now only creating new notes trigger captcha.
    """
    def __init__(self,email:str=None,password:str=None):
        self.email = email
        self.password = password
        self.logged = False
        self.s = self._login()
        if self.s:
            if type(self.s) == requests.Session:
                self.logged = True
            else:
                print(self.s)
                print("Continuing anonymously.")
                self.logged = False
        else:
            print("Something else happened while logging in, continuing anonymously.")
            self.logged = False

    def _login(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0",
                "Sec-Ch-Ua": '"Chromium";v="108", "Opera";v="94", "Not)A;Brand";v="99"'}
        payl = {"email":self.email,"password":self.password,"rememberMe":True}
        r = requests.Session()
        f = r.post("https://justpaste.it/api/v1/login",headers=headers,json=payl).json()
        #print(f)
        if "password" in f:
            if f["password"] == "invalidPassword":
                return "Invalid password."
            elif f["password"] == "wrongLengthMin":
                return "Password is too short."
            elif f["email"] == "userNotFound":
                return "User not found."
            else:
                pass
        if "success" in f:
            if f["success"]:
                return r
        else:
            pass
        
    def _get_attrs(self,url:str):
        r = self.s.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        for res in soup.find_all("script"):
            try:
                secure_code = re.search('"secureCode":"(.*)","editUrl"',str(res.contents)).group(1)
            except:
                continue
            try:
                id = re.search('"id":(.*),"secureCode"',str(res.contents)).group(1)
            except:
                continue
        return id,secure_code

    def _construct_body(self,_id,_sc,title:str,body:str,privacy=None,path="",password=None,anon_owner=False,hide_views=False,require_captcha=False,shared_users:list=[],tags:list=[],description="",expire_date:int=None,viewonce=False):
        if not privacy:
            if self.logged:
                privacy = "hidden"
            else:
                privacy = "public"
        payl = {
                    "articleId":_id,
                    "secureCode":_sc,
                    "content":body,
                    "captcha":None,
                    "path":path,
                    "visibilityLevel":privacy,
                    "password":password,
                    "repeatPassword":password,
                    "tags":tags,
                    "sharedUsers":shared_users,
                    "title":title,
                    "linkSharingAllowed":False,
                    "description":description,
                    "articleViewRequiresCaptcha":require_captcha,
                    "hideViews":hide_views,
                    "anonymizeOwner":anon_owner,
                    "expireAfterDate":expire_date,
                    "expireAfterRead":viewonce,
                    "isLoggedUser":self.logged,
                    "sH":1080,
                    "sW":1920
                }
        return payl

    def _new_note(self,return_attr = False,*args,**kwargs):
        r1 = self.s.post("https://justpaste.it/api/v1/new-article",data="{}").json()
        if "status" in r1:
            if r1["status"] == 429:
                raise Exception("Rate Limit detected, for now only premium users can use this function.")
        _sc = r1["article"]["secureCode"]
        _id = r1["article"]["id"]
        payl = self._construct_body(_id=_id,_sc=_sc,*args,**kwargs)
        payl["articleId"] = _id
        payl["secureCode"] = _sc
        r = self.s.post("https://justpaste.it/api/v1/save-article",json=payl).json()
        if r["action"] == "redirect":
            if return_attr:
                return _id,_sc
            else:
                return "https://justpaste.it" + str(r["url"])
        elif r["action"] == "captcha":
            raise Exception("Captcha detected, for now only premium users can use this function.")

    def _delete_note(self,_id,_sc):
        r = self.s.post(f"https://justpaste.it/account/manage/delete/{_id}/{_sc}").json()
        if r['status'] == "success":
            return True
        else:
            pass

    def _edit_note(self,_id,_sc,*args,**kwargs):
        note_properties = {"articleId":_id,"secureCode":_sc}
        r = self.s.post("https://justpaste.it/api/v1/existing-article",json=note_properties).json()
        new_id = r["article"]["id"]
        new_sc = r["article"]["secureCode"]
        new_body = self._construct_body(new_id,new_sc,*args,**kwargs)
        r2 = self.s.post("https://justpaste.it/api/v1/save-article",json=new_body).json()
        if "success" in r2:
            if r2["success"] == True:
                return True
            else:
                pass
        else:
            print(r2)

    def new_note(self,*args,**kwargs):

        """Creates a new JustPaste.it page (note).
        ### Parameters:
            - title (str): Title of the note.
            - body (str): Content of the note.
            - description (str): Description of the note. (deprecated in the website but still accessible by the API) Default=""
            - privacy ("public","hidden","private"): Visibility level of the note. Default="hidden" if logged, else "public"
            - password (str): Password of the note. Default=None
            - require_captcha (bool): State of the captcha status, Captcha will be needed before viewing if set to True. Default=False
            - hide_views (bool): State of the views counter, the counter will be hidden if set to True. Default=False
            - anon_owner (bool): State of the profile link, the note will look anonymous if set to True. Default=False
            - viewonce (bool): State of the note persistence, the note will expire after read once. Default=False
            - tags (list): Tags that will be assigned to the note. Default=[]
            - shared_users (list): If set, only the accounts that are specified will be able to see the note. Default=[] #WIP
            - expire_date (int): If set, the note will be expired after the timestamp date. Default=None"""

        return self._new_note(*args,**kwargs)

    def edit_note(self,url:str,*args,**kwargs):

        """Edits an existing JustPaste.it page (note).
        ### Parameters:
            - url (str): URL of the page.
            - title (str): Title of the note.
            - body (str): Content of the note.
            - description (str): Description of the note. (deprecated in the website but still accessible by the API) Default=""
            - privacy ("public","hidden","private"): Visibility level of the note. Default="hidden" if logged, else "public"
            - password (str): Password of the note. Default=None
            - require_captcha (bool): State of the captcha status, Captcha will be needed before viewing if set to True. Default=False
            - hide_views (bool): State of the views counter, the counter will be hidden if set to True. Default=False
            - anon_owner (bool): State of the profile link, the note will look anonymous if set to True. Default=False
            - viewonce (bool): State of the note persistence, the note will expire after read once. Default=False
            - tags (list): Tags that will be assigned to the note. Default=[]
            - shared_users (list): If set, only the accounts that are specified will be able to see the note. Default=[] #WIP
            - expire_date (int): If set, the note will be expired after the timestamp date. Default=None"""

        path = url.strip("/")[-5:]
        article_id,secure_code = self._get_attrs(url)
        return self._edit_note(_id=article_id,_sc=secure_code,path=path,*args,**kwargs)

    def delete_note(self,url,*args,**kwargs):
        """Deletes an existing JustPaste.it page (note).
        ### Parameters:
            - url (str): URL of the page."""
        article_id,secure_code = self._get_attrs(url)
        return self._delete_note(_id=article_id,_sc=secure_code,*args,**kwargs)

    def _logout(self):
        r = self.s.post("https://justpaste.it/logout").json()
        if r["success"] == True:
            return self.s
        else:
            return "could_not_logout"


