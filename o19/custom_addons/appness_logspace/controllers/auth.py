# -*- coding: utf-8 -*-
import urllib.parse

from odoo import http
from odoo.http import request

from .common import LogspaceController


class LogspaceAuth(LogspaceController):
    """Authentication routes.

    The old mockup login/signup pages authenticated nobody - the login form
    just navigated to /logspace/my/orders and the signup form to
    /logspace/my/profile, so both are retired as redirects to Odoo's real
    endpoints. The paths stay alive so old links, emails and bookmarks keep
    working.
    """

    @http.route(['/logspace/login'], type='http', auth='public', website=True)
    def logspace_login(self, **kwargs):
        redirect = kwargs.get('redirect', '/logspace/my')
        # /logspace/my already branches per role (My Deliveries for a driver,
        # My Orders for a customer).
        return request.redirect(
            '/web/login?redirect=' + urllib.parse.quote(redirect, safe=''))

    @http.route(['/logspace/signup'], type='http', auth='public', website=True)
    def logspace_signup(self, **kwargs):
        redirect = kwargs.get('redirect', '/logspace/my/profile')
        return request.redirect(
            '/web/signup?redirect=' + urllib.parse.quote(redirect, safe=''))
