# import werkzeug
import json
import requests 
import math 
import random
import werkzeug
import logging

from datetime import datetime, timedelta
from collections import defaultdict
from werkzeug.urls import url_encode

from operator import itemgetter
from markupsafe import Markup

from odoo import http,Command,_
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools import groupby as groupbyelem
from odoo.addons.web.controllers.home import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.osv.expression import AND, FALSE_DOMAIN
from . import portal_general,portal_form

_logger = logging.getLogger(__name__)

def generateOTP() : 
    digits = "0123456789"
    OTP = "" 
    for i in range(4) : 
        OTP += digits[int(math.floor(random.random() * 10))] 
    return OTP 

class OAuthLoginOtp(AuthSignupHome):

    def _prepare_signup_values(self, qcontext):
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password','phone','is_family','family_type','company_type') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        return values

    def get_auth_signup_config(self):
        response = super(OAuthLoginOtp, self).get_auth_signup_config()
        company_id = request.env['res.company'].sudo().search([('id','=',1)])
        response.update({
            'signup_otp': company_id.use_otp_login,
        })
        return response
    
    # @http.route('/phoneexist', type='http', auth="public", website=True, methods=['GET'], csrf=False)
    # def validate_referral_code(self, **kwargs):
    #     """Controller for validating referral codes"""
    #     result_dict = {}
    #     params_keys = list(kwargs.keys())
    #     phone = kwargs['sendto']
    #     name = kwargs['name']
    #     if phone and name:
    #         partner_ids = request.env['res.users'].sudo().search(['|',('phone','=',phone),('login','=',name)])
    #         if partner_ids:
    #             return "False"
    #         else:
    #             return "True"
    #     return json.dumps(result_dict)
    
    # @http.route('/portal/session/set_login_time', type='json', auth='user')
    # def set_login_time(self):
    #     
    #         if not request.session.get('portal_login_time'):
    #             request.session['portal_login_time'] = datetime.utcnow().isoformat()
    #     return {"status": "ok"}

    # @http.route('/portal/session/check_timeout', type='json', auth='user')
    # def check_timeout(self):
    #     if not request.env.user.has_group('base.group_portal'):
    #         return {"timeout": False}
    #     login_time = request.session.get('portal_login_time')
    #     if login_time:
    #         try:
    #             dt_login = datetime.fromisoformat(login_time)
    #             if (datetime.utcnow() - dt_login).total_seconds() > 10:
    #                 return {"timeout": True}
    #         except Exception:
    #             pass
    #     return {"timeout": False}

    @http.route('/web/request_otp', type='http', auth='public', website=True, sitemap=False)
    def web_auth_request_otp(self, *args, **kw):
        qcontext = request.params.copy()
        #TODO: change the company in multi-company env
        # company_id = request.env['res.company'].sudo().search([('id', '=', 1)])
        company_id = request.env.company
        
        # raise UserError(f"{request.env.user}")
        if request.env.user.has_group('base.group_portal'):
            return request.redirect('/my')

        if request.env.user.has_group('base.group_user'):
            return request.redirect('/web')

        # try:
        if qcontext.get('mobile'):
            otp = generateOTP()
            # qcontext.update({'otp_original': otp})
            #TODO: change phone country key
            mobile = str(qcontext.get('mobile'))
            user_id = request.env['res.users'].sudo().search([('phone', '=', qcontext.get('mobile'))], limit=1)
            if user_id:
                qcontext.update({'user': user_id.id})
                user_id.otp = otp
                request.session['swms_otp'] = otp
                request.session['swms_user'] = user_id.id
                request.session['swms_phone'] = qcontext.get('mobile')
            else:
                # TODO: Send OTP for new users
                request.session['swms_otp'] = otp
                request.session['swms_user'] = False
                request.session['swms_phone'] = qcontext.get('mobile')
                company_id.sudo().message_post(message_type='comment',body=f"New User with Phone: {qcontext.get('mobile')} and OTP: {otp}")
            
            #Send OTP SMS
            if company_id and company_id.otp_message:
                if '%s' not in company_id.otp_message:
                    text = str(company_id.otp_message)+ str(otp)
                else:
                    text = str(company_id.otp_message).replace('%s',otp)
            else:
                text = """Dear Customer,
                            %s is your one time password (OTP). Please enter the OTP to proceed.
                            Thank you,
                            Alrahama"""%otp
                    
            data_url = ''
                
            try:
                if company_id and company_id.use_otp_login:
                    data_url = company_id and company_id.otp_message_url or ''
                    phone_key = company_id and str(company_id.phone_key) or ''
                    message_key = company_id and str(company_id.message_key) or ''
                    if data_url and phone_key and message_key:
                        data_url = str(data_url).replace(phone_key,mobile)
                        data_url = str(data_url).replace(message_key,str(text))

                    #TODO: Send OTP SMS
                    # _logger.info("Data URL: %s", data_url)
                    if data_url:
                        # convert data_url to dictionary
                        data_url = data_url.split("?")
                        data_url_params = data_url[1].split("&")
                        data_url_content = {i.split("=")[0]:i.split("=")[1] for i in data_url_params}
                        result = requests.post(data_url[0], timeout=20,data=data_url_content)
                        _logger.info("Result: %s %s", result.status_code, result.text)
                    # request.env["sms.sms"].sudo().create({
                    #     "partner_id":user_id.partner_id.id or False,
                    #     "number":mobile,
                    #     "body":str(text)
                    # })
                response = request.render('appness_swms_portal.verify_otp', qcontext)
                return response
            except Exception as e:
                _logger.info("Error: %s", str(e))
                # qcontext["error"] = str(e)
                response = request.render('appness_swms_portal.request_otp', qcontext)
                return response

        if qcontext.get('otp_one') and qcontext.get('otp_two') and qcontext.get('otp_three') and qcontext.get('otp_four'):
            otp_customer =  str(qcontext.get('otp_one')+qcontext.get('otp_two')+qcontext.get('otp_three')+qcontext.get('otp_four'))
            swms_otp = request.session['swms_otp']
            swms_user = request.session['swms_user'] 
            swms_phone = request.session['swms_phone']
            if otp_customer != swms_otp:
                try:
                    raise UserError(_('Verification Failed'))
                except UserError as e:
                    qcontext['error'] = str(e) or e.value
                    response = request.render('appness_swms_portal.verify_otp', qcontext)
                    return response
            else:
                user_id = request.env['res.users'].sudo().search([('id', '=', swms_user)], limit=1)
                if user_id:
                    qcontext.update({'login': user_id.sudo().login,
                                    'name': user_id.sudo().partner_id.name,
                                    'type':'otp',
                                    'password':otp_customer})  
                    request.params.update(qcontext)
                    swms_otp = request.session.pop("swms_otp")
                    swms_user = request.session.pop("swms_user")
                    swms_phone = request.session.pop("swms_phone")
                    if user_id.sudo().partner_id.name == "Father Name":
                        self.web_login(*args, **kw)
                        return request.redirect('/my/swms_account/1')
                    return self.web_login(*args, **kw)
                    # TODO: Redirect the user to update his profile if he has old data
                else:
                    auth_signup_qcontext = self.get_auth_signup_qcontext()
                    try:
                        auth_signup_qcontext.update({
                            'login': swms_phone, 
                            'phone': swms_phone, 
                            'name': "Father Name", #TODO: Change Name
                            'password': swms_otp, #TODO: change passsword with something esle << otp for now >>
                            'confirm_password': swms_otp, 
                            'country_id': '',
                            'is_family':True,
                            'family_type':'family', 
                            'company_type':'company',
                        })
                        self.do_signup(auth_signup_qcontext)

                        # Set user to public if they were not signed in by do_signup
                        # (mfa enabled)
                        if request.session.uid is None:
                            public_user = request.env.ref('base.public_user')
                            request.update_env(user=public_user)

                        # Send an account creation confirmation email
                        User = request.env['res.users']
                        user_sudo = User.sudo().search(
                            User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                        )
                        template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                        if user_sudo and template:
                            template.sudo().send_mail(user_sudo.id, force_send=True)
                        # return self.web_login(*args, **kw)
                        # return request.redirect('/my')
                        swms_otp = request.session.pop("swms_otp")
                        swms_user = request.session.pop("swms_user")
                        swms_phone = request.session.pop("swms_phone")
                        return request.redirect('/my/swms_account/1')
                    except UserError as e:
                        qcontext['error'] = e.args[0]
                    except (SignupError, AssertionError) as e:
                        if request.env["res.users"].sudo().search_count([("login", "=", qcontext.get("login"))], limit=1):
                            qcontext["error"] = _("Another user is already registered using this phone number.")
                        else:
                            _logger.warning("%s", e)
                            qcontext['error'] = _("Could not create a new account.") + Markup('<br/>') + str(e)
                        response = request.render('appness_swms_portal.verify_otp', qcontext)
                        return response

                    # return request.redirect('/my')
                    response = request.render('appness_swms_portal.verify_otp', qcontext)
                    return response

        # except UserError as e:
        #     qcontext['error'] = str(e) or e.value
            
        response = request.render('appness_swms_portal.request_otp', {})
        return response

    @http.route([
        '/my/swms_account/<int:page_id>',
        '/my/swms_account/<int:page_id>/<int:member_id>'
    ], type='http', auth="user", website=True)
    def swms_account(self,page_id=None,member_id=None,**kw):
        stepper = request.env["swms.stepper"].sudo()
        res_partner = request.env["res.partner"].sudo()
        stepper_id = stepper.search([('type','=','family')],limit=1)
        params_to_pop = ["redirect","page_id","token"]
        user = request.env.user

        partner_id = False
        update_member = False

        if user:
            if not user.partner_id.is_family:
                return request.redirect('/my')
        else:
            return request.redirect('/my')

        if member_id:
            member = res_partner.search([
                ('parent_id','=',user.partner_id.id),
                ('id','=',member_id),
            ],limit=1)

            if member:
                update_member = True
                params_to_pop.append("member_id")
                partner_id = member.id
                stepper_id = stepper.search([('type','=','member')],limit=1)
            else:
                return request.redirect('/my')
        else:
            partner_id = user.partner_id.id

        steps_count = 0

        if stepper_id:
            steps_count = len(stepper_id.steps_ids)

        if request.httprequest.method == 'POST':
            params = request.params.copy()
            # raise UserError(f"params: {params}")

            params_to_pop,m2o_params,o2m_params,binary_params = portal_form._prepare_files(params,params_to_pop,partner_id)
            fv = portal_form._prepare_swms_form_values(stepper_id, page_id, False, partner_id)
            o2m_records = portal_form._prepare_o2m_records(o2m_params)

            for step in fv['steps']:
                if step['page_id'] == page_id:
                    for field in step['fields']:

                        if field['type'] == 'checkbox':
                            if field['name'] in params.keys():
                                params[field['name']] = True
                            else:
                                params[field['name']] = False

                        if field['disabled']:
                            if field['name'] in params.keys():
                                params_to_pop.append(field['name'])
                            if field['name'] in o2m_records.keys():
                                o2m_records.pop(field['name'])

            for param_to_pop in params_to_pop:
                params.pop(param_to_pop)

            if m2o_params:
                params.update(m2o_params)

            if binary_params:
                params.update(binary_params)

            #TODO: m2o field has a problem in insert ex. customer vendor 
            #TODO: close my/account page needs action .. if family don't enter
            # raise UserError(o2m_records)

            family = res_partner.browse(partner_id)
            if family:
                family.sudo().write(params)
                portal_form._insert_o2m_records_in_main(stepper_id,partner_id,o2m_records)
                if page_id < steps_count:
                    if update_member:
                        return request.redirect(f"/my/swms_account/{page_id+1}/{partner_id}")
                    else:
                        return request.redirect(f"my/swms_account/{page_id+1}")
                elif page_id == steps_count:
                    if update_member:
                        return request.redirect('my/swms_account/2')
                    else:
                        return request.redirect('/my')
            else:
                return request.redirect('/my')

        values = request.params.copy()
        values.update(portal_form._prepare_documents_values(partner_id,False))
        values.update(portal_form._prepare_swms_form_values(stepper_id,page_id,False,partner_id))
        if values.get("page_id"):
            values.update({
                "update_member":update_member,
                "member_id":member_id,
            })
            return request.render("appness_swms_portal.portal_my_swms_account",values)
        else:
            return request.redirect('/my')


