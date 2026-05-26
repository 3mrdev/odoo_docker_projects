from odoo import models,fields,api,Command,_
import datetime
from odoo.exceptions import UserError

class Branch(models.Model):
    _name = "maintenance.branch"

    name = fields.Many2one("res.users")
    requests_count = fields.Integer(compute="count_all",store=True)
    plans_count = fields.Integer(compute="count_all",store=True)
    equipments_count = fields.Integer(compute="count_all",store=True)

    @api.depends("name")
    def count_all(self):
        for rec in self:
            rec.requests_count = self.env["maintenance.request"].search_count([('user_id','=',rec.name.id)])
            rec.plans_count = self.env["maintenance.plan"].search_count([('equipment_id.technician_user_id','=',rec.name.id)])
            rec.equipments_count = self.env["maintenance.equipment"].search_count([('technician_user_id','=',rec.name.id)])

    def action_open_requests(self):
        return {
            'name': _('Maintenance Requests'),
            'type': 'ir.actions.act_window',
            'domain': [('user_id', '=', self.name.id)],
            # 'context': {'default_user_id': self.id},
            'view_type': 'kanban',
            'view_mode': 'kanban',
            'res_model': 'maintenance.request',
            'view_id': False,
            'views': [
                (self.env.ref('maintenance.hr_equipment_request_view_kanban').id, 'kanban'),
                (self.env.ref('maintenance.hr_equipment_request_view_tree').id, 'tree'),
                (self.env.ref('maintenance.hr_equipment_request_view_form').id, 'form')
            ],
            'target': 'current',
        }

    def action_open_plans(self):
        return {
            'name': _('Maintenance Plans'),
            'type': 'ir.actions.act_window',
            'domain': [('equipment_id.technician_user_id', '=', self.name.id)],
            # 'context': {'default_user_id': self.id},
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'maintenance.plan',
            'view_id': False,
            'views': [
                (self.env.ref('maintenance_plan.maintenance_plan_view_tree').id, 'tree'),
                (self.env.ref('maintenance_plan.maintenance_plan_view_form').id, 'form')
            ],
            'target': 'current',
        }

    def action_open_equipments(self):
        return {
            'name': _('Equipments'),
            'type': 'ir.actions.act_window',
            'domain': [('technician_user_id', '=', self.name.id)],
            # 'context': {'default_user_id': self.id},
            'view_type': 'kanban',
            'view_mode': 'kanban',
            'res_model': 'maintenance.equipment',
            'view_id': False,
            'views': [
                (self.env.ref('maintenance.hr_equipment_view_kanban').id, 'kanban'),
                (self.env.ref('maintenance.hr_equipment_view_tree').id, 'tree'),
                (self.env.ref('maintenance.hr_equipment_view_form').id, 'form')
            ],
            'target': 'current',
        }

