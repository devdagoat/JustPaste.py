from requests import Request, PreparedRequest, Response
from colorama import Fore
import pprint
from typing import Callable

class RequireDynamicLoading(Exception):
    def __init__(self, article_id:int) -> None:
        self.article_id = article_id
        super().__init__()

class APIError(Exception):
    def __init__(self, message:str, /, request:Request|PreparedRequest|None=None, response:Response|None=None) -> None:
        self.request = request
        self.response = response
        msg = message
        if response is not None:
            msg += f"\nResponse Info:\nHTTP {response.status_code} ({response.reason})"
            msg += f"\nResponse Body:\n"
            try:
                msg += pprint.pformat(response.json())
            except:
                msg += response.text
                

        if request is not None:
            msg += f"\nRequest Info: \nRequest URL: {request.url}"
            msg += f"\nRequest Body:\n{request.body}" #type: ignore
            msg += f"\nRequest Headers:\n{pprint.pformat(request.headers)}"

        super().__init__(msg)

class UserNotFound(APIError):
    pass
class InvalidPassword(APIError):
    pass
class PasswordTooShort(APIError):
    pass

class CaptchaRequired(APIError):
    def __init__(self, message:str, /, request: Request | None = None, response: Response | None = None) -> None:
        print(Fore.YELLOW + 
              "\nCaptcha required. This happens to accounts with no premium purchase history. " +
              "Once purchased, JustPaste will not ask for captcha again even after the premium expires.\n" + 
              Fore.RESET)
        super().__init__(message, request=request, response=response)

class ArticleError(APIError):
    pass

resp_conditions = (
    lambda r: r.ok,
)

def check_response(resp:Response, exc:type[APIError], message:str, conditions:tuple[Callable[[Response], bool], ...] = resp_conditions, *, include_request=True) -> None:
    if not all(c(resp) for c in conditions):
        raise exc(message, request=resp.request if include_request else None, response=resp)