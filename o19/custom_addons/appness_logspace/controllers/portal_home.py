# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

from .common import LogspaceController


class LogspacePortalHome(LogspaceController, CustomerPortal):
    """Send the core portal landing routes to the Logspace pages.

    Why this class has to exist, and why it has these two bases
    -----------------------------------------------------------
    Odoo builds its routing map from *leaf* controller classes only
    (http.py::_generate_routing_rules -> get_leaf_classes -> build_controllers),
    and one dynamic class is created per top-level controller of every installed
    module. Every controller in this module descends from LogspaceController, so
    they are all merged into a single dynamic class whose rules are inserted into
    the werkzeug map BEFORE the ones built from portal.CustomerPortal. Ties on an
    identical static path are broken by insertion order, so that merged class
    wins /my, /my/home and /my/account.

    LogspacePaymentController already inherits payment.controllers.portal.
    PaymentPortal (it calls _create_transaction, _validate_transaction_kwargs and
    friends through self), which drags portal.CustomerPortal's whole route surface
    into that merged class. Two consequences, both observed on a live o19_db_5:

      * /my/home resolved to the inherited core home(), not to logspace_my_account
        - inside one merged class the endpoint methods are enumerated
        alphabetically, and 'home' sorts before 'logspace_my_account'.
      * /my/account resolved to the inherited core account() and 500'd for every
        portal user, because that merged class reaches portal.CustomerPortal
        WITHOUT passing through account.PortalAccount - the override that supplies
        `invoice_sending_methods`, which portal.portal_my_details then does
        len(...) on:  TypeError: object of type 'NoneType' has no len().

    Defining the two endpoints here puts them in a leaf of BOTH inheritance trees
    (LogspaceController's and portal.CustomerPortal's), so C3 places this class
    ahead of portal.CustomerPortal in every merged controller. That makes the
    override deterministic instead of dependent on alphabetical enumeration or on
    which module happens to sort first.

    Inheriting LogspaceController (not only CustomerPortal) is what matters: a
    class that inherited CustomerPortal alone would join portal's merged class but
    NOT ours, and ours is the one that is inserted first and therefore wins.
    """

    # @http.route() with no arguments is the documented override form: the
    # decorator only sets original_routing['routes'] when a path is given, so the
    # merge in _generate_routing_rules keeps the parent's paths, auth, website flag
    # and list_as_website_content ("User Dashboard", which feeds Website ->
    # Technical Pages). Restating them here would be the thing that breaks that.
    @http.route()
    def home(self, **kw):
        """/my and /my/home -> the Logspace account page, for every portal user.

        The core dashboard is deliberately not served: this module replaces the
        portal home outright. If core cards (sales, invoices) are wanted later they
        should be added to logspace_my_account one by one rather than by handing
        this route back to portal.portal_my_home.
        """
        return request.redirect('/logspace/my')

    @http.route()
    def account(self, **kwargs):
        """/my/account -> the Logspace profile page.

        Also the fix for the 500 described above: this module intends /my/account
        to serve logspace_profile (that path is in its route list) but the
        inherited core endpoint used to win it and crash.
        """
        return request.redirect('/logspace/my/profile')
