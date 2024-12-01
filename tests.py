from src.justpaste import Justpaste
from src.justpaste.exceptions import *
from src.justpaste.objects import *

import unittest

EMAIL = "<your email here>"
PASSWORD = "<your password here>"

TESTERS = {
    'new_password' : "",
    'own_article_url' : "",
    'article_url' : "",
    'own_article_to_edit_url' : "",
    'own_article_to_delete_url' : "",
    'other_user_url' : "",
    'background_path' : "",
    'photo_path' : "",
    'proxy' : ""
}

justpaste = Justpaste(EMAIL, PASSWORD)

class TestJustpaste(unittest.TestCase): 

    def test_article_from_url(self):
        
        result = justpaste.article_from_url(TESTERS["article_url"])
        assert isinstance(result, Article)
        self.assertIsNotNone(result)
        result = justpaste.article_from_url(TESTERS["own_article_url"])
        assert isinstance(result, OwnArticle)
        self.assertIsNotNone(result)

    def test_new_article(self):
        """Test creating a new article."""

        article = justpaste.new_article(title="Test Title", body="Test Body")

        self.assertIsNotNone(article)  # Assuming article_from_url returns a non-None value

        article = justpaste.new_article(
            title="Test Title",
            body="<p>Test Body</p>",
            description="",
            privacy="hidden",
            password=None,
            require_captcha=False,
            hide_views=False,
            anon_owner=True,
            viewonce=False,
            tags=["test", "article"],
            shared_users=[],
            expiry_date=datetime.datetime(year=2025, month=1, day=1)
        )

        assert isinstance(article, OwnArticle)
        self.assertIsNotNone(article)



    def test_delete_article(self):
        """Test deleting an article."""
        
        article = justpaste.article_from_url(TESTERS["own_article_to_delete_url"])
        assert isinstance(article, OwnArticle)

        justpaste.delete_article(article)

        self.assertTrue(justpaste.article_from_url(TESTERS["own_article_to_delete_url"]).is_in_trash)


    def test_edit_article(self):
        """Test editing an article."""

        article = justpaste.article_from_url(TESTERS["own_article_to_edit_url"])
        assert isinstance(article, OwnArticle)
        
        edited = justpaste.edit_article(article, 
                               title="Hey123",
                               description="",
                               body="Edited now! ")
        
        self.assertEqual(str(edited.url), TESTERS["own_article_to_edit_url"])
        self.assertEqual(edited.title, "Hey123")
        self.assertIn("Edited now!", edited.body)


    def test_get_messages(self):
        """Test getting messages."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        msgs = justpaste.get_messages(user)
        assert len(msgs) > 0


    def test_get_conversation(self):
        """Test getting conversation."""
        conv = justpaste.get_conversation(justpaste.user_from_url(TESTERS["other_user_url"]))
        assert isinstance(conv, Conversation)

    def test_send_message(self):
        """Test sending a message."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        conv1 = justpaste.get_messages(user)
        msg = justpaste.send_message(user, "Testing")
        conv2 = justpaste.get_messages(user)
        assert len(conv2) == len(conv1) + 1



    def test_mute_conversation(self):
        """Test muting a conversation."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        conv = justpaste.get_conversation_info(user)
        justpaste.mute_conversation(conv)

        conv = justpaste.get_conversation_info(user)
        assert conv.muted is True

    def test_unmute_conversation(self):
        """Test unmuting a conversation."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        conv = justpaste.get_conversation_info(user)
        justpaste.unmute_conversation(conv)

        conv = justpaste.get_conversation_info(user)
        assert conv.muted is False

    def test_star_conversation(self):
        """Test starring a conversation."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        conv = justpaste.get_conversation_info(user)
        justpaste.star_conversation(conv)

        conv = justpaste.get_conversation_info(user)
        assert conv.starred is True

    def test_unstar_conversation(self):
        """Test unstarring a conversation."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        conv = justpaste.get_conversation_info(user)
        justpaste.unstar_conversation(conv)

        conv = justpaste.get_conversation_info(user)
        assert conv.starred is False



    def test_add_to_contacts(self):
        """Test adding a user to contacts."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        justpaste.add_to_contacts(user)

    def test_remove_from_contacts(self):
        """Test removing a user from contacts."""
        user = justpaste.user_from_url(TESTERS["other_user_url"])
        justpaste.remove_from_contacts(user)

    def test_change_password(self):
        """Test password change functionality."""

        user = justpaste.user_from_url(TESTERS["other_user_url"])

        justpaste.change_password(TESTERS["new_password"])
        self.assertEqual(justpaste.password, TESTERS["new_password"])

        justpaste.get_conversation(user)

        justpaste.change_password(PASSWORD)
        self.assertEqual(justpaste.password, PASSWORD)

        justpaste.get_conversation(user)
        
    def test_change_settings(self):
        """Test changing multiple settings."""

        with open(TESTERS["photo_path"], 'rb') as buf:
            photo = buf.read()
        with open(TESTERS["background_path"], 'rb') as buf:
            bg = buf.read()

        pairs = {
            "photo" : photo,
            "background" : bg,
            "location" : "yes",
            "allowMessages" : "everyone",
            "newArticleVisibilityLevel" : "hidden",
            "newArticleHideViews" : False,
            "sharedArticleEmailNotification" : "never_notify",
            "removeBackground" : False
        }

        justpaste.change_settings(pairs)

    def test_initialization_without_proxy(self):
        """Test Justpaste initialization without proxy."""

        justpaste_tester = Justpaste(EMAIL, PASSWORD)
        assert isinstance(justpaste_tester.user_from_url(TESTERS["other_user_url"]), User)

    def test_initialization_with_proxy(self):
        """Test Justpaste initialization with proxy."""
        justpaste_tester = Justpaste(EMAIL, PASSWORD, TESTERS["proxy"])
        assert isinstance(justpaste_tester.user_from_url(TESTERS["other_user_url"]), User)



if __name__ == '__main__':
    unittest.main()
