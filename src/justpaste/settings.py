import re
import requests
import json

from .consts import *
from .utils import *
from .exceptions import *

class SettingsMixin(JustpasteSessionProto):

    settings : dict[Literal['profile', 'notes', 'notification', 'privacy'], dict[str, Any]] = {
        "profile" : {
            "name":None,
            "permalink":None,
            "description":None,
            "location":None,
            "website":None
        },
        "notes" : {
            "newArticleVisibilityLevel":None,
            "newArticleLinkSharingAllowed":None,
            "newArticleRequireCaptcha":None,
            "newArticleHideViews":None,
            "newArticleAnonymizeOwner":None,
            "newArticleExpireAfterRead":None,
            "newArticleExpireAfterDate":None
        },
        "notification" : {
            "sharedArticleEmailNotification":None,
            "subscribedArticleEmailNotification":None
        },
        "privacy" : {
            "allowMessages":None
        },

    }
        
    def change_password(self, new_password:str):
        form = {
            "oldPassword":self.password,
            "newPassword":new_password,
            "newPasswordRepeat":new_password
        }

        resp = self.session.post(APIEndpoints.CHANGE_PASSWORD.value, json=form)
        check_response(resp, APIError, "Could not change password")

        self.__init__(self.email, new_password)

    def _change_setting(self, category:Literal['profile', 'notes', 'notification', 'privacy'], pairs:dict[str, Any]): 
        
        if category == "profile":
            files = {}
            form = {**self.settings["profile"]}
            for name, value in pairs.items():
                if name in ('photo', 'background'):
                    files[name] = ('tmp.'+determine_filetype(value), value)
                else:
                    form[name] = value

            if 'removeBackground' not in pairs:
                form['removeBackground'] = False

            files['form'] = (None, json.dumps(form))

            self.session.headers['Accept'] = 'application/json, text/plain, */*'

            resp = self.session.post(APIEndpoints.PROFILE_SETTINGS_SAVE.value, files=files)
            check_response(resp, APIError, "Error while updating profile settings", (lambda r: r.ok, lambda r: r.json()['success']), include_request=False)

            self.settings['profile'] = without_key(form, 'removeBackground')

        else:
            self.settings[category].update(pairs)
            
            match category:
                case 'notes':
                    url = APIEndpoints.NOTES_SETTINGS_SAVE.value
                case 'notification':
                    url = APIEndpoints.NOTIFICATION_SETTINGS_SAVE.value
                case 'privacy':
                    url = APIEndpoints.PRIVACY_SETTINGS_SAVE.value
                case _:
                    raise ValueError(category + ' is not a valid settings category')
            
            resp = self.session.post(url, json=self.settings[category])
            check_response(resp, APIError, f"Error while updating {category} settings", (lambda r: r.ok, lambda r: r.json()['success']))


    def get_settings(self,mode:Literal['profile', 'notes', 'notification', 'privacy']):
        match mode:
            case "profile":
                resp = self.session.get(APIEndpoints.PROFILE_SETTINGS.value)
                check_response(resp, APIError, "Failed to fetch settings")
                default_values = json.loads(scrape_from_script_tags(RegexPatterns.PREMIUM_USER_DATA.value, resp.text, 5).group(1))
            case "notes":
                resp = self.session.get(APIEndpoints.NOTES_SETTINGS.value)
                check_response(resp, APIError, "Failed to fetch settings")
                default_values = json.loads(scrape_from_script_tags(RegexPatterns.NOTES_SETTINGS_PAGE_SETTINGS.value, resp.text, 6).group(1))
            case "notification":
                resp = self.session.get(APIEndpoints.NOTIFICATION_SETTINGS.value)
                check_response(resp, APIError, "Failed to fetch settings")
                default_values = json.loads(scrape_from_script_tags(RegexPatterns.NOTIFICATION_SETTINGS_PAGE_SETTINGS.value, resp.text, 6).group(1))
            case "privacy":
                resp = self.session.get(APIEndpoints.PRIVACY_SETTINGS.value)
                check_response(resp, APIError, "Failed to fetch settings")
                default_values = json.loads(scrape_from_script_tags(RegexPatterns.PRIVACY_SETTINGS_PAGE_SETTINGS.value, resp.text, 6).group(1))
            case _:
                raise ValueError(f"{mode} is not a valid settings category")
            
        return default_values
    
    def load_all_settings(self):
        for setting in self.settings:
            defaults = self.get_settings(setting)
            for k, v in defaults.items():
                if k in ("saveSettingsUrl", "isPublic", "profileLink", "avatarUrl", "backgroundUrl"):
                    continue
                self.settings[setting][k] = v

        self.category_map : dict[str, str] = {}
        for category, mapping in self.settings.items():
            if category == 'profile':
                self.category_map.update({
                    k.casefold(): category
                    for k in
                    (*mapping.keys(), "photo", "background", "removeBackground")
                    })
            else:
                self.category_map.update({
                    k.casefold(): category
                    for k in
                    mapping.keys()
                })


    def change_settings(self, pairs:dict[str, Any], /):
        """
        Changes the dict keys with dict values inside the given list.

        ### Parameters:
            - dict: The dict of key-value pairs that will be changed.
        
        ### Possible keys and values:
            - password* (): New password for the account.
            - photo (bytes): Sets new image using the image data. (min. 200x200px, best 400x400px)
            - background (bytes): Sets new background image using the image data. (1500x500px)
            - name (str): Sets account display name.
            - permalink (str): Sets account link URL (hence the username.).
            - description (str): Sets account description.
            - location (str): Sets location info.
            - website (str): Sets website info.
            - removeBackground (bool): Disables the background if set to True.
            - allowMessages ("everyone","only_contacts","nobody"): Sets who can message you.
            - newArticleVisibilityLevel ("public","hidden","private"): Sets the default value for articles on who can see new articles.
            - newArticleLinkSharingAllowed (bool): Sets the default value for articles on link sharing. (deprecated on GUI)
            - newArticleRequireCaptcha (bool): Sets the default value for articles on which they require captcha or not.
            - newArticleHideViews (bool): Sets the default value for articles on which the views are hidden or not.
            - newArticleAnonymizeOwner (bool): Sets the default value for articles on which the author is hidden or not.
            - newArticleExpireAfterRead (bool): Sets the default value for articles on which the articles will expire after reading or not.
            - newArticleExpireAfterDate (null,"days_3","days_7","days_30","months_3","months_6","years_1"): Sets the default value for articles on expiry date.
            - sharedArticleEmailNotification ("always_notify","only_contacts","never_notify"): Sets if the account owner is notified for new shared articles via email.
            - subscribedArticleEmailNotification ("instantly_notify","hourly_notification","daily_notification","weekly_notification","never_notify"): Sets if and when the account owner is notified when there is a new article from subscribed author via email.
        """
        settings_to_update = {}

        for key,value in pairs.items():
            if key == "password":
                self.change_password(value)

            category = self.category_map.get(key.casefold(), sentinel)
            if category is sentinel:
                raise ValueError(f"{key} is not a supported setting")
            else:
                if category not in settings_to_update:
                    settings_to_update[category] = {}
                settings_to_update[category][key] = value
        
        for category, mapping in settings_to_update.items():
            self._change_setting(category, mapping)


                    