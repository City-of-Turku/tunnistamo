from functools import update_wrapper
from tunnistamo import auditlog, ratelimit

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class TunnistamoAdminSite(admin.AdminSite):
    def admin_view(self, view, cacheable=False):
        """Make admin views emit an audit log event whenever they're called"""

        outer = super().admin_view(view, cacheable)

        def inner(request, *args, **kwargs):
            auditlog.log_admin_view(request)
            return outer(request, *args, **kwargs)

        return update_wrapper(inner, outer)

    @method_decorator(never_cache)
    def login(self, request, extra_context=None):
        if request.method == 'POST':
            username = request.POST.get('username')
            auditlog.log_admin_login_attempt(request, username=username)
            if ratelimit.is_ratelimited(
                request, fn=self.login, key='ip', rate='5/h', increment=True
            ):
                return HttpResponseForbidden('Rate limited')

        return super().login(request, extra_context)


@receiver(post_save, sender=LogEntry)
def handle_log_entry_save(sender, **kwargs):
    obj = kwargs['instance']
    msg = 'Admin action for %s: %s' % (str(obj.content_type), str(obj))
    auditlog.log_admin_action(request=None, msg=msg)
