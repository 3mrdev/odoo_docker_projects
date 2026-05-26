from ast import literal_eval
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.http import request
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.modules.registry import Registry
import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    otp = fields.Char(string="Otp")
    
    @classmethod
    def _login(cls, db, credential, user_agent_env):
        try:
            return super()._login(db, credential, user_agent_env=user_agent_env)
        except AccessDenied as e:
            if credential['type'] == 'otp':
                with Registry(db).cursor() as cr:
                    login = credential['login']
                    cr.execute("SELECT id FROM res_users WHERE lower(login)=%s", (login,))
                    res = cr.fetchone()
                    if res:
                        return {
                            'uid': res[0],
                            'auth_method': 'otp',
                            'mfa': 'skip',
                        }
                    raise e

    def _check_credentials(self, credential, env):
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            if credential['type'] == 'otp':
                if credential['password'] == self.env.user.otp:
                    return {
                        'uid': self.env.user.id,
                        'auth_method': 'otp',
                        'mfa': 'skip',
                    }
            raise