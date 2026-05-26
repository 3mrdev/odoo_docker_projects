from odoo import http
from odoo.http import request

class LogspaceMockup(http.Controller):

    def _get_mock_context(self, extra=None):
        ctx = {
            'is_mockup': True,
        }
        if extra:
            ctx.update(extra)
        return ctx

    # 1. & 2. Search & List/Grid View
    @http.route(['/mockup/search'], type='http', auth='public', website=True)
    def mockup_search(self, **kwargs):
        trucks = [
            {'id': 1, 'name': 'Standard Flatbed', 'vendor': 'Logistics Pro', 'price': '$150', 'rating': 4.5, 'reviews': 120, 'image': '/web/image/product.template/1/image_256'},
            {'id': 2, 'name': 'Heavy Duty Trailer', 'vendor': 'Quick Haul', 'price': '$250', 'rating': 4.8, 'reviews': 85, 'image': '/web/image/product.template/2/image_256'},
            {'id': 3, 'name': 'Refrigerated Truck', 'vendor': 'Cool Trans', 'price': '$300', 'rating': 4.2, 'reviews': 40, 'image': '/web/image/product.template/3/image_256'},
        ]
        return request.render('appness_logspace_mockup.mockup_search_page', self._get_mock_context({'trucks': trucks}))

    # 3. Vendor Details / Item Page
    @http.route(['/mockup/vendor/<int:vendor_id>'], type='http', auth='public', website=True)
    def mockup_vendor(self, vendor_id, **kwargs):
        vendor = {'id': vendor_id, 'name': 'Logistics Pro', 'rating': 4.5, 'description': 'The best in the business for flatbed transport.'}
        return request.render('appness_logspace_mockup.mockup_vendor_page', self._get_mock_context({'vendor': vendor}))

    # 4. Add-ons Screen
    @http.route(['/mockup/addons'], type='http', auth='public', website=True)
    def mockup_addons(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_addons_page', self._get_mock_context({'step': 1}))

    # 5. Order Details / Setup
    @http.route(['/mockup/details'], type='http', auth='public', website=True)
    def mockup_details(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_details_page', self._get_mock_context({'step': 2}))

    # 6. Checkout Screen
    @http.route(['/mockup/checkout'], type='http', auth='public', website=True)
    def mockup_checkout(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_checkout_page', self._get_mock_context({'step': 3}))

    # 7. Payment Screen
    @http.route(['/mockup/payment'], type='http', auth='public', website=True)
    def mockup_payment(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_payment_page', self._get_mock_context({'step': 4}))

    # 8. Done / Confirmation Screen
    @http.route(['/mockup/done'], type='http', auth='public', website=True)
    def mockup_done(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_done_page', self._get_mock_context({'order_number': 'ORD-100234'}))

    # 9. Login
    @http.route(['/mockup/login'], type='http', auth='public', website=True)
    def mockup_login(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_login_page', self._get_mock_context())

    # 10. SignUp
    @http.route(['/mockup/signup'], type='http', auth='public', website=True)
    def mockup_signup(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_signup_page', self._get_mock_context())

    # 11. Profile
    @http.route(['/mockup/my/profile'], type='http', auth='public', website=True)
    def mockup_profile(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_profile_page', self._get_mock_context())

    # 12. All Orders
    @http.route(['/mockup/my/orders'], type='http', auth='public', website=True)
    def mockup_orders(self, **kwargs):
        orders = [
            {'id': 'ORD-100234', 'date': '2023-10-01', 'status': 'In Transit', 'total': '$150'},
            {'id': 'ORD-100233', 'date': '2023-09-15', 'status': 'Delivered', 'total': '$250'},
        ]
        return request.render('appness_logspace_mockup.mockup_orders_page', self._get_mock_context({'orders': orders}))

    # 13. Order Tracking (Map/Timeline)
    @http.route(['/mockup/my/orders/track'], type='http', auth='public', website=True)
    def mockup_track(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_track_page', self._get_mock_context())

    # 14. Notifications
    @http.route(['/mockup/my/notifications'], type='http', auth='public', website=True)
    def mockup_notifications(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_notifications_page', self._get_mock_context())

    # 15. Rating Screen
    @http.route(['/mockup/rate'], type='http', auth='public', website=True)
    def mockup_rate(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_rate_page', self._get_mock_context())

    # 16. Refund Screen
    @http.route(['/mockup/refund'], type='http', auth='public', website=True)
    def mockup_refund(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_refund_page', self._get_mock_context())

    # 17. Ticket Screen
    @http.route(['/mockup/ticket'], type='http', auth='public', website=True)
    def mockup_ticket(self, **kwargs):
        return request.render('appness_logspace_mockup.mockup_ticket_page', self._get_mock_context())
