from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_om_pasi_establishment_no = fields.Char(
        string="PASI Establishment Number",
        help="Establishment number registered with the Public Authority for Social Insurance",
    )
    l10n_om_cr_number = fields.Char(
        string="Commercial Registration (CR) Number",
        help="Commercial Registration number issued by the Ministry of Commerce and Industry",
    )
    l10n_om_wps_reference = fields.Char(
        string="WPS Bank Reference",
        help="Bank reference for the Wage Protection System (WPS)",
    )
