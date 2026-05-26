from odoo import models,fields,api 

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    chassis_model = fields.Char(string="Model")
    chassis_submission_date = fields.Datetime(string='Submission Date')
    chassis_height = fields.Float(string="Height")
    chassis_width = fields.Float(string="Width")
    chassis_length = fields.Float(string="Length")
    chassis_empty_weight = fields.Float(string="Empty Weight")
    chassis_load_capacity = fields.Float(string="Load Capacity")
    chassis_max_weight = fields.Float(string="Max Weight")
    chassis_axies_number= fields.Float(string="Axies Number")
    chassis_axies_weight= fields.Float(string="Axies Weight")
    chassis_manufactur_year = fields.Float(string="Manufactur Year")
    chassis_manufactur_country = fields.Char(string="Manufactur Country")
    chassis_reference_number = fields.Char(string="General Traffic Department No")
    chassis_model_og_rop_letter_link = fields.Char(string="OG ROP Letter Link")
    chassis_vehicle_type = fields.Many2one('obc.vehicle.type',string="Vehicle Type")
    chassis_image = fields.Binary()
    chassis_image_link = fields.Char()

    chassis_numbers = fields.One2many('obc.chassis','sale_order_line_id',string="Chassis Numbers")
    chassis_numbers_count = fields.Integer(string="Chassis Numbers Count",compute='_compute_chassis_numbers_count',store=True)
    chassis_numbers_passed_count = fields.Integer(string="Passed",compute='_compute_chassis_numbers_count',store=True)
    chassis_numbers_failed_count = fields.Integer(string="Failed",compute='_compute_chassis_numbers_count',store=True)  
    chassis_numbers_inspection = fields.Char(string="Inspection",compute='_compute_chassis_numbers_count',store=True)

    gln_certs = fields.One2many('gln.cert','sale_order_line_id',string="GLN Certs")
    gln_certs_count = fields.Integer(string="GLN Certs Count",compute='_compute_gln_certs_count')
    max_gln_certs = fields.Integer(string="Max GLN Certificates",compute='_compute_is_rop_letter_and_gln_cert',store=True)
    gln_certs_count_display = fields.Char(string="GLN Certs Count Display",compute='_compute_gln_certs_count_display')
    is_rop_letter = fields.Boolean(string="Is ROP Letter",compute='_compute_is_rop_letter_and_gln_cert',store=True)
    is_gln_cert = fields.Boolean(string="Is GLN Cert",compute='_compute_is_rop_letter_and_gln_cert',store=True)

    @api.depends('product_id.is_gln_cert','product_id.is_rop_letter','product_id.max_gln_certs')
    def _compute_is_rop_letter_and_gln_cert(self):
        for record in self:
            record.is_rop_letter = record.product_id.is_rop_letter
            record.is_gln_cert = record.product_id.is_gln_cert
            record.max_gln_certs = record.product_id.max_gln_certs

    @api.depends('gln_certs')
    def _compute_gln_certs_count_display(self):
        for record in self:
            if record.is_gln_cert:
                record.gln_certs_count_display = f"{record.gln_certs_count}/{record.max_gln_certs}"
            else:
                record.gln_certs_count_display = "N/A"

    @api.depends('chassis_numbers.state')
    def _compute_chassis_numbers_count(self):
        for record in self:
            record.chassis_numbers_count = len(record.chassis_numbers)
            record.chassis_numbers_failed_count = len(record.chassis_numbers.filtered(lambda x: x.state == 'failed'))
            record.chassis_numbers_passed_count = len(record.chassis_numbers.filtered(lambda x: x.state == 'passed'))
            record.chassis_numbers_inspection = f"{record.chassis_numbers_passed_count}/{record.chassis_numbers_count}"

    @api.depends('gln_certs')
    def _compute_gln_certs_count(self):
        for record in self:
            record.gln_certs_count = len(record.gln_certs)