class Plan(models.Model):
    _inherit = "maintenance.plan"

    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team',required=True)
    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",
        related="maintenance_team_id.member_ids",domain="[('company_ids', 'in', company_id)]")
    
    @api.constrains('maintenance_plan_horizon','planning_step')
    def _check_interval(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        planning_horizon = ICPSudo.get_param('fb_wajiz_maintenance.planning_horizon')
        for record in self:
            if planning_horizon:
                years = int(planning_horizon)
                months = years * 12
                weeks = years * 52
                days = years * 365
                if record.planning_step == 'year':
                    if record.maintenance_plan_horizon > years:
                        raise UserError(_(f"Planning Horizon must be less than {years} years"))
                elif record.planning_step == 'month':
                    if record.maintenance_plan_horizon > months:
                        raise UserError(_(f"Planning Horizon must be less than {months} months"))
                elif record.planning_step == 'week':
                    if record.maintenance_plan_horizon > weeks:
                        raise UserError(_(f"Planning Horizon must be less than {weeks} weeks"))
                elif record.planning_step == 'day':
                    if record.maintenance_plan_horizon > days:
                        raise UserError(_(f"Planning Horizon must be less than {days} days"))
            else:
                raise UserError(_("Planning Horizon is not set go to settings to set it"))

class Equipment(models.Model):
    _inherit = "maintenance.equipment"

    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team', check_company=True,required=True)
    todo = fields.Many2one("maintenance.todo")
    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",
        related="maintenance_team_id.member_ids",domain="[('company_ids', 'in', company_id)]")
    product_id = fields.Many2one(
        'product.product',  # Reference to the product model
        string='Product',
        help='Product associated with this equipment'
    )
    sparepart_ids = fields.Many2many(
        'stock.move',  # The model that sparepartslines2 refers to
        string='Spare Parts',
        compute='_compute_sparepart_ids',
        store=True
    )
    equipment_number = fields.Char(
        string="Equipment Number"
    )

    @api.depends('maintenance_ids.sparepartslines2')
    def _compute_sparepart_ids(self):
        for record in self:
            sparepart_moves = record.mapped('maintenance_ids.sparepartslines2')
            record.sparepart_ids = [(6, 0, sparepart_moves.ids)]   
 
    def _prepare_request_from_plan(self, maintenance_plan, next_maintenance_date):
        team_id = maintenance_plan.maintenance_team_id.id or self.maintenance_team_id.id
        request_model = self.env["maintenance.request"]
        if not team_id:
            team_id = request_model._get_default_team_id()

        description = self.name if self else maintenance_plan.name
        kind = maintenance_plan.maintenance_kind_id.name or _("Unspecified kind")
        name = _(
            "Preventive Maintenance (%(kind)s) - %(description)s",
            kind=kind,
            description=description,
        )

        data = {
            "name": name,
            "request_date": next_maintenance_date,
            "schedule_date": next_maintenance_date,
            "category_id": self.category_id.id,
            "equipment_id": self.id,
            "maintenance_type": "preventive",
            "address_id":self.address_id.id or False,
            "employee_id":self.employee_id.id or False,
            "owner_user_id": self.owner_user_id.id or self.env.user.id,
            "user_id": self.technician_user_id.id,
            "maintenance_team_id": team_id,
            "maintenance_kind_id": maintenance_plan.maintenance_kind_id.id,
            "maintenance_plan_id": maintenance_plan.id,
            "duration": maintenance_plan.duration,
            "note": maintenance_plan.note,
            "company_id": maintenance_plan.company_id.id or self.company_id.id,
        }
        # This field comes from maintenance_timesheet for avoiding a glue module
        if "planned_hours" in request_model._fields:
            data["planned_hours"] = maintenance_plan.duration
        return data
    
class EquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"

    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team',required=True)
    todo = fields.Many2one("maintenance.todo")
    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",
        related="maintenance_team_id.member_ids",domain="[('company_ids', 'in', company_id)]")
        
class MaintenanceKind(models.Model):
    _inherit = "maintenance.kind"

    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team',required=True)
    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",
        related="maintenance_team_id.member_ids",domain="[('company_ids', 'in', company_id)]")

class Team(models.Model):
    _inherit = "maintenance.team"

    picking_type_id = fields.Many2one("stock.picking.type",string="Operation",required=True)
    location = fields.Many2one("stock.location",string="Storage Location",required=True)
    source_location = fields.Many2one("stock.location",string="Source Location",required=True)
    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",readonly=True,
        domain="[('company_ids', 'in', company_id)]",default=lambda self: [Command.link(self.env.user.id)])


