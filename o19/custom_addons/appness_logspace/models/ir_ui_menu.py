from odoo import models, fields, api, _
from odoo import tools
import logging
_logger = logging.getLogger(__name__)

class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def filter_logspace_menus(self, menu_ids):
        """ Return the ids of the menu items visible to the user. """
        menu_objs = self.browse(menu_ids).exists()
        mp_menu_list = [
            self.env.ref('appness_logspace.logspace_action_website').id, 
            self.env.ref('appness_logspace.menu_logspace_root').id,
            self.env.ref('appness_logspace.menu_logspace_configuration').id,
        ]
        for menu in menu_objs:
            if menu.parent_id.id in mp_menu_list:
                mp_menu_list.append(menu.id)
        return mp_menu_list

    def hide_logspace_menus_to_user(self, menu_data):
        """ Return the ids of the menu items hide to the user. """
        menu_ids = []
        core_website_menu_id = self.env.ref(
            'website.menu_website_configuration').id
        if core_website_menu_id in menu_data:
            menu_ids.extend((
                self.env.ref('appness_logspace.logspace_action_website').id,
            ))
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
