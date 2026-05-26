from operator import itemgetter
from markupsafe import Markup

from odoo.http import request,route
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.tools.translate import _
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import AND, FALSE_DOMAIN
from odoo.addons.appness_swms_portal.models import helpers

class SWMSPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        
        vdoc = helpers.validate_documents(request, user.partner_id)
        
        required_docs_list = vdoc['types_list']
        expired_documents_list = vdoc['expired_list']

        for child in user.partner_id.child_ids:
            child_vdoc = helpers.validate_documents(request, child)
            required_docs_list += child_vdoc['types_list']
            expired_documents_list += child_vdoc['expired_list']

        service_requests = request.env["helpdesk.ticket"].sudo().search([
            ('partner_id','=',user.partner_id.id),#TODO: filter out done requests
        ])
        sr_required_docs_list = []
        sr_expired_documents_list = []

        for srequest in service_requests:
            sr_vdoc = helpers.validate_documents(request, srequest, True)
            sr_required_docs_list += sr_vdoc['types_list']
            sr_expired_documents_list += sr_vdoc['expired_list']
            
        if 'expired_documents_count' in counters:
            values['expired_documents_count'] = len(expired_documents_list)
        if 'missing_documents_count' in counters:
            values['missing_documents_count'] = len(required_docs_list)
        if 'services_expired_documents_count' in counters:
            values['services_expired_documents_count'] = len(sr_expired_documents_list)
        if 'services_missing_documents_count' in counters:
            values['services_missing_documents_count'] = len(sr_required_docs_list)
        if 'missing_information_count' in counters:
            values['missing_information_count'] = len(expired_documents_list) + len(required_docs_list)
        return values

    def _request_get_page_view_values(self, ticket, access_token, **kwargs):
        values = {
            'page_name': 'swms_request_page',
            'swms_request': ticket,
            'ticket_link_section': [],
            'ticket_closed': kwargs.get('ticket_closed', False),
            'preview_object': ticket,
        }
        # 'access_url':'/swms/request/%s' % ticket.id,
        return self._get_page_view_values(ticket, access_token, values, 'my_requests_history', False, **kwargs)

    def _request_get_searchbar_inputs(self):
        return {
            'name': {'input': 'name', 'label': _(
                'Search%(left)s Requests%(right)s',
                left=Markup('<span class="nolabel">'),
                right=Markup('</span>'),
            ), 'sequence': 10},
            # 'user_id': {'input': 'user_id', 'label': _('Search in Assigned to'), 'sequence': 20},
            # 'partner_id': {'input': 'partner_id', 'label': _('Search in Customer'), 'sequence': 30},
            'team_id': {'input': 'team_id', 'label': _('Search in SWMS Service'), 'sequence': 40},
            'stage_id': {'input': 'stage_id', 'label': _('Search in Stage'), 'sequence': 50},
        }

    def _request_get_searchbar_groupby(self):
        return {
            'none': {'label': _('None'), 'sequence': 10},
            # 'user_id': {'label': _('Assigned to'), 'sequence': 20},
            'team_id': {'label': _('SWMS Service'), 'sequence': 30},
            'stage_id': {'label': _('Stage'), 'sequence': 40},
            'kanban_state': {'label': _('Status'), 'sequence': 50},
            # 'partner_id': {'label': _('Customer'), 'sequence': 60},
        }

    def _request_get_search_domain(self, search_in, search):
        if search_in == 'name':
            return ['|', ('name', 'ilike', search), ('ticket_ref', 'ilike', search)]
        # elif search_in == 'user_id':
        #     assignees = request.env['res.users'].sudo()._search([('name', 'ilike', search)])
        #     return [('user_id', 'in', assignees)]
        elif search_in in self._ticket_get_searchbar_inputs():
            return [(search_in, 'ilike', search)]
        else:
            return ['|', ('name', 'ilike', search), ('ticket_ref', 'ilike', search)]

    def _prepare_my_requests_values(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None, groupby='none', search_in='name'):
        values = self._prepare_portal_layout_values()
        domain = self._prepare_helpdesk_tickets_domain()

        searchbar_sortings = {
            'create_date desc': {'label': _('Newest')},
            'id desc': {'label': _('Reference')},
            'name': {'label': _('Subject')},
            # 'user_id': {'label': _('Assigned to')},
            'stage_id': {'label': _('Stage')},
            'date_last_stage_update desc': {'label': _('Last Stage Update')},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            # 'assigned': {'label': _('Assigned'), 'domain': [('user_id', '!=', False)]},
            # 'unassigned': {'label': _('Unassigned'), 'domain': [('user_id', '=', False)]},
            'open': {'label': _('Open'), 'domain': [('close_date', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('close_date', '!=', False)]},
        }
        searchbar_inputs = dict(sorted(self._request_get_searchbar_inputs().items(), key=lambda item: item[1]['sequence']))
        searchbar_groupby = dict(sorted(self._request_get_searchbar_groupby().items(), key=lambda item: item[1]['sequence']))

        # default sort by value
        if not sortby:
            sortby = 'create_date desc'

        domain = AND([domain, searchbar_filters[filterby]['domain']])

        if date_begin and date_end:
            domain = AND([domain, [('create_date', '>', date_begin), ('create_date', '<=', date_end)]])

        # search
        if search and search_in:
            domain = AND([domain, self._request_get_search_domain(search_in, search)])

        # pager
        tickets_count = request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/requests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby, 'filterby': filterby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        order = f'{groupby}, {sortby}' if groupby != 'none' else sortby
        tickets = request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_requests_history'] = tickets.ids[:100]

        if not tickets:
            grouped_tickets = []
        elif groupby != 'none':
            grouped_tickets = [request.env['helpdesk.ticket'].concat(*g) for k, g in groupbyelem(tickets, itemgetter(groupby))]
        else:
            grouped_tickets = [tickets]

        values.update({
            'date': date_begin,
            'grouped_tickets': grouped_tickets,
            'page_name': 'request',
            'default_url': '/my/requests',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
        })
        return values

    @route()
    def account(self, redirect=None, **post):
        user = request.env.user

        if user.partner_id.is_family:
            raise AccessError("Sorry you don't have access to this page")

        return super().account(redirect=redirect, **post)