class Request(models.Model):
    _inherit = "maintenance.request"

    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",
        related="maintenance_team_id.member_ids",domain="[('company_ids', 'in', company_id)]")
    seq = fields.Char(default="New")
    closed = fields.Boolean()
    active = fields.Boolean(default=True)
    close_date = fields.Date() #compute="cal_close",store=True
    address_id = fields.Many2one("res.partner")
    purchase_orders = fields.One2many("purchase.order","maintenance_request_id")
    stock_pickings2 = fields.One2many("stock.picking","maintenance_request_id")
    stock_pickings = fields.One2many("maintenance.spareparts","maintenance_request_id")
    stock_pickings_count = fields.Integer(compute="pickings_count",store=True)
    sparepartslines = fields.Many2many("maintenance.spareparts.line",compute="pickings_count",store=True)
    sparepartslines2 = fields.Many2many("stock.move",compute="pickings_count2",store=True)
    todo = fields.Many2one("maintenance.todo",compute="cal_todo",store=True)
    todo_do = fields.Many2one("maintenance.todo")
    todolines = fields.One2many("maintenance.todo.line","request")
    catalog = fields.Binary()
    cost = fields.Float(compute="compute_cost",store=True)
    mtype = fields.Selection([
        ('preventive','Preventive'),
        ('corrective','Corrective'),
        ('periodic','Periodic'),
        ('proactive ','Proactive '),
        ('schedule','Scheduled'),
    ])
    equipment_number = fields.Char(
        string="Equipment Number",
        related="equipment_id.equipment_number",
        readonly=True,
        store=True
    )

    def archive_done_requests_cron(self,rec_limit=100,day_limit=30,archive_flag=True):
        last_month = datetime.date.today() - datetime.timedelta(days=day_limit)
        if archive_flag:
            requests = self.env["maintenance.request"].sudo().search([
                ('request_date','<',last_month),
                ('stage_id.done', '=', True)
            ],limit=rec_limit,order="request_date desc")
            for rec in requests:
                rec.active = False
        else:
            archived_requests = self.env["maintenance.request"].sudo().with_context(active_test=False).search([
                ('active', '=', False),
                ('request_date','<',last_month),
                ('stage_id.done', '=', True)
            ],limit=rec_limit,order="request_date desc")
            archived_requests.write({'active': True})

    # @api.depends("closed")
    # def cal_close(self):
    #     for rec in self:
    #         if rec.closed:
    #             close_date = datetime.date.today()

    @api.depends("equipment_id")
    def cal_todo(self):
        for rec in self:
            if rec.equipment_id:
                rec.todolines = False
                ids = []
                if rec.equipment_id.category_id:
                    rec.todo = rec.equipment_id.category_id.todo.id
                    for line in rec.equipment_id.category_id.todo.lines:
                        id = self.env["maintenance.todo.line"].create({
                            "name":line.name,
                            "maintenance_strategy":line.maintenance_strategy,
                            "maintenance_kind_id":line.maintenance_kind_id.id,
                            "check":line.check,
                            "note":line.note
                        })
                        ids.append(id.id)
                else:
                    rec.todo = rec.equipment_id.todo.id
                    for line in rec.equipment_id.todo.lines:
                        id = self.env["maintenance.todo.line"].create({
                            "name":line.name,
                            "maintenance_strategy":line.maintenance_strategy,
                            "maintenance_kind_id":line.maintenance_kind_id.id,
                            "check":line.check,
                            "note":line.note
                        })
                        ids.append(id.id)
                rec.todolines = [[6,False,ids]]

    @api.depends("purchase_orders","stock_pickings2")
    def compute_cost(self):
        for rec in self:
            cost = 0
            for porder in rec.purchase_orders:
                cost = cost + porder.amount_total
            for picking in rec.stock_pickings2:
                for move in picking.move_ids_without_package:
                    cost = cost + (move.product_id.standard_price *  move.product_uom_qty)
            rec.cost = cost

    @api.onchange("equipment_id")
    def onchange_address(self):
        for rec in self:
            rec.address_id = rec.equipment_id.address_id.id
                
    @api.model
    def create(self, vals):
        if vals.get('seq', 'New') == 'New':
            vals['seq'] = self.env['ir.sequence'].next_by_code('maintenance.seq') or '/'
        newId = super(Request, self).create(vals)
        return newId

    @api.depends("stock_pickings")
    def pickings_count(self):
        for rec in self:
            lines = []
            for req in rec.stock_pickings:
                for line in req.sparepart_lines:
                    lines.append((4,line.id))

            rec.sparepartslines = lines
            rec.stock_pickings_count = len(rec.stock_pickings)

    @api.depends("stock_pickings2.move_ids_without_package")
    def pickings_count2(self):
        for rec in self:
            moves = []
            for picking in rec.stock_pickings2:
                for move in picking.move_ids_without_package:
                    if move.id:
                        moves.append((4,move.id))

            rec.sparepartslines2 = moves

    def gen_sec(self):
        reqs = self.env["maintenance.request"].sudo().search([],order="id")
        for req in reqs:
            req.seq = self.env['ir.sequence'].next_by_code('maintenance.seq') or '/'

    def action_open_pickings(self):
        return {
            'name': _('Spareparts Transfers'),
            'type': 'ir.actions.act_window',
            'domain': [('maintenance_request_id', '=', self.id)],
            'context': {'default_maintenance_request_id': self.id},
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'maintenance.spareparts',
            'view_id': False,
            'views': [
                (self.env.ref('fb_wajiz_maintenance.spareparts_tree').id, 'tree'),
                (self.env.ref('fb_wajiz_maintenance.spareparts_form').id, 'form')
            ],
            'target': 'current',
        }

    # def sparepart(self):
    #     return {
    #         'name': _('Spareparts'),
    #         'type': 'ir.actions.act_window',
    #         # 'domain': [('patient', '=', self.account.id)],
    #         'context': {'default_maintenance_request_id': self.id},
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'maintenance.sparepart',
    #         'view_id': False,
    #         'views': [(self.env.ref('fb_wajiz_maintenance.sparepart_wizard_form').id, 'form')],
    #         'target': 'new',
    #     }
    
    def sparepart(self):
        return {
            'name': _('Spareparts'),
            'type': 'ir.actions.act_window',
            'context': {'default_maintenance_request_id': self.id},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'view_id': False,
            'views': [(self.env.ref('stock.view_picking_form').id, 'form')],
            'target': 'new',
        }

    def purchase(self):
        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'context': {'default_maintenance_request_id': self.id},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'view_id': False,
            'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
            'target': 'new',
        }

    @api.model
    def _cron_check_maintenance_requests(self):
        # Get all maintenance requests
        all_requests = self.env['maintenance.request'].search([])

        # Group requests by equipment and date
        grouped_requests = {}
        for request in all_requests:
            key = (request.equipment_id.id, request.request_date)
            if key not in grouped_requests:
                grouped_requests[key] = []
            grouped_requests[key].append(request)

        for key, requests in grouped_requests.items():
            equipment_id, request_date = key
            # Sort requests by plan interval and interval_step
            sorted_requests = sorted(requests, key=lambda r: (r.maintenance_plan_id.interval, r.maintenance_plan_id.interval_step))

            # Change the stage_id of all requests except the one with the highest priority
            for request in sorted_requests[:-1]:
                # Only update the request if it's in new stage
                if request.stage_id.id == 1:
                    request.write({'stage_id': 4})

        # Move requests on Friday to the next day
        for request in all_requests:
            if request.request_date.weekday() == 4:  # Friday
                request.write({'request_date': request.request_date + datetime.timedelta(days=1)})
                request.write({'scheduled_date': request.scheduled_date + datetime.timedelta(days=1)})

        return True
    
