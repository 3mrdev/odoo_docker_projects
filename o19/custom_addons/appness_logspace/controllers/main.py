from odoo import http
from odoo.http import request

class LogspaceBooking(http.Controller):
    @http.route('/booking', type='http', auth="public", website=True)
    def render_booking_page(self, **kw):
        return request.render('appness_logspace.booking_page_template', {})
