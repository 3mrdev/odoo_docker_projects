from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _

from . import portal_general,portal_form

class SWMSPortal(portal_general.SWMSPortal):

    @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', auth="user", website=True)
    def my_swms_requests(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None, groupby='none', search_in='name', **kw):
        values = self._prepare_my_requests_values(page, date_begin, date_end, sortby, filterby, search, groupby, search_in)
        return request.render("appness_swms_portal.portal_swms_requests", values)

    @http.route([
        '/swms/service_request/<int:service_id>/<int:page_id>',
        '/swms/service_request/<int:service_id>/<int:page_id>/<int:request_id>'
    ], type='http', auth="user", website=True)
    def swms_service_request(self,service_id,page_id,request_id=None,**kw):
        helpdesk_ticket = request.env['helpdesk.ticket'].sudo()
        helpdesk_team = request.env['helpdesk.team'].sudo()
        stepper = request.env["swms.stepper"].sudo()
        stepper_id = stepper.search([('type','=','service'),('service_id','=',service_id)],limit=1)
        team_id = helpdesk_team.search([('service','=',service_id)],limit=1)
        user = request.env.user
        params_to_pop = ["redirect","service_id","page_id"]

        steps_count = 0
        swms_request = False
        update_request = False

        #If no form for the service redirect out
        if stepper_id:
            steps_count = len(stepper_id.steps_ids)
        else:
            return request.redirect('/my/requests')

        #If no team for the service redirect out
        if not team_id:
            return request.redirect('/my/requests')

        if user:
            if not user.partner_id.is_family:
                return request.redirect('/my')
        else:
            return request.redirect('/my')

        if request_id:
            swms_request = request.env["helpdesk.ticket"].sudo().search([
                ('partner_id','=',user.partner_id.id),
                ('team_id','=',team_id.id),
                ('id','=',request_id),
            ],limit=1)

            if swms_request:
                update_request = True
                params_to_pop.append("request_id")
            else:
                return request.redirect('/my/requests')
        else:
            stage_ids = [
                team_id.is_done_stage.id,
                team_id.is_reject_stage.id,
                team_id.is_cancel_stage.id
            ]
            if not team_id.service.can_be_repeated:
                swms_request = request.env["helpdesk.ticket"].sudo().search([
                    ('partner_id','=',user.partner_id.id),
                    ('team_id', '=', team_id.id),
                    ('stage_id', 'not in', stage_ids),
                ],limit=1)

                if swms_request:
                    return request.redirect(f'/swms/request/{swms_request.id}')

        if request.httprequest.method == 'POST':
            params = request.params.copy()

            params_to_pop,m2o_params,o2m_params,binary_params = portal_form._prepare_files(params,params_to_pop,user.partner_id.id)

            for param_to_pop in params_to_pop:
                params.pop(param_to_pop)

            o2m_records = portal_form._prepare_o2m_records(o2m_params)

            if m2o_params:
                params.update(m2o_params)

            if binary_params:
                params.update(binary_params)
                
            #TODO: m2o field has a problem in insert ex. customer vendor 
            # raise UserError(params)

            if swms_request:
                swms_request.write(params)
                portal_form._insert_o2m_records_in_main(stepper_id,swms_request.id,o2m_records)
                if page_id < steps_count:
                    if update_request:
                        return request.redirect(f"/swms/service_request/{service_id}/{page_id+1}/{request_id}")
                    else:
                        return request.redirect(f"/swms/service_request/{service_id}/{page_id+1}")
                elif page_id == steps_count:
                    return request.redirect('/my/requests')
            else:
                params["team_id"] = team_id.id
                params["partner_id"] = user.partner_id.id
                # params["name"] = "Ticket from portal 2"
                ticket_id = helpdesk_ticket.create(params)
                if ticket_id:
                    portal_form._insert_o2m_records_in_main(stepper_id,ticket_id.id,o2m_records)
                    return request.redirect(f"/swms/service_request/{service_id}/{page_id+1}/{ticket_id.id}")

        values = request.params.copy()
        values.update(portal_form._prepare_request_service_values(service_id))
        values.update(portal_form._prepare_documents_values(user.partner_id.id,swms_request))
        values.update(portal_form._prepare_swms_form_values(stepper_id,page_id,swms_request,False))
        if values.get("service_id") and values.get("page_id"):
            values.update({
                "page_name":"swms_service_request",
                "update_request":update_request,
                "request_id":request_id,
                "request_seq":swms_request.request_seq if update_request else False
            })
            return request.render("appness_swms_portal.portal_swms_service_request",values)
        else:
            # return request.render('website.page_404' or 'http_routing.404')
            return request.redirect('/my')

    @http.route([
        "/swms/request/<int:ticket_id>",
        "/swms/request/<int:ticket_id>/<access_token>",
        '/my/request/<int:ticket_id>',
        '/my/request/<int:ticket_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def requests_followup(self, ticket_id=None, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access('helpdesk.ticket', ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._request_get_page_view_values(ticket_sudo, access_token, **kw)

        prev_url = False
        next_url = False

        if values.get('prev_record',False):
            prev_url = f"/swms/request/{values.get('prev_record').split('/')[3]}"
        if values.get('next_record',False):
            next_url = f"/swms/request/{values.get('next_record').split('/')[3]}"
        
        values.update({
            'prev_record': prev_url,
            'next_record': next_url,
            'service_id': ticket_sudo.team_id.service.id,
            'request_id': ticket_id,
        })
        return request.render("appness_swms_portal.requests_followup", values)