class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_payments_widget = fields.Binary(
        groups="base.group_user",
        exportable=False,
    )
    
    payments_summary = fields.Binary(
        groups="account.group_account_invoice,account.group_account_readonly,purchase.group_purchase_user",
        exportable=False,
    )

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    maintenance_request_id = fields.Many2one("maintenance.request")
    # invoice_summary = fields.Text(
    #     string="Invoice Summary",
    #     compute='_compute_invoice_summary',
    #     store=True
    # )

    # @api.depends('invoice_ids')
    # def _compute_invoice_summary(self):
    #     for order in self:
    #         summaries = []
    #         for invoice in order.invoice_ids:
    #             payments_widget = invoice.invoice_payments_widget or "No Payments"
    #             summary = (
    #                 f"The Invoice ({invoice.name}) "
    #                 f"With Total ({invoice.amount_total}) "
    #                 f"Have Payments: ({payments_widget})"
    #             )
    #             summaries.append(summary)
    #         order.invoice_summary = '\n'.join(payments_widget)

class Todo(models.Model):
    _name = "maintenance.todo"

    name = fields.Char(required=True)
    lines = fields.One2many("maintenance.todo.line","todo")

class TodoLine(models.Model):
    _name = "maintenance.todo.line"

    name = fields.Char(required=True)
    maintenance_kind_id = fields.Many2one("maintenance.kind")
    maintenance_strategy = fields.Selection([
        ('daily','Daily'),
        ('weekly','Weekly'),
        ('monthly','Monthly'),
        ('quarterly','Quarterly'),
        ('half_yearly','Half Yearly'),
        ('yearly','Yearly'),
    ])
    check = fields.Boolean()
    note = fields.Text()
    request = fields.Many2one("maintenance.request")
    todo = fields.Many2one("maintenance.todo")
    equipment_number = fields.Char(
        string="Equipment Number"
    )

