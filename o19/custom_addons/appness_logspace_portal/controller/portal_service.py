from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from . import portal_general

class LogspacePortal(portal_general.LogspacePortal):

    @http.route(['/logspace/services'], type='http', auth="user", website=True)
    def logspace_services(self, **kw):
        user = request.env.user
        allowed_services = []

        if user:
            if not user.partner_id.is_logspace_customer:
                return request.redirect('/my')
        else:
            return request.redirect('/my')

        services = request.env["product.template"].sudo().search([
            ('is_logspace','=',True),
            ('is_published_logspace','=',True),
            ('type','=','service'),
        ])

        for service in services:
            # # Skip services with no addresses
            # if not service.allowed_address:
            #     continue
                
            service_allowed = True

            # for address in service.allowed_address:
            #     # Check if user's country matches the address country
            #     if user.partner_id.country_id.id != address.country_id.id:
            #         continue
                
            #     # Case 1: Service has country, state, and city
            #     if address.city_ids:
            #         if user.partner_id.city_id.id in address.city_ids.ids:
            #             service_allowed = True
            #             break
                
            #     # Case 2: Service has country and state but no city
            #     elif address.state_ids:
            #         if user.partner_id.state_id.id in address.state_ids.ids:
            #             service_allowed = True
            #             break
                
            #     # Case 3: Service has only country (no state and no city)
            #     elif not address.state_ids and not address.city_ids:
            #         service_allowed = True
            #         break

            if service_allowed:
                allowed_services.append(service)

        return request.render("appness_logspace_portal.portal_logspace_services",{
            "page_name":"logspace_services",
            "services":allowed_services
        })

    @http.route(['/logspace/service/<int:service_id>'], type='http', auth="user", website=True)
    def logspace_service(self, service_id=None, **kw):
        user = request.env.user

        if user:
            if not user.partner_id.is_logspace_customer:
                return request.redirect('/my')
        else:
            return request.redirect('/my')

        service = request.env["product.template"].sudo().search([
            ('is_logspace','=',True),
            ('is_published_logspace','=',True),
            ('type','=','service'),
            ('id','=',service_id),
        ], limit=1)
        
        if service:
            found_city = True
            found_state = True
            found_country = True

            # for address in service.allowed_address: 
            #     if user.partner_id.country_id.id == address.country_id.id:
            #         found_country = True
            #     if user.partner_id.state_id.id in address.state_ids.ids:
            #         found_state = True
            #     if user.partner_id.city_id.id in address.city_ids.ids:
            #         found_city = True

            if found_city or found_state or found_country: #TODO
                required_documents = []
                for doc_type in service.document_types:
                    required_documents.append({
                        "name":doc_type.name,
                        "description":doc_type.description
                    })
                return request.render("appness_logspace_portal.portal_logspace_service",{
                    "service_id":service_id,
                    "service_name":service.name,
                    "service_desc":service.description_sale,
                    "required_documents":required_documents,
                    "page_name":"logspace_service"
                })
            else:
                return request.redirect('/my')
        else:
            # return request.render('website.page_404' or 'http_routing.404')
            return request.redirect('/my')