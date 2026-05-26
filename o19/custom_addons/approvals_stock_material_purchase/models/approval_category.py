from odoo import api, fields, models


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[
        ('stock_material_purchase', 'Stock Transfer + Purchase')
    ])

    # Sequential transfer creation configuration
    transfer_creation_mode = fields.Selection([
        ('manual', 'Manual - User creates transfer after PO receipt'),
        ('auto_on_validate', 'Automatic - Create when receipt is validated'),
    ],
    string='Transfer Creation Mode',
    default='manual',
    help="When PO receipt is validated, how should the internal transfers be created?")

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        """Override to set required fields for combined type."""
        super()._onchange_approval_type()
        if self.approval_type == 'stock_material_purchase':
            self.has_product = 'required'
            self.has_quantity = 'required'