class StockPicking(models.Model):
    _inherit = "stock.picking"

    spareparts_request_id = fields.Many2one("maintenance.spareparts")
    maintenance_request_id = fields.Many2one("maintenance.request")

class StockLocation(models.Model):
    _inherit = "stock.location"

    user_id = fields.Many2one("res.users",required=True)

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    user_id = fields.Many2one("res.users",required=True)

class SpareParts(models.Model):
    _name = 'maintenance.spareparts'
    _inherit = ["mail.thread","mail.activity.mixin"]
    _rec_name = "seq"
    _description = "SpareParts"
    
    seq = fields.Char(default="New")
    maintenance_request_id = fields.Many2one("maintenance.request")
    member_ids = fields.Many2many(
        'res.users', 'maintenance_team_users_rel', string="Team Members",
        related="maintenance_request_id.maintenance_team_id.member_ids",domain="[('company_ids', 'in', company_id)]")
    picking_type_id = fields.Many2one("stock.picking.type",string="Operation",required=True)
    from_loc = fields.Many2one("stock.location",string="Source Location",required=True)
    to_loc_dest = fields.Many2one("stock.location",string="Destination Location",required=True)
    sparepart_lines = fields.One2many('maintenance.spareparts.line',"spareparts_id")
    stock_pickings = fields.One2many("stock.picking","spareparts_request_id")
    stock_pickings_count = fields.Integer(compute="pickings_count",store=True)
    state = fields.Selection([
        ('draft','Draft'),
        ('submit','Submited'),
        ('confirm','Confirmed'),
        ('reject','Rejected'),
        ('cancel','Canceled'),
    ],default="draft",tracking="1")

    @api.model
    def create(self, vals):
        if vals.get('seq', 'New') == 'New':
            vals['seq'] = self.env['ir.sequence'].next_by_code('sparepart.seq') or '/'
        newId = super(SpareParts, self).create(vals)
        return newId
    
    @api.depends("stock_pickings")
    def pickings_count(self):
        for rec in self:
            rec.stock_pickings_count = len(rec.stock_pickings)

    def cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def draft(self):
        for rec in self:
            rec.state = 'draft'

    def reject(self):
        for rec in self:
            rec.state = 'reject'

    def confirm(self):
        stock_moves = []
        for rec in self:
            for line in self.sparepart_lines:
                stock_move_t = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    "location_id": self.from_loc.id,
                    "location_dest_id": self.to_loc_dest.id,
                    "name": line.product_id.name
                }
                stock_move = (0, 0, stock_move_t)
                stock_moves.append(stock_move)

            self.env["stock.picking"].create({
                "spareparts_request_id": self.id,
                "origin":self.seq,
                "picking_type_id": self.picking_type_id.id,
                "location_id":self.from_loc.id,
                "location_dest_id":self.to_loc_dest.id,
                "move_ids_without_package":stock_moves
            })

            rec.state = 'confirm'

    def action_open_pickings(self):
        return {
            'name': _('Spareparts Transfers'),
            'type': 'ir.actions.act_window',
            'domain': [('spareparts_request_id', '=', self.id)],
            'context': {'default_spareparts_request_id': self.id},
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'stock.picking',
            'view_id': False,
            'views': [
                (self.env.ref('stock.vpicktree').id, 'tree'),
                (self.env.ref('stock.view_picking_form').id, 'form')
            ],
            'target': 'current',
        }

    def sparepart(self):
        return {
            'name': _('Spareparts'),
            'type': 'ir.actions.act_window',
            # 'domain': [('patient', '=', self.account.id)],
            'context': {'default_maintenance_request_id': self.id},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.sparepart',
            'view_id': False,
            'views': [(self.env.ref('fb_wajiz_maintenance.sparepart_wizard_form').id, 'form')],
            'target': 'new',
        }

