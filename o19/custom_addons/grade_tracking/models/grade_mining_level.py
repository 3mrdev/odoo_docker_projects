from odoo import fields, models


class GradeMiningLevel(models.Model):
    _name = "grade.mining.level"
    _description = "Mining Level"
    _order = "project_id, sequence, id"

    sequence = fields.Integer(default=10)
    project_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        required=True,
        ondelete="restrict",
    )
    name = fields.Char(required=True)

    _name_unique = models.Constraint(
        "unique(project_id, name)",
        "A mining level name must be unique per mining location.",
    )

    def _compute_display_name(self):
        for level in self:
            level.display_name = (
                f"{level.project_id.name} - {level.name}" if level.project_id else level.name
            )
