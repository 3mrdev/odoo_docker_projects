from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SparePartsPopupWizard(models.TransientModel):
    _name = 'maintenance.sparepart'

    # @api.model
    # def default_get(self,fields):
    #     res = super(SparePartsPopupWizard,self).default_get(fields)
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #     picking_type_id = ICPSudo.get_param('fb_wajiz_maintenance.picking_type_id')
    #     source_location = ICPSudo.get_param('fb_wajiz_maintenance.source_location')
    #     if source_location:
    #         res.update({
    #             "from_loc":int(source_location)
    #         })
    #     if picking_type_id:
    #         res.update({
    #             "picking_type_id":int(picking_type_id)
    #         })
    #     return res
    
    maintenance_request_id = fields.Many2one("maintenance.request")
    picking_type_id = fields.Many2one("stock.picking.type",related="maintenance_request_id.maintenance_team_id.picking_type_id",string="Operation",required=True)
    from_loc = fields.Many2one("stock.location",related="maintenance_request_id.maintenance_team_id.source_location",string="Source Location",required=True)
    to_loc_dest = fields.Many2one("stock.location",related="maintenance_request_id.maintenance_team_id.location",string="Destination Location")
    sparepart_lines = fields.One2many('maintenance.sparepart.line',"spareparts_id")
    
    def confirm(self):
        stock_moves = []
        for line in self.sparepart_lines:
            stock_move_t = {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
            }
            stock_move = (0, 0, stock_move_t)
            stock_moves.append(stock_move)

        if self.to_loc_dest:
            self.env["maintenance.spareparts"].create({
                "picking_type_id": self.picking_type_id.id,
                "from_loc":self.from_loc.id,
                "to_loc_dest":self.to_loc_dest.id,
                "state": "submit",
                "sparepart_lines":stock_moves
            })
        else:
            raise ValidationError("Your team doesn't have a storage location please contact your admin")


class SparePartsLines(models.TransientModel):
    _name = 'maintenance.sparepart.line'

    spareparts_id = fields.Many2one('maintenance.sparepart')
    product_id = fields.Many2one("product.product",string="Product",required=True,domain="[('detailed_type','=','product')]")
    product_uom_qty = fields.Float(string="Demand")
    product_uom = fields.Many2one("uom.uom",string="UOM",required=True)

    @api.onchange("product_id")
    def onchange_product(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id.id

class MassEditingWizard(models.TransientModel):
    _name = 'fb_wajiz.mass.editing.wizard'

    equipment_ids = fields.Many2many('maintenance.equipment', readonly=True)
    op_type = fields.Selection([
        ('refresh','Refresh Address'),
        ('refresh_todo','Refresh Todo List'),
        ('generate','Generate Plans'),
    ])

    def action_update(self):
        for rec in self:
            
            for equipment in rec.equipment_ids:
                if rec.op_type == "refresh":
                    for request in equipment.maintenance_ids:
                        request.address_id = equipment.address_id.id or False
                        request.employee_id = equipment.employee_id.id or False
                elif rec.op_type == "refresh_todo":
                    for request in equipment.maintenance_ids:
                        if request.equipment_id:
                            request.todolines = False
                            ids = []
                            if request.equipment_id.category_id:
                                request.todo = request.equipment_id.category_id.todo.id
                                for line in request.equipment_id.category_id.todo.lines:
                                    id = self.env["maintenance.todo.line"].create({
                                        "name":line.name,
                                        "maintenance_strategy":line.maintenance_strategy,
                                        "maintenance_kind_id":line.maintenance_kind_id.id,
                                        "check":line.check,
                                        "note":line.note
                                    })
                                    ids.append(id.id)
                            else:
                                request.todo = request.equipment_id.todo.id
                                for line in request.equipment_id.todo.lines:
                                    id = self.env["maintenance.todo.line"].create({
                                        "name":line.name,
                                        "maintenance_strategy":line.maintenance_strategy,
                                        "maintenance_kind_id":line.maintenance_kind_id.id,
                                        "check":line.check,
                                        "note":line.note
                                    })
                                    ids.append(id.id)
                            request.todolines = [[6,False,ids]]
                elif rec.op_type == "generate":
                    for plan in equipment.maintenance_plan_ids: 
                        if plan.maintenance_open_count < 1:
                            plan.button_manual_request_generation()
                else:
                    raise ValidationError("Choose Type Please !")