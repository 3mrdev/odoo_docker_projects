# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from .common import LogspaceController


class LogspaceAuth(LogspaceController):
    """Authentication routes: login and signup."""

    @http.route(['/logspace/login'], type='http', auth='public', website=True)
    def logspace_login(self, **kwargs):
        """Screen 9: Simple login (no OTP)"""
        return request.render('appness_logspace.logspace_login_page',
                              self._get_page_context({'redirect': kwargs.get('redirect', '/logspace/my/orders')}))

    # Screen 10: Signup (simplified, NO OTP)
    @http.route(['/logspace/signup'], type='http', auth='public', website=True)
    def logspace_signup(self, **kwargs):
        """Screen 10: Simple signup (no OTP)"""
        return request.render('appness_logspace.logspace_signup_page',
                              self._get_page_context({'redirect': kwargs.get('redirect', '/logspace/my/profile')}))

