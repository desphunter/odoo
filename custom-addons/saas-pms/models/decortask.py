from . import decorproject

class DecorTaskStageType(models.Model):
    _name = 'saaspms.decortask.stagetype'
    _description = 'Decor Stage Types'
    _order = 'sequence, id'

    def _get_default_decorproject_ids(self):
        default_decorproject_id = self.env.context.get('default_decorproject_id')
        return [default_decorproject_id] if default_decorproject_id else None

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    decorproject_ids = fields.Many2many('saaspms.decorproject', 'decortask_stagetype_rel', 'stagetype_id', 'decorproject_id', string='Decor Projects',
        default=_get_default_decorproject_ids)
    legend_blocked = fields.Char(
        'Red Label', default=lambda s: _('Blocked'), translate=True, required=True,
        help='Override the default value displayed for the blocked state, when the task or issue is in that stage.')
    legend_done = fields.Char(
        'Green Label', default=lambda s: _('Ready for Next Stage'), translate=True, required=True,
        help='Override the default value displayed for the done state, when the task or issue is in that stage.')
    legend_normal = fields.Char(
        'Grey Label', default=lambda s: _('In Progress'), translate=True, required=True,
        help='Override the default value displayed for the normal state, when the task or issue is in that stage.')

    def unlink(self):
        stages = self
        default_decorproject_id = self.env.context.get('default_decorproject_id')
        if default_decorproject_id:
            shared_stages = self.filtered(lambda x: len(x.decorproject_ids) > 1 and default_decorproject_id in x.decorproject_ids.ids)
            tasks = self.env['saaspms.decortask'].with_context(active_test=False).search([('decorproject_id', '=', default_decorproject_id), ('stage_id', 'in', self.ids)])
            if shared_stages and not tasks:
                shared_stages.write({'decorproject_ids': [(3, default_decorproject_id)]})
                stages = self.filtered(lambda x: x not in shared_stages)
        return super(DecorStageType, stages).unlink()


class DecorTask(models.Model):
    _name = "saaspms.decortask"
    _description = "The decor tasks "
    _date_name = "date_assign"
    _order = "priority desc, sequence, id desc"

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        decorproject_id = self.env.context.get('default_decorproject_id')
        if not decorproject_id:
            return False
        return self.stage_find(decorproject_id)

    active = fields.Boolean(default=True)
    name = fields.Char(string='Title', tracking=True, required=True, index=True)
    description = fields.Html(string='Description')
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Priority")
    sequence = fields.Integer(string='Sequence', index=True, default=10,
                              help="Gives the sequence order when displaying a list of tasks.")
    stage_id = fields.Many2one('saaspms.decortask.stagetype', string='Stage', ondelete='restrict', tracking=True,
                               index=True,
                               default=_get_default_stage_id,
                               domain="[('decorproject_ids', '=', decorproject_id)]", copy=False)

    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True, index=True)
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True)
    date_deadline = fields.Date(string='Deadline', index=True, copy=False, tracking=True)
    date_deadline_formatted = fields.Char(compute='_compute_date_deadline_formatted')
    date_last_stage_update = fields.Datetime(string='Last Stage Update',
                                             index=True,
                                             copy=False,
                                             readonly=True)
    decorproject_id = fields.Many2one('saaspms.decorproject', string='Decor Project',
                                      default=lambda self: self.env.context.get('default_decorproject_id'),
                                      index=True, tracking=True, change_default=True)
    planned_hours = fields.Float("Planned Hours",
                                 help='It is the time planned to achieve the task. If this document has sub-tasks, it means the time needed to achieve this tasks and its childs.',
                                 tracking=True)

    plan_item_code = fields.Char(string='Task Plan Item Code', required=True, index=True)
    plan_item_critical = fields.Boolean(string='Task Plan Item Critical or Not', default=True)

    @api.depends('date_deadline')
    def _compute_date_deadline_formatted(self):
        for task in self:
            task.date_deadline_formatted = format_date(self.env, task.date_deadline) if task.date_deadline else None



class DecorPreTask(models.Model):
    _name = 'saaspms.decorpretask'

    active = fields.Boolean(default=True)
    name = fields.Char(string='PreTask Name', required=True, index=True)
    description = fields.Html(string='Description')

    defined_code = fields.Char(string='PreTask Defined Purchase_code', required=True, index=True)
    worktime_coefficient = fields.Integer(string='Work Time Coefficient', default=1,
                                          help='Give the coefficient of the standard required time.')
    decorproject_id = fields.Many2one('saaspms.decorproject', string='Decor Project', default=lambda self:self.env.context.get('default_decorproject_id'),
                                      index=True, tracking=True, change_default=True)


