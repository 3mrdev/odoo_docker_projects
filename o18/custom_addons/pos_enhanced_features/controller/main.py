# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.point_of_sale.controllers.main import PosController
import logging
import werkzeug

_logger = logging.getLogger(__name__)


class POSController(PosController):
    """
    Override POS controller to mark session when user accesses POS
    """
    
    @http.route('/pos/ui', type='http', auth='user')
    def pos_ui(self, config_id=False, **kw):
        """Mark this session as a POS session"""
        # Set a flag in the session to indicate this is a POS user
        request.session['is_pos_session'] = True
        _logger.info(f"[POS Security] Session marked as POS session: {request.session.sid}")
        
        # Continue with normal POS loading
        return super(POSController, self).pos_ui(config_id=config_id, **kw)


class POSBackendSecurity(Home):
    """
    Override web controller to block POS sessions from accessing backend
    """

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        """
        Check if this is a POS session trying to access backend
        """
        # Check if session is marked as POS session
        is_pos_session = request.session.get('is_pos_session', False)
        
        if is_pos_session:
            _logger.warning(
                f"[POS Security] BLOCKED: POS session attempted backend access. "
                f"Session: {request.session.sid}, "
                f"User: {request.session.get('login', 'Unknown')}, "
                f"IP: {request.httprequest.remote_addr}"
            )
            
            # Clear the session completely
            request.session.logout(keep_db=True)
            
            # Redirect to login with error message
            redirect_url = '/web/login?error=access_denied'
            return werkzeug.utils.redirect(redirect_url)
        
        # Normal backend access - allow it
        return super(POSBackendSecurity, self).web_client(s_action=s_action, **kw)
    
    
    @http.route('/web/webclient', type='http', auth="none")
    def web_webclient(self, s_action=None, **kw):
        """
        Also protect the webclient route
        """
        is_pos_session = request.session.get('is_pos_session', False)
        
        if is_pos_session:
            _logger.warning(f"[POS Security] Blocked webclient access from POS session")
            request.session.logout(keep_db=True)
            return werkzeug.utils.redirect('/web/login')
        
        return super(POSBackendSecurity, self).web_webclient(s_action=s_action, **kw)