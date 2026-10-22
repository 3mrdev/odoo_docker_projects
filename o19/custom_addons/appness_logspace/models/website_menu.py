# -*- coding: utf-8 -*-
from odoo import models

# The url of this module's own "My Orders" top-navbar entry, created in
# data/website_menu.xml.
#
# Matched on url rather than resolved by xmlid on purpose: website.menu.create()
# (addons/website/models/website_menu.py:110-152) copies a parent-less main-menu
# record once per website and then binds the xmlid to an extra website_id=False
# row that never renders. Verified in o19_db_5, where the single record in
# data/website_menu.xml exists as TWO rows: id 10 (website_id=1, the one users
# see) and id 11 (website_id=False, the one env.ref() resolves to). Filtering by
# xmlid would therefore have changed nothing.
LOGSPACE_MY_ORDERS_URL = '/logspace/my/orders'


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    def _compute_visible(self):
        super()._compute_visible()
        user = self.env.user
        # Internal users are designers here: they need every menu present in the
        # recordset or they cannot edit the header in the website editor.
        if user._is_internal():
            return
        # Only a logged-in customer has orders to look at. An anonymous visitor
        # gets bounced to the login page by the auth='user' route behind this url,
        # and a driver delivers orders assigned by a provider rather than placing
        # any - their page is /logspace/driver/orders.
        #
        # This cannot be expressed with website.menu.group_ids: that field is an
        # allowlist enforced by an ir.rule (addons/website/security/
        # website_security.xml:27-31), and "not a driver" is not a group - a driver
        # holds base.group_portal exactly like a customer does.
        is_customer = not user._is_public() and not user.partner_id.is_driver
        if is_customer:
            return
        for menu in self.filtered(lambda m: m.url == LOGSPACE_MY_ORDERS_URL):
            menu.is_visible = False