# #Note: Password should be atleast 8 characters and shall contain atleast one special character (!, @ , # , $ , % , & , * , ?), one numeric [0 - 9] and one uppercase letter [A - Z].
# # I want a strong creative and simple to memorize 12 characters password for the sms api gateway with the above mentioned conditions. Please generate a password for me. and add alrahma name to it.

# password = "a!ra7ma@appn3$$%0d00%API#968"
# p = "Ra7n3$$D00API#968"

    @http.route(
        '/swms/states/<model("res.country"):country>',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
    )
    def get_states(self, country, **kw):
        states = request.env['res.country.state'].sudo().search([('country_id', '=', country.id)])
        family = request.env.user.partner_id
        return {'states': [(s.id, s.name) for s in states],'current_state':family.state_id.id or False}

    @http.route(
        '/swms/cities/<model("res.country.state"):state>',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
    )
    def get_cities(self, state, **kw):
        cities = request.env['res.city'].sudo().search([('state_id', '=', state.id)])
        family = request.env.user.partner_id
        return {'cities': [(c.id, c.name) for c in cities],'current_city':family.city_id.id or False}

    @http.route(
        '/swms/areas/<model("res.city"):city>',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
    )
    def get_areas(self, city, **kw):
        areas = request.env['swms.area'].sudo().search([('city_id', '=', city.id)])
        family = request.env.user.partner_id
        return {'areas': [(a.id, a.name) for a in areas],'current_area':family.area_id.id or False}

    @http.route(
        '/swms/check_civil_number/<string:civil_number>',
        type='json',
        auth='user',
        methods=['POST'],
        website=True,
    )
    def check_civil_number(self, civil_number, **kw):
        partners = request.env['res.partner'].sudo().search([('civil_number', '=', civil_number)])
        for partner in partners:
            if partner.id != request.env.user.partner_id.id:
                return {'exists': True}
        return {'exists': False}
