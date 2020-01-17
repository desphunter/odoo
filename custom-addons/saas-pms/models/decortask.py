from . import decorproject
from odoo import api, fields, models
from odoo.tools.misc import format_date


# class DecorTask(models.Model):
#     _name = "saaspms.decortask"
#     _description = "The decor tasks "
#     _date_name = "date_assign"
#     _order = "priority desc, sequence, id desc"
#
#     active = fields.Boolean(default=True)
#     name = fields.Char(string='Title', tracking=True, required=True, index=True)
#     description = fields.Html(string='Description')
#     priority = fields.Selection([
#         ('0', 'Normal'),
#         ('1', 'Important'),
#     ], default='0', index=True, string="Priority")
#     sequence = fields.Integer(string='Sequence', index=True, default=10,
#                               help="Gives the sequence order when displaying a list of tasks.")
#
#     status = fields.Selection([
#         ('created', 'task is created'),
#         ('ongoing', 'task is ongoing'),
#         ('finished', 'task is finished'),
#         ('confirmed', 'task is finished and confirmed'),
#     ], default='created', string='Task Status')
#
#     create_date = fields.Datetime("Created On", readonly=True, index=True)
#     write_date = fields.Datetime("Last Updated On", readonly=True, index=True)
#     date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
#     date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True)
#     date_deadline = fields.Date(string='Deadline', index=True, copy=False, tracking=True)
#     date_deadline_formatted = fields.Char(compute='_compute_date_deadline_formatted')
#     date_last_stage_update = fields.Datetime(string='Last Stage Update',
#                                              index=True,
#                                              copy=False,
#                                              readonly=True)
#     decorproject_id = fields.Many2one('saaspms.decorproject', string='Decor Project',
#                                       default=lambda self: self.env.context.get('default_decorproject_id'),
#                                       index=True, tracking=True, change_default=True)
#     planned_hours = fields.Float("Planned Hours",
#                                  help='It is the time planned to achieve the task. If this document has sub-tasks, it means the time needed to achieve this tasks and its childs.',
#                                  tracking=True)
#
#     plan_item_code = fields.Char(string='Task Plan Item Code', required=True, index=True)
#     plan_item_critical = fields.Boolean(string='Task Plan Item Critical or Not', default=True)
#
#     @api.depends('date_deadline')
#     def _compute_date_deadline_formatted(self):
#         for task in self:
#             task.date_deadline_formatted = format_date(self.env, task.date_deadline) if task.date_deadline else None



class DecorPreTask(models.Model):
    _name = 'saaspms.decorpretask'

    active = fields.Boolean(default=True)
    name = fields.Char(string='PreTask Name', required=True, index=True)
    description = fields.Html(string='Description')

    defined_code = fields.Char(string='PreTask Defined Purchase_code', required=True, index=True)
    worktime_coefficient = fields.Integer(string='Work Time Coefficient', default=1,
                                          help='Give the coefficient of the standard required time.')
    decorproject_id = fields.Many2one('saaspms.decorproject', string='Decor Project',
                                      default=lambda self: self.env.context.get('default_decorproject_id'),
                                      index=True, tracking=True, change_default=True)


