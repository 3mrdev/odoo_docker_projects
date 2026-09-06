# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError
from . import helpers

class JizWaqf(models.Model):
    _name = 'jiz.waqf'
    _description = 'Waqf Information'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'documents.mixin']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    name = fields.Char(string='Name', required=True,translate=True)
    waqf_endower_contact_id = fields.Many2one('res.partner', string='Waqf Endower Contact', required=True)
    waqf_sequence_number = fields.Char(string='Waqf Sequence Number', readonly=True)
    waqf_date = fields.Date(string='Waqf Date', tracking=True)
    waqf_valuation = fields.Float(string='Waqf Valuation')
    land_number = fields.Char(string='Land Number')
    donor_terms_and_conditions = fields.Html(string='Donor Terms and Conditions')
    notes = fields.Html(string='Notes')
    address_location_details_link = fields.Char(string='Address/Location Details Link', widget='url')
    address_location_details_id = fields.Many2one('res.partner', string='Address/Location Details')
    waqf_type_id = fields.Many2one('jiz.waqf.type', string='Waqf Type')
    use_type_id = fields.Many2one('jiz.use.type', string='Use Type')
    use_type_is_rent = fields.Boolean(related='use_type_id.is_rent', store=True)
    responsible_id = fields.Many2one('res.partner', string='Responsible')
    responsible_invoice_address_updated = fields.Date(string='Invoice Address Updated', compute='_compute_responsible_invoice_address',store=True)
    # invoice_address_id = fields.Many2one('res.partner', string='Invoice Address')
    unit_ids = fields.One2many('jiz.waqf.unit', 'waqf_id', string='Units')
    tag_ids = fields.Many2many('crm.tag', string='Tags')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('sold', 'Sold'),
    ], string='Status', default='draft')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account (Auto-generated)')
    analytic_distribution = fields.Json(string='Analytic Distribution')
    analytic_precision = fields.Integer(default=2)
    asset_id = fields.Many2one('account.asset', string='Asset', readonly=True, copy=False)
    asset_bill_id = fields.Many2one('account.move', string='Asset Bill', readonly=True, copy=False)
    asset_model_id = fields.Many2one('account.asset', string='Asset Type', domain="[('state', '=', 'model')]",related='waqf_type_id.asset_model_id',store=True)
    asset_count = fields.Integer(string='Asset Count', compute='_compute_asset_count')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    opportunity_count = fields.Integer(string='Opportunity Count', compute='_compute_opportunity_count')
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state')
    country_id = fields.Many2one('res.country')
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')
    city_id = fields.Many2one('res.city', string='City')
    area_id = fields.Many2one('res.area', string='Area')
    sell_invoices = fields.One2many('account.move', 'sell_waqf_id', string='Sell Invoices')
    sell_invoices_count = fields.Integer(string='Sell Invoices Count', compute='_compute_sell_invoices_count')
    sell_amount = fields.Float(string='Sell Amount', compute='_compute_sell_amount')
    approximate_sale_amount = fields.Float(string='Approximate Sale Amount')

    waqf_invoices = fields.One2many('account.move', 'waqf_id', string='Waqf Invoices')
    waqf_invoices_count = fields.Integer(string='Waqf Invoices Count', compute='_compute_waqf_invoices_count')
    waqf_subscriptions = fields.One2many('sale.order', 'waqf_id', string='Waqf Subscriptions')
    waqf_subscriptions_count = fields.Integer(string='Waqf Subscriptions Count', compute='_compute_waqf_subscriptions_count')

    project_ids = fields.One2many('project.project','waqf_id', string='Projects')
    project_count = fields.Integer(string='Project Count', compute='_compute_project_count', store=True)
    purchase_ids = fields.One2many('purchase.order','waqf_id', string='Purchases')
    purchase_count = fields.Integer(string='Purchase Count', compute='_compute_purchase_count', store=True)
    expense_ids = fields.One2many('hr.expense','waqf_id', string='Expenses')
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count', store=True)

    @api.depends("responsible_id")
    def _compute_responsible_invoice_address(self):
        for waqf in self:
            for unit in waqf.unit_ids:
                for subscription in unit.subscription_ids:
                    if subscription.state == 'sale':
                        subscription.partner_invoice_id = waqf.responsible_id or subscription.partner_id
                        subscription.partner_shipping_id = waqf.responsible_id or subscription.partner_id
            waqf.responsible_invoice_address_updated = fields.Date.today()
    
    @api.depends('waqf_invoices')
    def _compute_waqf_invoices_count(self):
        for waqf in self:
            waqf.waqf_invoices_count = len(waqf.waqf_invoices)

    @api.depends('waqf_subscriptions')
    def _compute_waqf_subscriptions_count(self):
        for waqf in self:
            waqf.waqf_subscriptions_count = len(waqf.waqf_subscriptions)

    @api.depends('sell_invoices')
    def _compute_sell_invoices_count(self):
        for waqf in self:
            waqf.sell_invoices_count = len(waqf.sell_invoices)

    @api.depends('project_ids')
    def _compute_project_count(self):
        for waqf in self:
            waqf.project_count = len(waqf.project_ids)

    @api.depends('purchase_ids')
    def _compute_purchase_count(self):
        for waqf in self:
            waqf.purchase_count = len(waqf.purchase_ids)

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for waqf in self:
            waqf.expense_count = len(waqf.expense_ids)

    @api.depends('sell_invoices')
    def _compute_sell_amount(self):
        for waqf in self:
            amount = 0
            for invoice in waqf.sell_invoices:
                if invoice.state == 'posted':
                    amount += invoice.amount_total
            waqf.sell_amount = amount

    @api.depends('opportunity_id')
    def _compute_opportunity_count(self):
        for waqf in self:
            waqf.opportunity_count = 1 if waqf.opportunity_id else 0

    def action_view_waqf_subscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Waqf Subscriptions',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }

    def action_view_sell_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sell Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('sell_waqf_id', '=', self.id)],
            'context': {'default_sell_waqf_id': self.id},
        }

    def action_view_waqf_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Waqf Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }

    def action_view_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Projects',
            'res_model': 'project.project',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }

    def action_view_purchase(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchases',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }

    def action_view_expense(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expenses',
            'res_model': 'hr.expense',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }

    def action_view_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Units',
            'res_model': 'jiz.waqf.unit',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }

    @api.depends('asset_id')
    def _compute_asset_count(self):
        for waqf in self:
            waqf.asset_count = 1 if waqf.asset_id else 0

    document_count = fields.Integer(compute='compute_document_count', string='Documents',store=True)
    documents = fields.One2many('documents.document', 'waqf_id', string='Documents')
    noti_documents = fields.Text()
    units_total_rent = fields.Float(string='Total Rent', compute='_compute_unit_counts')
    unit_count = fields.Integer(string='Unit Count', compute='_compute_unit_counts')
    free_unit_count = fields.Integer(string='Free Units', compute='_compute_unit_counts')
    rented_unit_count = fields.Integer(string='Rented Units', compute='_compute_unit_counts')
    maintenance_unit_count = fields.Integer(string='Maintenance Units', compute='_compute_unit_counts')

    @api.constrains('document_count','status')
    def check_documents(self):
        for rec in self:
            # rec._compute_document_count()
            vdoc = helpers.validate_documents(self)
            if vdoc['types']:
                rec.noti_documents = _("Missing Documents:")+f""" \n{vdoc['types']}"""
            else:
                rec.noti_documents = False

    @api.depends('unit_ids.status')
    def _compute_unit_counts(self):
        for waqf in self:
            waqf.unit_count = len(waqf.unit_ids)
            waqf.units_total_rent = sum(waqf.unit_ids.mapped('price'))
            waqf.free_unit_count = len(waqf.unit_ids.filtered(lambda u: u.status == 'free'))
            waqf.rented_unit_count = len(waqf.unit_ids.filtered(lambda u: u.status == 'under_rent'))
            waqf.maintenance_unit_count = len(waqf.unit_ids.filtered(lambda u: u.status == 'under_maintenance'))
    
    @api.depends('documents','opportunity_id.documents')
    def compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.documents) + len(rec.opportunity_id.documents)

    def _get_document_folder(self):
        return self.company_id.documents_waqf_folder

    def _get_document_tags(self):
        return self.company_id.documents_waqf_tags

    def _check_create_documents(self):
        return self.company_id.documents_waqf_settings and super()._check_create_documents()

    def action_open_attachments(self):
        self.ensure_one()
        if not self.company_id.documents_waqf_settings:
            return True
        waqf_folder = self._get_document_folder()
        waqf_tags = self._get_document_tags()
        action = self.env['ir.actions.act_window']._for_xml_id('documents.document_action')
        action['domain'] = [
            '|',
                ('type', '=', 'folder'),
                '|',
                    '&',
                        ('res_model', '=', self._name),
                        ('res_id', '=', self.id),
                    '&',
                        ('res_model', '=', self.opportunity_id._name),
                        ('res_id', '=', self.opportunity_id.id),
        ]
        action['context'] = {
            'default_res_id': self.id,
            'default_res_model': self._name,
            'searchpanel_default_folder_id': waqf_folder.id,
            'searchpanel_default_tag_ids': waqf_tags.ids,
        }
        return action

    def action_create_asset(self):
        for waqf in self:
            if not waqf.asset_model_id:
                raise UserError(_("You cannot create an asset without an asset model. Please add one in the waqf"))
            
            if not waqf.asset_id:
                asset = self.env['account.asset'].create({
                    'name': waqf.name,
                    'original_value': waqf.waqf_valuation,
                    'company_id': waqf.company_id.id,
                    'currency_id': waqf.company_id.currency_id.id,
                    'model_id': waqf.asset_model_id.id,
                    'account_asset_id': waqf.asset_model_id.account_asset_id.id,
                    'display_account_asset_id':waqf.asset_model_id.account_asset_id.id,
                    'account_depreciation_id': waqf.asset_model_id.account_depreciation_id.id,
                    'account_depreciation_expense_id': waqf.asset_model_id.account_depreciation_expense_id.id,
                    'equity_account_id':waqf.asset_model_id.equity_account_id.id,
                    'equity_journal_id':waqf.asset_model_id.equity_journal_id.id,
                    'analytic_distribution':waqf.analytic_distribution,
                    'journal_id':waqf.asset_model_id.journal_id.id,
                    'state':'draft'
                })
                waqf.asset_id = asset.id

                if not waqf.asset_bill_id:
                    balance = waqf.waqf_valuation
                    partner = waqf.waqf_endower_contact_id

                    analytic_distribution = waqf.analytic_distribution or {}
                    
                    if not waqf.asset_model_id.equity_journal_id or not waqf.asset_model_id.account_asset_id or not waqf.asset_model_id.equity_account_id:
                        raise UserError(_("You cannot create an asset bill without an equity account, journal or asset account.\n Please add them in the asset model"))
                    
                    data = {
                        'waqf_id': waqf.id,
                        'move_type': 'entry',
                        'date': fields.Date.today(),
                        'journal_id': waqf.asset_model_id.equity_journal_id.id,
                        'line_ids': [
                            Command.create({
                                'debit': balance if balance > 0.0 else 0.0,
                                'credit': -balance if balance < 0.0 else 0.0,
                                'account_id': waqf.asset_model_id.account_asset_id.id,
                                'partner_id': partner.id if partner else None,
                                'analytic_distribution': analytic_distribution,
                            }),
                            Command.create({
                                'debit': -balance if balance < 0.0 else 0.0,
                                'credit': balance if balance > 0.0 else 0.0,
                                'account_id': waqf.asset_model_id.equity_account_id.id,
                                'partner_id': partner.id if partner else None,
                            }),
                        ],
                    }
                    invoice_id = self.env['account.move'].sudo().create(data)
                    waqf.asset_bill_id = invoice_id.id

    def action_submit(self):
        for waqf in self:
            vdoc = helpers.validate_documents(self)
            if vdoc['types']:
                raise UserError(_("Missing Documents:")+f""" \n{vdoc['types']}""")
            
            if waqf.waqf_valuation <= 0:
                raise UserError(_("You cannot submit a Waqf with a valuation of zero or less."))
        self.write({'status': 'in_progress'})
        for unit in self.unit_ids:
            rented = False
            for subscription in unit.subscription_ids:
                if subscription.state == 'sale':
                    rented = True
                    break
            if rented:
                unit.action_set_under_rent()
            else:
                unit.action_set_free()

    def action_hold(self):
        self.write({'status': 'on_hold'})
        for unit in self.unit_ids:
            unit.action_hold()
            
    def action_sell(self):
        self.write({'status': 'sold'})
        for unit in self.unit_ids:
            unit.action_sell()

    def action_reset_to_draft(self):
        self.write({'status': 'draft'})

    def action_migrate_analytic_distribution(self):
        """Migrate existing analytic_account_id to analytic_distribution for backward compatibility."""
        waqfs = self.search([
            ('analytic_account_id', '!=', False),
            ('analytic_distribution', '=', False),
        ])
        for waqf in waqfs:
            distribution = {}
            if waqf.analytic_account_id:
                distribution[str(waqf.analytic_account_id.id)] = 100
            partner_analytic = waqf.waqf_endower_contact_id.analytic_account_id
            if partner_analytic:
                distribution[str(partner_analytic.id)] = 100
            waqf.analytic_distribution = distribution or None

        units = self.env['jiz.waqf.unit'].search([
            ('waqf_id', '!=', False),
            ('analytic_distribution', '=', False),
        ])
        for unit in units:
            if unit.waqf_id.analytic_distribution:
                unit.analytic_distribution = unit.waqf_id.analytic_distribution
            elif unit.analytic_account_id:
                unit.analytic_distribution = {str(unit.analytic_account_id.id): 100}

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Migration Complete',
                'message': f'Migrated {len(waqfs)} waqfs and {len(units)} units to analytic distribution.',
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_asset(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asset',
            'res_model': 'account.asset',
            'view_mode': 'form',
            'res_id': self.asset_id.id,
        }

    def action_view_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Opportunity',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.opportunity_id.id,
        }

    def action_view_units(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} - Units',
            'res_model': 'jiz.waqf.unit',
            'view_mode': 'list,form',
            'domain': [('waqf_id', '=', self.id)],
            'context': {'default_waqf_id': self.id},
        }
    
    @api.model_create_multi
    def create(self, vals):
        rec = super(JizWaqf, self).create(vals)

        if not rec.waqf_sequence_number:
            rec.waqf_sequence_number = self.env['ir.sequence'].next_by_code('jiz.waqf')

        if not rec.analytic_account_id:
            analytic_plan = self.env['account.analytic.plan'].search([('name', '=', 'WAQFS')])
            if not analytic_plan:
                analytic_plan = self.env['account.analytic.plan'].create({
                    'name': 'WAQFS',
                })
            analytic_account_id = self.env['account.analytic.account'].create({
                'name': rec.name,
                'code': rec.waqf_sequence_number,
                'company_id': rec.company_id.id,
                'plan_id': analytic_plan.id,
            })
            rec.analytic_account_id = analytic_account_id.id

        rec._build_analytic_distribution()

        return rec

    def _build_analytic_distribution(self):
        for waqf in self:
            distribution = {}
            if waqf.analytic_account_id:
                distribution[str(waqf.analytic_account_id.id)] = 100
            partner_analytic = waqf.waqf_endower_contact_id.analytic_account_id
            if partner_analytic:
                distribution[str(partner_analytic.id)] = 100
            waqf.analytic_distribution = distribution or None

    def unlink(self):
        for waqf in self:
            if waqf.status != 'draft':
                raise UserError(_("You can only delete a Waqf that is in draft state."))
            elif waqf.status == 'draft':
                if waqf.unit_ids:
                    raise UserError(_("You cannot delete a Waqf that has units."))
                elif waqf.asset_id:
                    raise UserError(_("You cannot delete a Waqf that has an asset."))
                elif waqf.waqf_invoices:
                    raise UserError(_("You cannot delete a Waqf that has invoices."))
                elif waqf.waqf_subscriptions:
                    raise UserError(_("You cannot delete a Waqf that has subscriptions."))
                elif waqf.document_count:
                    raise UserError(_("You cannot delete a Waqf that has documents."))
        return super(JizWaqf, self).unlink()