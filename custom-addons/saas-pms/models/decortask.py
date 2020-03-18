from . import decorproject
from odoo import api, fields, models
from odoo.tools.misc import format_date
from . import decorproject
from . import decoritem


class DecorScheduleTask(models.Model):
    _name = "saaspms.decorscheduletask"
    _description = "The decor scheduled tasks "

    active = fields.Boolean(default=True)
    code = fields.Char(string='Schedule Task Code')
    name = fields.Char(string='Schedule Task Name', translate=True)
    description = fields.Html(string='Description')

    stage_sequence = fields.Char(string='Schedule Task Stage Sequence')
    date_start = fields.Datetime(string="Schedule Task Starting Date", index=True)
    date_end = fields.Datetime(string='Schedule Task Ending Date', index=True, copy=False)
    # offset_days = fields.Integer(string='delta days')
    offset_days = fields.Char(string='offset days')


    decorproject_id = fields.Many2one('saaspms.decorproject', string='Decor Project',
                                      default=lambda self: self.env.context.get('default_decorproject_id'),
                                      index=True, tracking=True, change_default=True)




class DecorPreTask(models.Model):
    _name = 'saaspms.decorpretask'
    _description = 'Decor Purchased Item - PreTask'


    active = fields.Boolean(default=True)
    # name = fields.Char(string='PreTask Name', required=True, index=True)
    purchase_item = fields.Many2one('saaspms.decoritem.input', string='Purchase Item')

    decorpretask_zone = fields.Many2one('saaspms.decorpretask.zone', string='DecorPretask Zone')

    description = fields.Html(string='Description')

    quantity = fields.Float(string='Item Quantity')


    @api.depends('purchase_item.item_project.code')
    def _compute_purchase_projectitem_code(self):
        for item in self:
            item.purchase_projectitem_code = item.purchase_item.item_project.code

    @api.depends('purchase_item.item_project.name')
    def _compute_purchase_projectitem_name(self):
        for item in self:
            item.purchase_projectitem_name = item.purchase_item.item_project.name

    @api.depends('purchase_item.item_project')
    def _compute_purchase_projectitem(self):
        for item in self:
            item.purchase_projectitem = item.purchase_item.item_project



    purchase_projectitem_code = fields.Char(string='ProjectItem Code', compute='_compute_purchase_projectitem_code', store=True)
    purchase_projectitem_name = fields.Char(string='ProjectItem Name', compute='_compute_purchase_projectitem_name', store=True)
    purchase_projectitem = fields.Many2one('saaspms.decoritem.project', string='Project Item',
                                  compute='_compute_purchase_projectitem')

    decorproject_id = fields.Many2one('saaspms.decorproject', string='Decor Project',
                                      default=lambda self: self.env.context.get('decorproject_id'),
                                      index=True, tracking=True, change_default=True)



class DecorTaskZone(models.Model):
    _name = 'saaspms.decorpretask.zone'
    _description = 'Decor Task Zone'

    name = fields.Char(string='Zone Name')
    style = fields.Char(string='Zone Style')