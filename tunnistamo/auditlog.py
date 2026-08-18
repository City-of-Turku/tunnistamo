import logging
from oidc_provider.models import Client


logger = logging.getLogger('tunnistamo.audit')


def _log_audit_message(request, event_name, message, extra_context=None):
    context = {
        'event': event_name,
    }
    if request is not None:
        user = request.user
        context.update({
            'user_ip': request.META['REMOTE_ADDR'],
            'user_uuid': str(user.uuid) if user.is_authenticated else None,
            'user_name': user.get_display_name() if user.is_authenticated else None,
            'path': request.get_full_path(),
            'host': request.get_host(),
        })

    if extra_context is not None:
        context.update(extra_context)

    adapter = logging.LoggerAdapter(logger, context)
    adapter.info(message)


def log_admin_view(request):
    msg = "Admin accessed %s (%s)" % (request.get_full_path(), request.method)
    _log_audit_message(request, 'admin_view', msg)


def log_admin_login_attempt(request, username):
    msg = "Admin login attempt (username '%s')" % username
    _log_audit_message(request, 'admin_login_attempt', msg)


def log_admin_action(request, msg):
    _log_audit_message(request, 'admin_action', msg)


def log_authorize(request):
    client = None
    client_id = request.GET.get('client_id', None)
    if client_id is not None:
        try:
            client = Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            pass

    extra_context = {
        'oidc_client_id': client_id,
        'oidc_client_name': client.name if client else None,
    }
    if request.method == 'GET':
        event_name = 'authorize'
        msg = 'OIDC authorization requested'
    else:
        event_name = 'authorize_post'
        consent = 'allow' if request.POST.get('allow') else 'reject'
        msg = 'OIDC user expressed consent (%s)' % consent

    _log_audit_message(request, event_name, msg, extra_context=extra_context)


def log_authorize_failure(request):
    _log_audit_message(request, 'authorization_failure', 'Authorize failed')


def log_end_session(request):
    _log_audit_message(request, 'end_session', 'OIDC end session requested')


def log_login(request):
    _log_audit_message(request, 'login', 'User requested login')


def log_token_retrieval(request):
    _log_audit_message(request, 'token_retrieval', 'Token requested')


def _log_auth_backend_event(request, event_name, msg, backend_name, identifier):
    extra_context = {'backend': backend_name}
    msg += ' (backend %s' % backend_name
    if identifier is not None:
        extra_context['user_identifier'] = identifier
        msg += ", user identifier '%s'" % identifier
    msg += ')'
    _log_audit_message(request, event_name, msg, extra_context=extra_context)


def log_authentication_request(request, backend_name, identifier=None):
    msg = 'User authentication requested'
    _log_auth_backend_event(request, 'authentication_request', msg, backend_name, identifier)


def log_authentication_failure(request, backend_name, identifier=None):
    msg = 'User authentication failed'
    _log_auth_backend_event(request, 'authentication_failure', msg, backend_name, identifier)


def log_authentication_rate_limited(request, backend_name, identifier=None):
    msg = 'User authentication rate limited'
    _log_auth_backend_event(request, 'authentication_rate_limited', msg, backend_name, identifier)


def log_authentication_success(request, backend_name, identifier=None):
    msg = 'User authentication succeeded'
    _log_auth_backend_event(request, 'authentication_success', msg, backend_name, identifier)
