import re
import json

class Settings:
    """
    justpaste.Settings object to be passed to the main object.
    
    ### Parameters:
        - jp (justpaste.Justpaste): The Justpaste object to be passed. (This is needed for obtaining default values, there are better ways to implement that but oh well)"""
    def __init__(self,jp):
        self.jp = jp

        if not jp.logged:
            raise Exception("User not logged in.")

        self.photo_b = None
        self.bg_b = None
        self.form = None
        self.files_req = dict()
        self.profile_req = dict()
        self.password_req = {
                    "oldPassword":None,
                    "newPassword":None,
                    "newPasswordRepeat":None
                    }
        self.notes_req = {
                        "newArticleVisibilityLevel":None,
                        "newArticleLinkSharingAllowed":None,
                        "newArticleRequireCaptcha":None,
                        "newArticleHideViews":None,
                        "newArticleAnonymizeOwner":None,
                        "newArticleExpireAfterRead":None,
                        "newArticleExpireAfterDate":None
                    }
        self.notification_req = {
                    "sharedArticleEmailNotification":None,
                    "subscribedArticleEmailNotification":None
                    }
        self.privacy_req = {
                    "allowMessages":None
                    }
        self.total_req = dict()
        self.profile_headers = {'accept': 'application/json, text/plain, */*'}

    def _dict_to_multipart_files(self,dict:dict,file:bool=False):
        multipart = {}
        for k,v in dict.items():
            if file:
                multipart.update({k:(v[0],v[1])})
            else:
                multipart.update({k:(None,v)})
            return multipart
        
    def _change_setting(self,mode:str,pair:dict): 
        if mode == "password":
            url = "https://justpaste.it/account/settings/change-password/save"
            if "password" in pair:
                self.password_req.update({"oldPassword":self.jp.password,"newPassword":pair["password"],"newPasswordRepeat":pair["password"]})
            else:
                pass
            self.total_req.update({url:self.password_req})
        elif mode == "notes":
            default = self._get_settings("notes")
            if "saveSettingsUrl" in default:
                del default["saveSettingsUrl"]
            if not any(self.notes_req.values()):
                self.notes_req = default
            url = "https://justpaste.it/account/settings/notes/save"
            for x in self.notes_req:
                if x in pair:
                    self.notes_req.update({x:pair[x]})
                else:
                    pass
            self.total_req.update({url:self.notes_req})
        elif mode == "notification":
            default = self._get_settings("notification")
            if "saveSettingsUrl" in default:
                del default["saveSettingsUrl"]
            if not any(self.notification_req.values()):
                self.notification_req = default
            url = "https://justpaste.it/account/settings/notification/save"
            for x in self.notification_req:
                if x in pair:
                    self.notification_req.update({x:pair[x]})
                else:
                    pass
            self.total_req.update({url:self.notification_req})
        elif mode == "privacy":
            default = self._get_settings("privacy")
            if "saveSettingsUrl" in default:
                del default["saveSettingsUrl"]
            if not any(self.privacy_req.values()):
                self.privacy_req = default
            url = "https://justpaste.it/account/settings/privacy/save"
            for x in self.privacy_req:
                if x in pair:
                    self.privacy_req.update({x:pair[x]})
                else:
                    pass
            self.total_req.update({url:self.privacy_req})
        elif mode == "profile":
            default = self._get_settings("profile")
            url = "https://justpaste.it/account/settings/public-profile/save"
            files = {}
            del default["isPublic"],default["profileLink"],default["avatarUrl"],default["backgroundUrl"]
            if not any(self.profile_req.values()):
                self.profile_req = default
            if "photo" in pair:
                files.update(self._dict_to_multipart_files(pair,file=True))
            if "background" in pair:
                files.update(self._dict_to_multipart_files(pair,file=True))
            else:
                for x in ["name","permalink","description","location","website"]:
                    if x in pair:
                        self.profile_req.update(pair)
                if "removeBackground" in pair and pair["removeBackground"] == True:
                    self.profile_req.update({"removeBackground":True})
                else:
                    self.profile_req.update({"removeBackground":False})
                files.update(self._dict_to_multipart_files({"form":json.dumps(self.profile_req)}))
            self.files_req.update(files)
            self.total_req.update({url:self.files_req})
        else:
            pass

    def _get_settings(self,mode:str):
        if mode == "profile":
            profile_regex = re.compile(r"window\.premiumUserData = (.*);")
            default_values = self.jp._get_json_element(reg=profile_regex,index=5,page="https://justpaste.it/account/settings/public-profile")
            return default_values
        elif mode == "notes":
            notes_regex = re.compile(r"window\.notesSettingsPageSettings = (.*);")
            default_values = self.jp._get_json_element(reg=notes_regex,index=6,page="https://justpaste.it/account/settings/notes")
            return default_values
        elif mode == "notification":
            notification_regex = re.compile(r"window\.notificationSettingsPageSettings = (.*);")
            default_values = self.jp._get_json_element(reg=notification_regex,index=6,page="https://justpaste.it/account/settings/notification")
            return default_values
        elif mode == "privacy":
            privacy_regex = re.compile(r"window\.privacySettingsPageSettings = (.*);")
            default_values = self.jp._get_json_element(reg=privacy_regex,index=6,page="https://justpaste.it/account/settings/privacy")
            return default_values
        else:
            pass
        
    def change(self,key:str,value):
        """
        Changes the given setting (key) with its value (value).

        ### Parameters:
            - key: The setting name.
            - value: The setting value.
        
        ### Possible keys and values:
            - password* (): New password for the account.
            - photo (tuple(filename,bytes)): Sets new image using the image data. (min. 200x200px, best 400x400px)
            - background (tuple(filename,bytes)): Sets new background image using the image data. (1500x500px)
            - name (str): Sets account display name.
            - permalink (str): Sets account link URL (hence the username.).
            - description (str): Sets account description.
            - location (str): Sets location info.
            - website (str): Sets website info.
            - removeBackground (bool): Disables the background if set to True.
            - allowMessages ("everyone","only_contacts","nobody"): Sets who can message you.
            - newArticleVisibilityLevel ("public","hidden","private"): Sets the default value for notes on who can see new notes.
            - newArticleLinkSharingAllowed (bool): Sets the default value for notes on link sharing. (deprecated on GUI)
            - newArticleRequireCaptcha (bool): Sets the default value for notes on which they require captcha or not.
            - newArticleHideViews (bool): Sets the default value for notes on which the views are hidden or not.
            - newArticleAnonymizeOwner (bool): Sets the default value for notes on which the author is hidden or not.
            - newArticleExpireAfterRead (bool): Sets the default value for notes on which the notes will expire after reading or not.
            - newArticleExpireAfterDate (null,"days_3","days_7","days_30","months_3","months_6","years_1"): Sets the default value for notes on expiry date.
            - sharedArticleEmailNotification ("always_notify","only_contacts","never_notify"): Sets if the account owner is notified for new shared notes via email.
            - subscribedArticleEmailNotification ("instantly_notify","hourly_notification","daily_notification","weekly_notification","never_notify"): Sets if and when the account owner is notified when there is a new note from subscribed author via email.
        """
        if key == "password":
            self._change_setting("password",{key:value})
        elif key in self.notes_req:
            self._change_setting("notes",{key:value})
        elif key in self.notification_req:
            self._change_setting("notification",{key:value})
        elif key in self.privacy_req:
            self._change_setting("privacy",{key:value})
        elif key in ["photo","background","name","permalink","description","location","website","removeBackground"]:
            self._change_setting("profile",{key:value})
        else:
            raise Exception("Please specify a supported setting")
        
    def change_bulk(self,dict:dict):
        """
        Changes the dict keys with dict values inside the given list.

        ### Parameters:
            - dict: The dict of key-value pairs that will be changed.
        
        ### Possible keys and values:
            - password* (): New password for the account.
            - photo (tuple(filename,bytes)): Sets new image using the image data. (min. 200x200px, best 400x400px)
            - background (tuple(filename,bytes)): Sets new background image using the image data. (1500x500px)
            - name (str): Sets account display name.
            - permalink (str): Sets account link URL (hence the username.).
            - description (str): Sets account description.
            - location (str): Sets location info.
            - website (str): Sets website info.
            - removeBackground (bool): Disables the background if set to True.
            - allowMessages ("everyone","only_contacts","nobody"): Sets who can message you.
            - newArticleVisibilityLevel ("public","hidden","private"): Sets the default value for notes on who can see new notes.
            - newArticleLinkSharingAllowed (bool): Sets the default value for notes on link sharing. (deprecated on GUI)
            - newArticleRequireCaptcha (bool): Sets the default value for notes on which they require captcha or not.
            - newArticleHideViews (bool): Sets the default value for notes on which the views are hidden or not.
            - newArticleAnonymizeOwner (bool): Sets the default value for notes on which the author is hidden or not.
            - newArticleExpireAfterRead (bool): Sets the default value for notes on which the notes will expire after reading or not.
            - newArticleExpireAfterDate (null,"days_3","days_7","days_30","months_3","months_6","years_1"): Sets the default value for notes on expiry date.
            - sharedArticleEmailNotification ("always_notify","only_contacts","never_notify"): Sets if the account owner is notified for new shared notes via email.
            - subscribedArticleEmailNotification ("instantly_notify","hourly_notification","daily_notification","weekly_notification","never_notify"): Sets if and when the account owner is notified when there is a new note from subscribed author via email.
        """

        for key,value in dict.items():
            if key == "password":
                self._change_setting("password",{key:value})
            elif key in self.notes_req:
                self._change_setting("notes",{key:value})
            elif key in self.notification_req:
                self._change_setting("notification",{key:value})
            elif key in self.privacy_req:
                self._change_setting("privacy",{key:value})
            elif key in ["photo","background","name","permalink","description","location","website","removeBackground"]:
                self._change_setting("profile",{key:value})
            else:
                raise Exception("Please specify a supported setting.")
                    