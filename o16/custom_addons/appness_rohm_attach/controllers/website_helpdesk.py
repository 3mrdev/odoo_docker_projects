from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessDenied, ValidationError, UserError
from odoo.addons.website.controllers import form

import base64

class WebsiteForm(form.WebsiteForm):

    def insert_attachment(self, model, id_record, files):
        # Define allowed image formats
        ALLOWED_IMAGE_FORMATS = ["image/jpeg", "image/png", "image/tiff"]
        IrConfigSudo = request.env["ir.config_parameter"].sudo()

        max_attachment_size = IrConfigSudo.get_param("appness_rohm_attach.attachment_size_limit2")
        if max_attachment_size:
            max_attachment_size = float(max_attachment_size)
            max_attachment_size_bytes = max_attachment_size * 1024 * 1024 #Convert MegaBytes to Bytes
        else:
            max_attachment_size = 2
            max_attachment_size_bytes = max_attachment_size * 1024 * 1024 #Convert MegaBytes to Bytes

        model_name = model.model
        if model_name == "helpdesk.ticket":
            for file in files:
                file_bytes = base64.encodebytes(file.read())
                file_size = len(file_bytes) 
                file_size_mb = file_size / 1024 / 1024 
                if hasattr(file, 'mimetype'):
                    if file.mimetype not in ALLOWED_IMAGE_FORMATS:
                        raise UserError(f"Only image files (JPEG, PNG, TIFF) are allowed. \n Your current file is {file.mimetype}")
                
                if file_size > max_attachment_size_bytes:
                    raise UserError(f"The attachment exceed the maximum attachment size please make sure to insert attachment less than or equal to [{max_attachment_size} MB]. \n Your current file size is [{round(file_size_mb,2)} MB]")
                
        return super().insert_attachment(model, id_record, files)
