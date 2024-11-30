import requests

from .consts import *
from .objects import *
from .exceptions import *
from .utils import *

class MessagesMixin(JustpasteSessionProto):

    def get_messages(self, user_or_conversation:User|Conversation, before:datetime.datetime|None=None, after:datetime.datetime|None=None) -> list[Message]:
        if isinstance(user_or_conversation, User):
            conversation = self.get_conversation_info(user_or_conversation)
        elif isinstance(user_or_conversation, Conversation):
            conversation = user_or_conversation

        data = {
            "beforeDateTime" : before.isoformat()+'Z' if before else before,
            "afterDateTime" : after.isoformat()+'Z' if after else after
        }

        resp = self.session.post(APIEndpoints.CONVERSATION_CHECK_MESSAGES.value.format(conversation.id), json=data)
        check_response(resp, APIError, "Error while getting messages", (lambda r: r.ok, lambda r: 'messages' in r.json()))

        return [ModelInitializer.message(m) for m in resp.json()['messages']]
    
    def get_conversation(self, user:User, before:datetime.datetime|None=None, after:datetime.datetime|None=None):

        conv = self.get_conversation_info(user)
        conv.messages = self.get_messages(conv, before, after)
        return conv

    def get_conversation_info(self, user:User) -> Conversation:
        username = user.permalink
        data = {"receiverPermalink":username}
        resp = self.session.post(APIEndpoints.CONVERSATION_NEW.value, json=data)
        check_response(resp, APIError, "Error while getting conversation info", (lambda r: r.ok, lambda r: 'conversation' in r.json()))
        return ModelInitializer.conversation(resp.json()['conversation'], user)

    def list_conversations(self, preload=False) -> list[Conversation]:

        resp = self.session.post(APIEndpoints.CONVERSATIONS_LIST.value, json={})
        check_response(resp, 
                       APIError, 
                       "Error while getting conversations list",
                       (lambda r: r.ok, lambda r: 'conversations' in r.json()))
        
        return [ModelInitializer.conversation(c, self.fetch_user(c['interlocutor']['url'])) for c in resp.json()['conversations']]

    def send_message(self, user:User, message:str):

        data = {"receiverPermalink":user.permalink, "message":message}

        resp = self.session.post(APIEndpoints.SEND_MESSAGE.value, json=data)
        check_response(resp,
                        APIError, 
                        f"Error while trying to send \"{message}\" to @{user.permalink}", 
                        (lambda r: r.ok, lambda r: 'success' in r.json() and r.json()['success']))

    def mute_conversation(self, conversation:Conversation):
        data = {'muted': True}

        resp = self.session.post(APIEndpoints.CONVERSATION_MUTE.value.format(conversation.id), json=data)
        check_response(resp, APIError, f"Error while trying to mute the conversation with @{conversation.user.permalink}")
        
    def unmute_conversation(self, conversation:Conversation):
        data = {'muted': False}

        resp = self.session.post(APIEndpoints.CONVERSATION_MUTE.value.format(conversation.id), json=data)
        check_response(resp, APIError, f"Error while trying to unmute the conversation with @{conversation.user.permalink}")
        
    def star_conversation(self, conversation:Conversation):
        data = {'star': True}

        resp = self.session.post(APIEndpoints.CONVERSATION_STAR.value.format(conversation.id), json=data)
        check_response(resp, APIError, f"Error while trying to star the conversation with @{conversation.user.permalink}")
        
    def unstar_conversation(self, conversation:Conversation):
        data = {'star': False}

        resp = self.session.post(APIEndpoints.CONVERSATION_STAR.value.format(conversation.id), json=data)
        check_response(resp, APIError, f"Error while trying to unstar the conversation with @{conversation.user.permalink}")
        

    def add_to_contacts(self, user:User):
        """
        Adds user to contacts
        ### Parameters:
        - user: User object
        """
        payl = {"premiumUserId":user.id}
        resp = self.session.post(APIEndpoints.ADD_TO_CONTACTS.value, json=payl)
        check_response(resp, APIError, f"Error while trying to add @{user.permalink} to contacts")
    
    def remove_from_contacts(self, user:User):
        """
        Removes user from contacts
        ### Parameters:
        - user: User object
        """
        resp = self.session.post(APIEndpoints.DELETE_FROM_CONTACTS.value.format(user.id))
        check_response(resp, APIError, f"Error while trying to remove @{user.permalink} from contacts")

    
