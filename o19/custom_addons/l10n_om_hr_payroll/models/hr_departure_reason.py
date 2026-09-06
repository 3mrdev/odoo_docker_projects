from odoo import fields, models


class HrDepartureReason(models.Model):
    _inherit = "hr.departure.reason"

    l10n_om_reason_type = fields.Selection([
        ('fired', "Fired"),
        ('resigned', "Resigned"),
        ('retired', "Retired"),
        ('end_of_contract', "End of Contract"),
        ('gross_misconduct', "Gross Misconduct"),
    ], default='resigned')
