import requests
import re
import json
from bs4 import BeautifulSoup
from .settings import Settings


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
            elif type(self.s) == tuple:
                print(self.s[1])
                print("Continuing anonymously.")
                self.s = self.s[0]
                self.logged = False

    def _login(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0",
                "Sec-Ch-Ua": '"Chromium";v="108", "Opera";v="94", "Not)A;Brand";v="99"'}
        payl = {"email":self.email,"password":self.password,"rememberMe":True}
        r = requests.Session()
        r.headers.update(headers)
        f = r.post("https://justpaste.it/api/v1/login",json=payl).json()
        #print(f)
        if "password" in f:
            if f["password"] == "invalidPassword":
                return r,"Invalid password."
            elif f["password"] == "wrongLengthMin":
                return r,"Password is too short."
            elif f["email"] == "userNotFound":
                return r,"User not found."
            else:
                return r,"Unknown Error"
        if "success" in f:
            if f["success"]:
                return r
        else:
            return r,"Unknown Error"
        
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

    def _construct_body(self,
    _id,
    _sc,
    title:str,
    body:str,
    privacy=None,
    path="",
    password=None,
    anon_owner=False,
    hide_views=False,
    require_captcha=False,
    shared_users:list=[],
    tags:list=[],
    description="",
    expire_date:str=None,
    viewonce=False):
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
            raise Exception("Could not delete the note. Did you log in with the right account?")

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
                raise Exception("Could not edit the note. Did you log in with the right account?")
        else:
            print(r2)

    def _fetch_info(self,info:str=None):
        resp = self.s.get("https://justpaste.it/")
        soup = BeautifulSoup(resp.content,"html.parser")
        raw_info = re.search("window.mainPanelOptions = (.*);",str(soup.find_all("script")[0])).group(1)
        dict_info = json.loads(raw_info)
        if info:
            value = str(dict_info[info])
            if value.startswith("/"):
                if info == "userAvatar":
                    if value.endswith("/20") or value.endswith("/40"):
                        return "https://justpaste.it" + value + "0"
                    else: 
                        return "https://justpaste.it" + value
                else:
                    return "https://justpaste.it" + value
            else:
                return value
        else:
            return dict_info

    def _get_json_element(self,reg,index:int,page=None,page_suffix=''):
        manage_page = f"https://justpaste.it/account/manage/{page_suffix}"
        if not page:
            page = manage_page
        resp = self.s.get(page)
        soup = BeautifulSoup(resp.content,"html.parser")
        scripts = soup.find_all("script")
        script = str(scripts[index])
        result = re.search(reg,script).group(1)
        return json.loads(result)

    def _fetch_notes(self):
        note_data = re.compile(r"window\.articlesData = (.*);")
        page_num_data = re.compile(r"window\.pagination = (.*);")
        try:
            notes_list = []
            max_pages = self._get_json_element(page_num_data,5)["totalPages"]
            for i in range(max_pages):
                notes = self._get_json_element(note_data,5,str(i+1))
                for note in notes:
                    notes_list.append(note)
            return notes_list
        except IndexError:
            print("Couldn't load notes")

    def _find_by_title(self,string:str):
        res = []
        for note in self._fetch_notes():
            if string in note["title"]:
                res.append({note["title"]:note["url"]})
        return res
        
    def _apply_settings(self,settings:Settings):
        result = dict()
        for url in settings.total_req:
            if url == "https://justpaste.it/account/settings/public-profile/save":
                self.s.headers.update(settings.profile_headers)
                resp = self.s.post(url,files=settings.files_req)
            else:
                self.s.headers.update({"Content-Type": "application/json"})
                resp = self.s.post(url,json=settings.total_req[url])
                if url == "https://justpaste.it/account/settings/change-password/save" and "success" in resp.json():
                    self._logout()
                    self.__init__(self.email,settings.total_req[url]["newPassword"])
            result.update({url:resp})
        return result

    def apply_settings(self,settings:Settings):

        """Applies the settings to the account.
        ### Parameters:
            - settings: The justpaste.Settings object to be passed.
        """
        return self._apply_settings(settings)
    def find_by_title(self,string:str):
        """Searches for the specified string in note titles and returns them in {title*:link} format.
        ### Parameters:
            - string (str): The string that is searched for.

        *if a note does not have a title, first ~60 characters of the body are searched instead"""
        
        return self._find_by_title(string)

    def fetch_notes(self,verbose = False):
        """Returns the notes that aren't in the trash in the format of {title*:link} format.**
        ### Parameters:
            - verbose (bool): If set to True, everything (Article ID, Secure code, creation date etc.) about the note is returned instead. Default=False

        *If a link does not have a title, first ~60 characters of the body is passed instead. (This is a result of the website API.)"""

        if verbose:
            return self._fetch_notes()
        else:
            notes_list = []
            for note in self._fetch_notes():
                notes_list.append({note["title"]:note["url"]})
            return notes_list

    def fetch_info(self,info:str):
        """Fetches information about the account that is used.
        ### Parameters:
        - info: The information that is to be fetched.
        #### Values: 
        - 'userEmail': Returns user email
        - 'userPermalink': Returns username
        - 'userAvatar': Returns avatar URL
        - 'userProfileIsPublic': Returns if the profile is public
        - 'userProfileLink': Returns user profile"""

        if not self.logged:
            raise Exception("An account is not used to return its properties.")
        else:
            return self._fetch_info(info)


    def new_note(self,*args,**kwargs):

        """Creates a new JustPaste.it page (note).
        ### Parameters:
            - title (str): Title of the note.
            - body (str): Content of the note in HTML.
            - description (str): Description of the note. (deprecated in the website but still accessible by the API) Default=""
            - privacy ("public","hidden","private"): Visibility level of the note. Default="hidden" if logged, else "public"
            - password (str): Password of the note. Default=None
            - require_captcha (bool): State of the captcha status, Captcha will be needed before viewing if set to True. Default=False
            - hide_views (bool): State of the views counter, the counter will be hidden if set to True. Default=False
            - anon_owner (bool): State of the profile link, the note will look anonymous if set to True. Default=False
            - viewonce (bool): State of the note persistence, the note will expire after read once. Default=False
            - tags (list): Tags that will be assigned to the note. Default=[]
            - shared_users (list): If set, only the accounts that are specified will be able to see the note. Default=[] #WIP
            - expire_date (yyyy-mm-ddTHH-MM-SSZ format e.g: "2023-03-02T00:00:00Z"): If set, the note will be expired after given date. Default=None"""

        return self._new_note(*args,**kwargs)

    def edit_note(self,url:str,*args,**kwargs):

        """Edits an existing JustPaste.it page (note).
        ### Parameters:
            - title (str): Title of the note.
            - body (str): Content of the note in HTML.
            - description (str): Description of the note. (deprecated in the website but still accessible by the API) Default=""
            - privacy ("public","hidden","private"): Visibility level of the note. Default="hidden" if logged, else "public"
            - password (str): Password of the note. Default=None
            - require_captcha (bool): State of the captcha status, Captcha will be needed before viewing if set to True. Default=False
            - hide_views (bool): State of the views counter, the counter will be hidden if set to True. Default=False
            - anon_owner (bool): State of the profile link, the note will look anonymous if set to True. Default=False
            - viewonce (bool): State of the note persistence, the note will expire after read once. Default=False
            - tags (list): Tags that will be assigned to the note. Default=[]
            - shared_users (list): If set, only the accounts that are specified will be able to see the note. Default=[] #WIP
            - expire_date (yyyy-mm-ddTHH-MM-SSZ format e.g: "2023-03-02T00:00:00Z"): If set, the note will be expired after given date. Default=None"""

        path = url.strip("/")[-5:]
        article_id,secure_code = self._get_attrs(url)
        return self._edit_note(_id=article_id,_sc=secure_code,path=path,*args,**kwargs)

    def delete_note(self,url,*args,**kwargs):
        """Deletes an existing JustPaste.it page (note).
        ### Parameters:
            - url (str): URL of the page."""
        article_id,secure_code = self._get_attrs(url)
        return self._delete_note(_id=article_id,_sc=secure_code,*args,**kwargs)

    def _logout(self): # idk why this exists but hey 
        r = self.s.post("https://justpaste.it/logout").json()
        if r["success"] == True:
            return True
        else:
            raise Exception("Could not logout")


