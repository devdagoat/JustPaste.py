import requests
import re
import json
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
            elif type(self.s) == tuple:
                print(self.s[1])
                print("Continuing anonymously.")
                self.s = self.s[0]
                self.logged = False

    def _login(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0",
                "Sec-Ch-Ua": '"Chromium";v="108", "Opera";v="94", "Not)A;Brand";v="99"'}
        payl = {"email":self.email,"password":self.password,"rememberMe":True}
        sess = requests.Session()
        sess.headers.update(headers)
        resp = sess.post("https://justpaste.it/api/v1/login",json=payl).json()
        #print(f)
        if "password" in resp:
            if resp["password"] == "invalidPassword":
                return sess,"Invalid password."
            elif resp["password"] == "wrongLengthMin":
                return sess,"Password is too short."
            elif resp["email"] == "userNotFound":
                return sess,"User not found."
            else:
                return sess,"Unknown Error"
        if "success" in resp:
            if resp["success"]:
                return sess
        else:
            return sess,"Unknown Error"
        
    def _api_request(self,reqtype:str,uri:str=None,payload=None,field=None,host="https://justpaste.it",files=None):
        if not uri:
            dest = host
        else:
            if uri.startswith(("https://","http://")):
                dest = uri
            else:
                if not uri.startswith("/"):
                    uri = "/" + uri
                dest = host + uri
        reqtype = reqtype.upper()
        if type(payload) == dict:
            if type(files) == bool and files == True:
                resp = self.s.request(reqtype,dest,files=payload)
            elif type(files) == dict:
                resp = self.s.request(reqtype,dest,json=payload,files=files)
            else:
                resp = self.s.request(reqtype,dest,json=payload)
        elif type(payload) == str:
            resp = self.s.request(reqtype,dest,data=payload)
        else:
            resp = self.s.request(reqtype,dest)

        try:
            resp = resp.json()
        except json.decoder.JSONDecodeError or requests.exceptions.JSONDecodeError or ValueError:
            pass

        if field:
            if field in resp:
                return resp[field]
        else:
            return resp

    def _get_attrs(self,url:str):
        regxid1 = re.compile(r'"id":(.*),"secureCode"')
        regxid2 = re.compile(r'"id":(.*),"url"')
        regxsc = re.compile(r'"secureCode":(.*),"editUrl"')
        secure_code = ""
        try:
            id = self._get_json_element(regxid1,1,url)
            secure_code = self._get_json_element(regxsc,1,url)
        except:
            id = self._get_json_element(regxid2,1,url)
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
        resp1 = self._api_request("post","/api/v1/new-article","{}","article")
        _sc = resp1["secureCode"]
        _id = resp1["id"]
        payl = self._construct_body(_id=_id,_sc=_sc,*args,**kwargs)
        payl["articleId"] = _id
        payl["secureCode"] = _sc
        resp = self._api_request("post","/api/v1/save-article",payl)
        if resp["action"] == "redirect":
            if return_attr:
                return _id,_sc
            else:
                return "https://justpaste.it" + str(resp["url"])
        elif resp["action"] == "captcha":
            raise Exception("Captcha detected, for now only premium users can use this function.")

    def _delete_note(self,_id,_sc):
        result = self._api_request("post",f"/account/manage/delete/{_id}/{_sc}",None,"status")
        if result == "success":
            return True
        else:
            raise Exception("Could not delete the note. Did you log in with the right account?")

    def _edit_note(self,_id,_sc,*args,**kwargs):
        note_properties = {"articleId":_id,"secureCode":_sc}
        resp = self._api_request("post","/api/v1/existing-article",note_properties,"article")
        new_id = resp["id"]
        new_sc = resp["secureCode"]
        new_body = self._construct_body(new_id,new_sc,*args,**kwargs)
        result = self._api_request("post","/api/v1/save-article",new_body,"success")
        if result == True:
            return True
        else:
            raise Exception("Could not edit the note. Did you log in with the right account?")

    def _fetch_info(self,info:str=None,profile_url=None,improve_avatar_res=False):
        if profile_url:
            regx1 = re.compile(r"window\.pagePremiumUser = (.*);")
            regx2 = re.compile(r"window\.showPremiumUser = (.*);")
            dict_info = {}
            dict_info.update(self._get_json_element(regx1,1,profile_url))
            dict_info.update(self._get_json_element(regx2,1,profile_url))
        else:
            regx = re.compile(r"window\.mainPanelOptions = (.*);")
            dict_info = self._get_json_element(regx,0,"https://justpaste.it/")
        if info:
            value = str(dict_info[info])
            if value.startswith("/"):
                if info == "userAvatar":
                    if improve_avatar_res:
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
        if page_suffix:
            page = page + page_suffix
        resp = self._api_request("get",page)
        soup = BeautifulSoup(resp.content,"html.parser")
        scripts = soup.find_all("script")
        script = str(scripts[index])
        result = re.search(reg,script).group(1)
        return json.loads(result)

    def _fetch_notes(self,trash=False):
        note_data = re.compile(r"window\.articlesData = (.*);")
        page_num_data = re.compile(r"window\.pagination = (.*);")
        if trash:
            page = "https://justpaste.it/account/trash/"
        else:
            page = "https://justpaste.it/account/manage/"
        try:
            notes_list = []
            max_pages = self._get_json_element(page_num_data,5,page)["totalPages"]
            for i in range(max_pages):
                notes = self._get_json_element(note_data,5,page,page_suffix=str(i+1))
                for note in notes:
                    notes_list.append(note)
            return notes_list
        except IndexError:
            raise Exception("Couldn't load notes")

    def _find_by_title(self,string:str):
        res = []
        for note in self._fetch_notes():
            if string in note["title"]:
                res.append({note["title"]:note["url"]})
        return res
    
    def _apply_settings(self,settings):
        result = dict()
        for url in settings.total_req:
            if url == "https://justpaste.it/account/settings/public-profile/save":
                self.s.headers.update(settings.profile_headers)
                resp = self._api_request("post",url,settings.files_req,files=True)
            else:
                self.s.headers.update({"Content-Type": "application/json"})
                resp = self._api_request("post",url,settings.total_req[url])
                if url == "https://justpaste.it/account/settings/change-password/save" and "success" in resp.json():
                    self._logout()
                    self.__init__(self.email,settings.total_req[url]["newPassword"])
            result.update({url:resp})
        return result
    
    def _get_conv_info(self,url):
        username = self._fetch_info(profile_url=url)["permalink"]
        check_payl = {"receiverPermalink":username}
        return self._api_request("post","/api/v1/conversation/new",check_payl,"conversation",host="https://msg.justpaste.it")

    def _get_note_info(self,url):
        full_info = {}
        regx1 = re.compile(r"window\.article = (.*);")
        regx2 = re.compile(r"window\.barOptions = (.*);")
        info1 = self._get_json_element(regx1,1,url)
        info2 = self._get_json_element(regx2,1,url)
        full_info.update(info1)
        full_info.update(info2)
        return full_info
    
    def _decide_the_fate_of_note_in_trash(self,action,_id,_sc):
        resp = self._api_request("post",f"/account/trash/{action}/{_id}/{_sc}")
        if resp["status"] == "success":
            if str(resp["id"]) == str(_id):
                return True
        else:
            return resp
        
    def _shred_note(self,_id,_sc):
        return self._decide_the_fate_of_note_in_trash("delete",_id,_sc)
    
    def _restore_note(self,_id,_sc):
        return self._decide_the_fate_of_note_in_trash("restore",_id,_sc)

    def subscribe_to_user(self,url):
        """
        Subscribes to user
        ### Parameters:
        - url (str): Url of user profile
        """
        user_id = self._fetch_info(profile_url=url)["id"]
        payl = {"premiumUserId":user_id}
        return self._api_request("post","/api/account/v1/subscribed-user",payl)
        
    def unsubscribe_from_user(self,url):
        """
        Unsubscribes from user
        ### Parameters:
        - url (str): Url of user profile
        """
        user_id = self._fetch_info(profile_url=url)["id"]
        return self._api_request("post",f"/api/account/v1/subscribed-user-delete/{user_id}",None)
       
    def add_to_contacts(self,url):
        """
        Adds user to contacts
        ### Parameters:
        - url (str): Url of user profile
        """
        user_id = self._fetch_info(profile_url=url)["id"]
        payl = {"premiumUserId":user_id}
        return self._api_request("post","/api/account/v1/contact-user",payl)
    
    def remove_from_contacts(self,url):
        """
        Removes user from contacts
        ### Parameters:
        - url (str): Url of user profile
        """
        user_id = self._fetch_info(profile_url=url)["id"]
        return self._api_request("post",f"/api/account/v1/contact-user-delete/{user_id}",None)
    
    def send_msg(self,url,msg):
        """
        Sends message to user*
        ### Parameters:
        - url (str): Url of user profile
        - msg (str): The message that will be sent

        #### Important:
        The user needs to be in contacts in order for messages to show up in website.
        """
        username = self._fetch_info(profile_url=url)["permalink"]
        payl = {"receiverPermalink":username,"message":msg}
        return self._api_request("post","/api/v1/message/send",payl,"success",host="https://msg.justpaste.it")
        
    def check_msgs(self,url,before=None,after=None):
        """
        Checks for new messages
        ### Parameters:
        - url (str): Url of user profile
        - before (time in format yyyy-mm-ddTHH-MM-SS.fff+zz e.g: 2023-02-26T04:26:04.000+03:00): Fetch for messages sent before this date Default: None 
        - after (time in format yyyy-mm-ddTHH-MM-SS.fff+zz e.g: 2023-02-26T04:26:04.000+03:00): Fetch for messages sent after this date Default: None 
        """
        conv_id = self._get_conv_info(url)["id"]
        payl = {"beforeDateTime":before,"afterDateTime":after}
        return self._api_request("post",f"/api/v1/conversation/{conv_id}/message",payl,"messages",host="https://msg.justpaste.it")
        
    def get_user_info(self,url):
        """
        Returns info about given user

        ### Parameters:
            - url (str): The url of profile
        """
        return self._fetch_info(profile_url=url)

    def mute_conv(self,url):
        """
        Mutes conversation
        ### Parameters:
        - url (str): Url of user profile
        """
        conv_id = self._get_conv_info(url)["id"]
        payl = {"muted":True}
        return self._api_request("post",f"/api/v1/conversation/{conv_id}/mute",payl,host="https://msg.justpaste.it")
    
    def unmute_conv(self,url):
        """
        Unmutes conversation
        ### Parameters:
        - url (str): Url of user profile
        """
        conv_id = self._get_conv_info(url)["id"]
        payl = {"muted":False}
        return self._api_request("post",f"/api/v1/conversation/{conv_id}/mute",payl,host="https://msg.justpaste.it")
    
    def star_conv(self,url):
        """
        Adds star to conversation
        ### Parameters:
        - url (str): Url of user profile
        - star (bool): State of the star 
        """
        conv_id = self._get_conv_info(url)["id"]
        payl = {"star":True}
        return self._api_request("post",f"/api/v1/conversation/{conv_id}/star",payl,host="https://msg.justpaste.it")
    
    def unstar_conv(self,url):
        """
        Removes star from conversation
        ### Parameters:
        - url (str): Url of user profile
        - star (bool): State of the star 
        """
        conv_id = self._get_conv_info(url)["id"]
        payl = {"star":False}
        return self._api_request("post",f"/api/v1/conversation/{conv_id}/star",payl,host="https://msg.justpaste.it")

    def list_msgs(self):
        """
        Lists all conversations
        """
        return self._api_request("post","/api/v1/conversation/list",{},"conversations",host="https://msg.justpaste.it")

    def fav_note(self,url):
        """
        Adds note to favorites
        ### Parameters:
        - url (str): Url of note
        """
        article_id = self._get_attrs(url)[0]
        payl = {"articleId":int(article_id)}
        return self._api_request("post","/api/account/v1/favourite-article",payl)
    
    def unfav_note(self,url):
        """
        Removes note from favorites
        ### Parameters:
        - url (str): Url of note
        """
        article_id = self._get_attrs(url)[0]
        return self._api_request("post",f"/api/account/v1/favourite-article-delete/{article_id}",None)
    
    def get_subscribed_notes(self):
        """
        Returns notes from subscribed users.
        """
        regx = re.compile(r"window\.publicArticlesData = (.*);")
        return self._get_json_element(regx,5,"https://justpaste.it/account/subscribed")
    
    def get_total_stats(self):
        """
        Returns total stats for profile.
        """
        regx = re.compile(r"window\.articlesStatsData = (.*);")
        return self._get_json_element(regx,5,"https://justpaste.it/account/articles-stats")

    def get_note_info(self,url):
        """
        Returns info about the given note
        
        ### Parameters:
            - url (str): The url of note"""
        return self._get_note_info(url)

    def shred_note(self,url):
        """
        Permanently deletes the note in trash.

        ### Parameters:
            - url (str): The url of note
        """

        article_id,secure_code = self._get_attrs(url)
        return self._shred_note(article_id,secure_code)
    
    def restore_note(self,url):
        """
        Restores the note in trash.

        ### Parameters:
            - url (str): The url of note
        """

        article_id,secure_code = self._get_attrs(url)
        return self._restore_note(article_id,secure_code)
    def apply_settings(self,settings):

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

    def fetch_notes(self,trash = False,verbose = False):
        """Returns the notes in the format of {title*:link} format.**
        ### Parameters:
            - verbose (bool): If set to True, everything (Article ID, Secure code, creation date etc.) about the note is returned instead. Default=False
            - trash (bool): If set to True, returns notes from trash instead.
        *If a link does not have a title, first ~60 characters of the body is passed instead. (This is a result of the website API.)"""
        
        if verbose:
            return self._fetch_notes(trash)
        else:
            notes_list = []
            for note in self._fetch_notes(trash):
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

    def _logout(self):
        result = self._api_request("post","/logout",None,"success")
        if result == True:
            return True
        else:
            raise Exception("Could not logout")


