import requests

from typing import Any
from urllib.parse import urlparse
from requests.auth import HTTPProxyAuth

from .base import JustpasteBase
from .settings import SettingsMixin
from .messages import MessagesMixin

class Justpaste(
    JustpasteBase,
    SettingsMixin,
    MessagesMixin
    ):
    
    def __init__(self, email: str | None = None, password: str | None = None, proxy: str | None = None):

        if proxy:
            session = requests.Session()
            parsed_proxy = urlparse(proxy)
            proxies = {
                "http" : proxy,
                "https" : proxy
            }
            if parsed_proxy.username or parsed_proxy.password:
                session.auth = HTTPProxyAuth(
                    parsed_proxy.username if parsed_proxy.username else '', 
                    parsed_proxy.password if parsed_proxy.password else '')
                
            session.proxies = proxies
        else:
            session = None

        super().__init__(email, password, session)
        self.load_all_settings()