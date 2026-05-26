from odoo import models

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """
        Inherit: Update the value of 'max_attachment_size' to the session. # T7329
        """
        session_info = super().session_info()
        IrConfigSudo = self.env["ir.config_parameter"].sudo()

        max_attachment_size1 = IrConfigSudo.get_param("appness_rohm_attach.attachment_size_limit1")
        if max_attachment_size1:
            max_attachment_size1 = float(max_attachment_size1)
            max_attachment_size1 *= 1024 * 1024 #Convert MegaBytes to bytes
            session_info.update({
                "max_attachment_size1": max_attachment_size1,
            })
        else:
            session_info.update({
                "max_attachment_size1": 2 * 1024 * 1024, #2 MegaBytes to bytes
            })
        
        max_attachment_size2 = IrConfigSudo.get_param("appness_rohm_attach.attachment_size_limit2")
        if max_attachment_size2:
            max_attachment_size2 = float(max_attachment_size2)
            max_attachment_size2 *= 1024 * 1024 #Convert MegaBytes to bytes
            session_info.update({
                "max_attachment_size2": max_attachment_size2,
            })
        else:
            session_info.update({
                "max_attachment_size2": 2 * 1024 * 1024, #2 MegaBytes to bytes
            })

        return session_info