class SparePartsLines(models.Model):
    _name = 'maintenance.spareparts.line'

    spareparts_id = fields.Many2one('maintenance.spareparts')
    product_id = fields.Many2one("product.product",string="Product",required=True,domain="[('detailed_type','=','product')]")
    product_uom_qty = fields.Float(string="Demand")
    product_uom = fields.Many2one("uom.uom",string="UOM",required=True)

    state = fields.Selection([
        ('draft','Draft'),
        ('submit','Submited'),
        ('confirm','Confirmed'),
        ('reject','Rejected'),
        ('cancel','Canceled'),
    ],default="draft",tracking="1",related="spareparts_id.state")

    @api.onchange("product_id")
    def onchange_product(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id.id

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    picking_type_id = fields.Many2one("stock.picking.type",string="Operation", config_parameter='fb_wajiz_maintenance.picking_type_id')
    source_location = fields.Many2one("stock.location",string="Source Location", config_parameter='fb_wajiz_maintenance.source_location')
    planning_horizon = fields.Integer(string="Planning Horizon Limit", config_parameter='fb_wajiz_maintenance.planning_horizon',default=2)
    max_attachment_size = fields.Float(string="Max Attachment Size (MB)", config_parameter='fb_wajiz_maintenance.max_attachment_size',default=2)
    # TODO: max_file_upload_size 

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('fb_wajiz_maintenance.picking_type_id', self.picking_type_id.id)
        ICPSudo.set_param('fb_wajiz_maintenance.source_location', self.source_location.id)
        ICPSudo.set_param('fb_wajiz_maintenance.planning_horizon', self.planning_horizon)
        ICPSudo.set_param('fb_wajiz_maintenance.max_attachment_size', self.max_attachment_size)
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        picking_type_id = ICPSudo.get_param('fb_wajiz_maintenance.picking_type_id')
        source_location = ICPSudo.get_param('fb_wajiz_maintenance.source_location')
        planning_horizon = ICPSudo.get_param('fb_wajiz_maintenance.planning_horizon')
        max_attachment_size = ICPSudo.get_param('fb_wajiz_maintenance.max_attachment_size')
        
        res.update(
            picking_type_id=int(picking_type_id),
            source_location=int(source_location),
            planning_horizon=int(planning_horizon),
            max_attachment_size=float(max_attachment_size),
        )
        return res