from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

class DecorProjectStage(models.Model):
    _name = 'saaspms.decorproject.stage'
    _description = 'DecorProject Stage Types'
    _order = 'sequence, id'

    # def _get_default_decorproject_ids(self):
    #     default_decorproject_id = self.env.context.get('default_decorproject_id')
    #     return [default_decorproject_id] if default_decorproject_id else None

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    fold = fields.Boolean(default=False)
    state = fields.Selection([
        ('ongoing', 'ongoing'),
        ('finished', 'finished'),
        ('confirmed', 'confirmed'),
    ], default='ongoing')



class DecorProject(models.Model):
    _name = "saaspms.decorproject"
    _description = "To manage the decoration work within a whole project."
    _order = "sequence, name, id"

    def _compute_pretask_count(self):
        task_data = self.env['saaspms.decorpretask'].read_group([('decorproject_id', 'in', self.ids)], ['decorproject_id'], ['decorproject_id'])
        result = dict((data['decorproject_id'][0], data['decorproject_id_count']) for data in task_data)
        for project in self:
            project.pretask_count = result.get(project.id, 0)


    @api.model
    def _default_stage(self):
        Stage = self.env['saaspms.decorproject.stage']
        return Stage.search([], limit=1)

    @api.model
    def _group_expand_stage_id(self, stages, domain, order):
        return stages.search([], order=order)

    # def _compute_access_url(self):
    #     super(DecorProject, self)._compute_access_url()
    #     for project in self:
    #         project.access_url = '/my/project/%s' % project.id


    name = fields.Char("Name", index=True, required=True, tracking=True)
    active = fields.Boolean(default=True,
        help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of Projects.")

    date_start = fields.Date(string='Start Date')
    date_required = fields.Date(string='Expiration Date', index=True, tracking=True)
    decor_address = fields.Text(string='Decor Address')

    stage_id = fields.Many2one('saaspms.decorproject.stage', default=_default_stage,
                               group_expand='_group_expand_stage_id')
    state = fields.Selection(related='stage_id.state')

    pretask_count = fields.Integer(compute='_compute_pretask_count', string="PreTask Count")
    decorpretasks = fields.One2many('saaspms.decorpretask', 'decorproject_id', string='Decor PreTask Activities')
    # decorpretask_ids = fields.One2many('saaspms.decorpretask', 'decorproject_id', string='Decor Pretasks')

    # decortasks = fields.One2many('saaspms.decortask', 'decorproject_id', string="Decor Task Activities")
    # decortask_ids = fields.One2many('saaspms.decortask', 'decorproject_id', string='Decor Tasks')

    # _sql_constraints = [
    #     ('project_date_greater', 'check(date >= date_start)', 'Error! project start-date must be lower than project end-date.')
    # ]

    def unlink(self):
        # Check project is empty
        for decorproject in self.with_context(active_test=False):
            if decorproject.decorpretasks:
                raise UserError(_('You cannot delete a project containing tasks. You can either archive it or first delete all of its tasks.'))
        result = super(DecorProject, self).unlink()
        return result


    # ---------------------------------------------------
    #  Actions
    # ---------------------------------------------------

    def open_decorpretasks(self):
        ctx = dict(self._context)
        ctx.update({'search_default_decorproject_id': self.id})
        action = self.env['ir.actions.act_window'].for_xml_id('saas-pms', 'view_decorproject_decorpretasks_all')
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