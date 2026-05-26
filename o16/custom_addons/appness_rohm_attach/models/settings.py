from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    max_file_attachment_size1 = fields.Float(
        string="Maximum File Size (Projects)",
        help="Set the file size in MegaBytes.",
        config_parameter="appness_rohm_attach.attachment_size_limit1",
        default=2
    )

    max_file_attachment_size2 = fields.Float(
        string="Maximum File Size (Helpdesk)",
        help="Set the file size in MegaBytes.",
        config_parameter="appness_rohm_attach.attachment_size_limit2",
        default=2
    )
