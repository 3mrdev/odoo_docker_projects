from odoo import models,fields,api,_, Command

class CaseStudyTask(models.Model):
    _name = "swms.list.task"
    _description = "Case Study Task"

    name = fields.Char(required=True, translate=True)
    check = fields.Boolean()
    list_id = fields.Many2one("swms.list")
    case_id = fields.Many2one("swms.case")

class CaseStudyTaskList(models.Model):
    _name = "swms.list"
    _description = "Case Study Task List"

    name = fields.Char(required=True, translate=True)
    tasks_ids = fields.One2many("swms.list.task","list_id")

class CaseStudy(models.Model):
    _name = "swms.case"
    _description = "Case Study"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(default="New")
    description = fields.Html(required=True)
    researcher_id = fields.Many2one("res.users",required=True,tracking=True)
    research_date = fields.Date(required=True,tracking=True,default=fields.Date.today())
    list_id = fields.Many2one("swms.list",required=True,tracking=True)
    request_id = fields.Many2one("helpdesk.ticket",required=True)
    tasks_ids = fields.One2many("swms.list.task","case_id")
    state = fields.Selection([
        ('draft','Draft'),
        ('approve','Approved'),
    ],default="draft",tracking=True)

    @api.constrains('name')
    def check_documents(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('case.seq') or '/'

    @api.onchange("list_id")
    def _onchange_tasklist(self):
        for rec in self:
            if rec.list_id:
                ids = []
                rec.tasks_ids = False
                for task in rec.list_id.tasks_ids:
                    # ids.append(Command.create({
                    #     "name":task.name
                    # }))
                    task_id = self.env["swms.list.task"].sudo().create({
                        "name":task.name
                    })
                    ids.append(task_id.id)
                # rec.tasks_ids = Command.set(ids)
                rec.tasks_ids = [[6,False,ids]]
                

    def button_approve(self):
        for rec in self:
            rec.state = "approve"

    def button_draft(self):
        for rec in self:
            rec.state = "draft"