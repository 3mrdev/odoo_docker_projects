from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _

from . import portal_general,portal_form

class LogspacePortal(portal_general.LogspacePortal):

    # @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', auth="user", website=True)
    # def my_logspace_requests(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None, groupby='none', search_in='name', **kw):
    #     values = self._prepare_my_requests_values(page, date_begin, date_end, sortby, filterby, search, groupby, search_in)
    #     return request.render("appness_logspace_portal.portal_logspace_requests", values)

    @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_requests(self, **kwargs):
        values = self._prepare_sale_portal_rendering_values(quotation_page=False, **kwargs)
        request.session['my_orders_history'] = values['orders'].ids[:100]
        return request.render("appness_logspace_portal.portal_logspace_requests", values)

    @http.route([
        '/logspace/service_request/<int:service_id>/<int:page_id>',
        '/logspace/service_request/<int:service_id>/<int:page_id>/<int:request_id>'
    ], type='http', auth="user", website=True)
    def logspace_service_request(self,service_id,page_id,request_id=None,**kw):
        sale_order = request.env['sale.order'].sudo()
        stepper = request.env["logspace.stepper"].sudo()
        stepper_id = stepper.search([('type','=','service'),('service_id','=',service_id)],limit=1)
        user = request.env.user
        params_to_pop = ["redirect","service_id","page_id"]

        steps_count = 0
        logspace_request = False
        update_request = False

        #If no form for the service redirect out
        if stepper_id:
            steps_count = len(stepper_id.steps_ids)
        else:
            return request.redirect('/my/requests')

        if user:
            if not user.partner_id.is_logspace_customer:
                return request.redirect('/my')
        else:
            return request.redirect('/my')

        if request_id:
            logspace_request = request.env["sale.order"].sudo().search([
                ('partner_id','=',user.partner_id.id),
                ('id','=',request_id),
            ],limit=1)

            if logspace_request:
                update_request = True
                params_to_pop.append("request_id")
            else:
                return request.redirect('/my/requests')
        else:
            # logspace_request = request.env["sale.order"].sudo().search([
            #     ('partner_id','=',user.partner_id.id),
            # ],limit=1)

            # if logspace_request:
            #     return request.redirect(f'/logspace/request/{logspace_request.id}')
            pass

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

            if logspace_request:
                logspace_request.write(params)
                portal_form._insert_o2m_records_in_main(stepper_id,logspace_request.id,o2m_records)
                if page_id < steps_count:
                    if update_request:
                        return request.redirect(f"/logspace/service_request/{service_id}/{page_id+1}/{request_id}")
                    else:
                        return request.redirect(f"/logspace/service_request/{service_id}/{page_id+1}")
                elif page_id == steps_count:
                    return request.redirect('/my/requests')
            else:
                params["partner_id"] = user.partner_id.id
                # params["name"] = "Ticket from portal 2"
                sale_order_id = sale_order.create(params)
                if sale_order_id:
                    portal_form._insert_o2m_records_in_main(stepper_id,sale_order_id.id,o2m_records)
                    return request.redirect(f"/logspace/service_request/{service_id}/{page_id+1}/{sale_order_id.id}")

        values = request.params.copy()
        values.update(portal_form._prepare_request_service_values(service_id))
        values.update(portal_form._prepare_documents_values(user.partner_id.id,logspace_request))
        values.update(portal_form._prepare_logspace_form_values(stepper_id,page_id,logspace_request,False))
        if values.get("service_id") and values.get("page_id"):
            values.update({
                "page_name":"logspace_service_request",
                "update_request":update_request,
                "request_id":request_id,
                "request_seq":logspace_request.request_seq if update_request else False
            })
            return request.render("appness_logspace_portal.portal_logspace_service_request",values)
        else:
            # return request.render('website.page_404' or 'http_routing.404')
            return request.redirect('/my')

    @http.route([
        "/logspace/request/<int:ticket_id>",
        "/logspace/request/<int:ticket_id>/<access_token>",
        '/my/request/<int:ticket_id>',
        '/my/request/<int:ticket_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def requests_followup(self, ticket_id=None, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access('sale.order', ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._request_get_page_view_values(ticket_sudo, access_token, **kw)

        prev_url = False
        next_url = False

        if values.get('prev_record',False):
            prev_url = f"/logspace/request/{values.get('prev_record').split('/')[3]}"
        if values.get('next_record',False):
            next_url = f"/logspace/request/{values.get('next_record').split('/')[3]}"
        
        values.update({
            'prev_record': prev_url,
            'next_record': next_url,
            'service_id': ticket_sudo.team_id.service.id,
            'request_id': ticket_id,
        })
        return request.render("appness_logspace_portal.requests_followup", values)