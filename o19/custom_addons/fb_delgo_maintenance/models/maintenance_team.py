from odoo import api, fields, models


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    code = fields.Char(
        string='Team Code', required=True, copy=False, index='btree_not_null',
        help="Short unique code used to build the maintenance requests reference, "
             "e.g. ELEC/2026/0001. The request sequence is created with the code "
             "as prefix; changing the code later does not affect the sequence "
             "prefix nor existing request references.")
    sequence_id = fields.Many2one(
        'ir.sequence', string='Request Sequence', copy=False, readonly=True,
        help="Sequence used to generate the reference of the maintenance "
             "requests assigned to this team.")

    _code_unique = models.Constraint(
        'unique(code)',
        'The team code must be unique.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        teams.filtered(lambda t: not t.sequence_id)._ensure_request_sequence()
        return teams

    def write(self, vals):
        res = super().write(vals)
        if vals.get('code'):
            # Legacy teams: create the sequence lazily once a code is set.
            self.filtered(lambda t: t.code and not t.sequence_id)._ensure_request_sequence()
        return res

    def _ensure_request_sequence(self):
        for team in self.filtered(lambda t: t.code and not t.sequence_id):
            team.sequence_id = self.sudo().env['ir.sequence'].create({
                'name': f'Maintenance Requests {team.name}',
                'code': f'fb.maintenance.request.{team.code}',
                'prefix': f'{team.code}/%(year)s/',
                'padding': 4,
                'company_id': team.company_id.id or False,
            })
