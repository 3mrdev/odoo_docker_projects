from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Define allowed image formats for maintenance requests
ALLOWED_IMAGE_FORMATS = ['image/jpeg', 'image/png', 'image/tiff']
RESTRICTED_MODELS = ['maintenance.request']

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.constrains('file_size', 'mimetype','res_model')
    def _check_file_size_and_format(self):
        """
        Override create to validate file size and format for maintenance.request attachments
        """
        for record in self:
            # Check if attachment is for a restricted model
            if record.res_model in RESTRICTED_MODELS:
                # Get max attachment size from config parameter
                max_size = self.env['ir.config_parameter'].sudo().get_param(
                    'fb_wajiz_maintenance.max_attachment_size', '2'
                )
                max_size_bytes = float(max_size) * 1024 * 1024  # Convert MB to bytes

                record_request = self.env['maintenance.request'].browse(record.res_id)
                
                # Check file size
                file_size = record.file_size
                if file_size > max_size_bytes:
                    msg = _(
                        "The attachment exceeds the maximum size of %s MB. "
                        "Please upload a smaller file. (Current size: %.2f MB)"
                    ) % (max_size, file_size / (1024 * 1024))
                    record_request.message_post(body=msg)
                    raise ValidationError(msg)
                
                # Check file format (mimetype)
                mimetype = record.mimetype
                if mimetype and mimetype not in ALLOWED_IMAGE_FORMATS:
                    msg = _(
                        "Only image files (JPEG, PNG, TIFF) are allowed for maintenance requests. "
                        "Your file type: %s"
                    ) % mimetype
                    record_request.message_post(body=msg)
                    raise ValidationError(msg)

    def unlink(self):
        for record in self:
            if record.res_model in RESTRICTED_MODELS:
                record_request = self.env['maintenance.request'].browse(record.res_id)
                if self.env.user.has_group('maintenance.group_equipment_manager'):
                    record_request.message_post(body="Attachment deleted by " + self.env.user.name)
                else:
                    raise UserError(_("You cannot delete attachment of maintenance request you are not authorized please contact your admin"))

        return super(IrAttachment, self).unlink()

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """
        Inherit: Update the value of 'max_attachment_size' to the session. # T7329
        """
        session_info = super().session_info()
        IrConfigSudo = self.env["ir.config_parameter"].sudo()

        max_attachment_size = IrConfigSudo.get_param("fb_wajiz_maintenance.max_attachment_size")
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