from odoo import models

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """
        Inherit: Update the value of 'max_attachment_size' to the session. 
        """
        session_info = super().session_info()
        IrConfigSudo = self.env["ir.config_parameter"].sudo()

        max_attachment_size = IrConfigSudo.get_param("appness_swms_portal.attachment_size_limit")
        if max_attachment_size:
            max_attachment_size = float(max_attachment_size)
            max_attachment_size *= 1024 * 1024 #Convert MegaBytes to bytes
            session_info.update({
                "max_attachment_size": max_attachment_size,
            })
        else:
            session_info.update({
                "max_attachment_size": 2 * 1024 * 1024, #2 MegaBytes to bytes
            })
        
        return session_info