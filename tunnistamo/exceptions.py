from django.utils.translation import gettext_lazy as _
from social_core.exceptions import SocialAuthBaseException


class FriendlySocialAuthException(SocialAuthBaseException):
    """An Exception with a user-friendly, translated message."""

    def __init__(self, message=None):
        if not message and hasattr(self, 'default_message'):
            message = self.default_message
        super().__init__(message)


class AuthBackendUnavailable(FriendlySocialAuthException):
    default_message = _('Authentication method temporarily unavailable.')


class AccountTemporarilyLocked(FriendlySocialAuthException):
    default_message = _('Your account is temporarily locked. Please try again later.')
