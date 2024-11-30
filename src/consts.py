from enum import Enum
import re

from random_user_agent.user_agent import UserAgent

FILE_MAGIC_BYTES = {
    "png":"89504E470D0A1A0A",
    "jpg":"FFD8FF",
    "bmp":"424D"
}

#USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0"

USER_AGENT = UserAgent().get_random_user_agent()

CAMEL_TO_SNAKE_REGEX = re.compile(r"([a-z]+|[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z]))+?")

class RegexPatterns(Enum):

    MESSAGE_EMOJI_ONLYEMOJI = re.compile(r"(<span class=\"onlyEmojiText\">)(<span class=\"anyEmojiText\">)(.*)(</span>)(</span>)")
    MESSAGE_EMOJI_ANYEMOJI = re.compile(r"(.*)(<span class=\"anyEmojiText\">)(.*)(</span>)(.*)")

    ARTICLE = re.compile(r"window\.article = (.*);")
    BAR_OPTIONS = re.compile(r"window\.barOptions = (.*);")

    PAGE_PREMIUM_USER = re.compile(r"window\.pagePremiumUser = (.*);")
    SHOW_PREMIUM_USER = re.compile(r"window\.showPremiumUser = (.*);")

    PUBLIC_ARTICLES_DATA = re.compile(r"window\.publicArticlesData = (.*);")
    ARTICLES_DATA = re.compile(r"window\.articlesData = (.*);")
    PAGINATION = re.compile(r"window\.pagination = (.*);")

    ARTICLES_STATS_DATA = re.compile(r"window\.articlesStatsData = (.*);")

    PREMIUM_USER_DATA = re.compile(r"window\.premiumUserData = (.*);")
    NOTES_SETTINGS_PAGE_SETTINGS = re.compile(r"window\.notesSettingsPageSettings = (.*);")
    NOTIFICATION_SETTINGS_PAGE_SETTINGS = re.compile(r"window\.notificationSettingsPageSettings = (.*);")
    PRIVACY_SETTINGS_PAGE_SETTINGS = re.compile(r"window\.privacySettingsPageSettings = (.*);")

ROOT = "https://justpaste.it"

API_ROOT = ROOT+"/api/v1"
ACCOUNT_ROOT = ROOT+"/account"
ACCOUNT_API_ROOT = ROOT+"/api/account/v1"
MESSAGE_API_ROOT = "https://msg.justpaste.it/api/v1"
SETTINGS_API_ROOT = ACCOUNT_ROOT+"/settings"

class APIEndpoints(Enum):
    LOGIN = API_ROOT+"/login"
    LOGOUT = API_ROOT+"/logout"

    NEW_ARTICLE = API_ROOT+"/new-article"
    EXISTING_ARTICLE = API_ROOT+"/existing-article"
    SAVE_ARTICLE = API_ROOT+"/save-article"

    DELETE_ARTICLE = ACCOUNT_ROOT+"/manage/delete/{}/{}"
    SHRED_ARTICLE = ACCOUNT_ROOT+"/trash/delete/{}/{}"
    RESTORE_ARTICLE = ACCOUNT_ROOT+"/trash/restore/{}/{}"

    ARTICLE_DYNAMIC = API_ROOT+"/article-dynamic"

    FAVORITE_ARTICLE = ACCOUNT_API_ROOT+"/favourite-article"
    UNFAVORITE_ARTICLE = ACCOUNT_API_ROOT+"/favorite-article-delete/{}"
    SUBSCRIBE_USER = ACCOUNT_API_ROOT+"/subscribed-user"
    UNSUBSCRIBE_USER = ACCOUNT_API_ROOT+"/subscribed-user-delete/{}"
    ADD_TO_CONTACTS = ACCOUNT_API_ROOT+"/contact-user"
    DELETE_FROM_CONTACTS = ACCOUNT_API_ROOT+"/contact-user-delete/{}"

    NOTES = ACCOUNT_ROOT+"/manage"
    TRASH = ACCOUNT_ROOT+"/trash"
    SUBSCRIBED = ACCOUNT_ROOT+"/subscribed"
    STATS = ACCOUNT_ROOT+"/articles-stats"

    CONVERSATION_NEW = MESSAGE_API_ROOT+"/conversation/new"
    CONVERSATION_CHECK_MESSAGES = MESSAGE_API_ROOT+"/conversation/{}/message"
    CONVERSATION_MUTE = MESSAGE_API_ROOT+"/conversation/{}/mute"
    CONVERSATION_STAR = MESSAGE_API_ROOT+"/conversation/{}/star"
    CONVERSATIONS_LIST = MESSAGE_API_ROOT+"/conversation/list"
    SEND_MESSAGE = MESSAGE_API_ROOT+"/message/send"

    CHANGE_PASSWORD = SETTINGS_API_ROOT+"/change-password/save"

    NOTES_SETTINGS = SETTINGS_API_ROOT+"/notes"
    NOTIFICATION_SETTINGS = SETTINGS_API_ROOT+"/notification"
    PRIVACY_SETTINGS = SETTINGS_API_ROOT+"/privacy"
    PROFILE_SETTINGS = SETTINGS_API_ROOT+"/public-profile"

    NOTES_SETTINGS_SAVE = SETTINGS_API_ROOT+"/notes/save"
    NOTIFICATION_SETTINGS_SAVE = SETTINGS_API_ROOT+"/notification/save"
    PRIVACY_SETTINGS_SAVE = SETTINGS_API_ROOT+"/privacy/save"
    PROFILE_SETTINGS_SAVE = SETTINGS_API_ROOT+"/public-profile/save"
