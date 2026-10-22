from odoo import models, fields, api, _
from odoo import tools
import logging
_logger = logging.getLogger(__name__)

class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def filter_logspace_menus(self, menu_ids):
        """ Return the ids of the menu items visible to the user. """
        # menu_ids is a SET, so browse() yields records in hash order (id %
        # table size), not ascending id. This whitelist is built in a single
        # forward pass - a menu is kept only if its parent was already listed -
        # so a level-3 menu survives only when its parent happens to be visited
        # first. Sorting by id makes that deterministic: every parent is
        # declared before its children in logspace_menus.xml and therefore has
        # a lower id.
        menu_objs = self.browse(menu_ids).exists().sorted('id')
        # Whitelist seed: the Logspace backend root. Never seed
        # logspace_action_website here - it is an ir.actions.act_url id, not a
        # menu id; comparing it against parent_id would collide with an
        # unrelated menu id. logspace_website_menu (the root menuitem that
        # uses it) is deliberately NOT whitelisted either: providers reach the
        # site from the frontend, and the menu hides for everyone holding the
        # core Website menu (see hide_logspace_menus_to_user).
        root_id = self.env.ref('appness_logspace.menu_logspace_root').id
        mp_menu_list = [root_id] if root_id in menu_ids else []
        for menu in menu_objs:
            if (menu.parent_id.id in mp_menu_list
                    and (not menu.group_ids or menu.group_ids & self.env.user.all_group_ids)):
                mp_menu_list.append(menu.id)
        return mp_menu_list

    def hide_logspace_menus_to_user(self, menu_data):
        """ Return the ids of the menu items hide to the user. """
        menu_ids = []
        core_website_menu_id = self.env.ref(
            'website.menu_website_configuration').id
        if core_website_menu_id in menu_data:
            # Hide the Logspace Website root menu (a menuitem) for users who
            # also have the core Website menu. The historical code removed
            # logspace_action_website - an act_url id, never a menu id - so
            # the dedup was a no-op (or hid an unrelated colliding menu id).
            menu_ids.append(
                self.env.ref('appness_logspace.logspace_website_menu').id,
            )
        else:
            menu_ids = []

        admin_group = self.env.ref(
            'appness_logspace.group_logspace_admin').id
        all_group_ids = self.env.user.sudo().all_group_ids.ids
        if admin_group in all_group_ids:
            try:
                menu_ids.extend((
                    self.env.ref(
                        'appness_logspace.wk_seller_payment_request').id,
                ))
            except Exception as e:
                _logger.warning(
                    "Warning !! Request For Payment menu not found (%r)", e)
                pass
        return menu_ids

    def update_logspace_menus(self, res):
        """Update menu names for marketplace sellers in load_menus dict."""
        if not res:
            return res
        if (
            self.env.user.has_group('appness_logspace.group_logspace_provider')
            and not self.env.user.has_group('appness_logspace.group_logspace_admin')
        ):
            for menu in res.values():
                if menu.get("xmlid") == "appness_logspace.menu_logspace_providers_list":
                    menu["name"] = _("My Profile")
                if menu.get("xmlid") == "appness_logspace.menu_logspace_providers":
                    menu["name"] = _("My Company")

        return res


    def load_menus(self, debug=False):
        """Called by webclient to load menus, safe override in Odoo 19."""
        res = super().load_menus(debug=debug)
        return self.update_logspace_menus(res)

    @api.model
    @tools.ormcache('frozenset(self.env.user.group_ids.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        res = super(IrUiMenu, self)._visible_menu_ids(debug=debug)
        to_remove_menu_ids = self.hide_logspace_menus_to_user(menu_data=res)
        res = res - set(to_remove_menu_ids)
        if self.env.user.has_group('appness_logspace.group_logspace_provider') and not self.env.user.has_group('appness_logspace.group_logspace_admin'):
            mp_menus = self.filter_logspace_menus(res)
            return set(mp_menus)
        return res
