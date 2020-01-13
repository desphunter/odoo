from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
from . import decortask


class DecorProject(models.Model):
    _name = "saaspms.decorproject"
    _description = "To manage the decoration work within a whole project."
    _order = "sequence, name, id"

    name = fields.Char("Name", index=True, required=True, tracking=True)
    active = fields.Boolean(default=True,
        help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of Projects.")

    date_start = fields.Date(string='Start Date')
    date_required = fields.Date(string='Expiration Date', index=True, tracking=True)
    decor_address = fields.Text(string='Decor Address')

    stagetype_ids = fields.Many2many('saaspms.decortask.stagetype', 'decortask_stagetype_rel', 'decorproject_id', 'stagetype_id', string='Tasks Stages')

    decortasks = fields.One2many('saaspms.decortask', 'decorproject_id', string="Decor Task Activities")
    decortask_ids = fields.One2many('saaspms.decortask', 'decorproject_id', string='Decor Tasks',
                               domain=[('stage_id', '=', False)])

    _sql_constraints = [
        ('project_date_greater', 'check(date >= date_start)', 'Error! project start-date must be lower than project end-date.')
    ]

    def unlink(self):
        # Check project is empty
        for decorproject in self.with_context(active_test=False):
            if decorproject.decortasks:
                raise UserError(_('You cannot delete a project containing tasks. You can either archive it or first delete all of its tasks.'))
        result = super(DecorProject, self).unlink()
        return result


    # ---------------------------------------------------
    #  Actions
    # ---------------------------------------------------

    def open_tasks(self):
        ctx = dict(self._context)
        ctx.update({'search_default_decorproject_id': self.id})
        action = self.env['ir.actions.act_window'].for_xml_id('decorproject', 'act_saaspms_decorproject_2_saaspms_decortask_all')
        return dict(action, context=ctx)



class ProjectTags(models.Model):
    """ Tags of project's tasks """
    _name = "saaspms.tags"
    _description = "Saas PMS Tags"

    name = fields.Char('Tag Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]