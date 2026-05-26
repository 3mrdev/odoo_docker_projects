from odoo import http
from odoo.http import request
import json
import datetime

class ZKTeco(http.Controller):

    @http.route(['/zkteco/sync'], type='http', auth='public', methods=['POST'], website=True, csrf=False, cors='*')
    def attendance_sync(self, api_key=False, device=False,attendance=False):
        values = {}
        
        try:
            if (api_key and device and attendance) or request.httprequest.data:

                if request.httprequest.data:
                    data = json.loads(request.httprequest.data)
                    api_key = data["api_key"]
                    device = data["device"]
                    attendance = data["attendance"]
                else:
                    attendance = json.loads(attendance)

                device_id = request.env["fb.zkteco.device"].sudo().search([
                    ('name', '=', device),
                    ('api_key', '=', api_key),
                    ('allow','=',True),
                ])
                if device_id:
                    # for attendance in attendances:
                    attendance_id = request.env["fb.zkteco.attendance"].sudo().create({
                        "name":attendance["name"],
                        "device":device_id.id,
                        "timestamp":attendance["timestamp"],
                        "check_type":"in" if attendance["status1"] == 0 else "out"
                    })
                    if attendance_id:
                        values['success'] = True
                        device_id.online = datetime.datetime.now()
                else:
                    values['success'] = False
                    values['error_code'] = 2
                    values['error_data'] = f'Device {device} not found'
            else:
                values['success'] = False
                values['error_code'] = 1
                values['error_data'] = 'Misisng Params'
        except Exception as e:
            values['success'] = False
            values['error_code'] = 0
            values['error_data'] = str(e)

        return json.dumps(values)