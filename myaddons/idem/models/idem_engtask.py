from . import idem_engproduce
from odoo import api, fields, models
from odoo.tools.misc import format_date
from . import idem_engproduce
from . import idem_engpretask


class DecorScheduleTask(models.Model):
    _name = "saaspms.decorscheduletask"
    _description = "计划任务"

    active = fields.Boolean(default=True)
    code = fields.Char(string='计划任务编码')
    name = fields.Char(string='计划任务名称', translate=True)
    description = fields.Html(string='任务描述')

    stage_sequence = fields.Char(string='阶段排序')
    date_start = fields.Datetime(string="起始日期", index=True)
    date_end = fields.Datetime(string='截止日期', index=True, copy=False)
    # offset_days = fields.Integer(string='delta days')
    offset_days = fields.Char(string='工期')


    decorproject_id = fields.Many2one('saaspms.decorproject', string='项目ID',
                                      default=lambda self: self.env.context.get('default_decorproject_id'),
                                      index=True, tracking=True, change_default=True)


    scheduletask_worker_id = fields.Many2one('hr.employee', string='派工人员',
                                             domain=['|', ('job_title', '!=', '监理'), ('job_title', '!=', '项目经理')])




class DecorPreTask(models.Model):
    _name = 'saaspms.decorpretask'
    _description = '预填项目模块'


    active = fields.Boolean(default=True)
    # name = fields.Char(string='PreTask Name', required=True, index=True)
    purchase_item = fields.Many2one('saaspms.decoritem.input', string='预填任务')

    decorpretask_zone = fields.Many2one('saaspms.decorpretask.zone', string='任务区域')

    description = fields.Html(string='备注')

    quantity = fields.Float(string='数量')


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



    purchase_projectitem_code = fields.Char(string='定额项编码', compute='_compute_purchase_projectitem_code', store=True)
    purchase_projectitem_name = fields.Char(string='定额项名称', compute='_compute_purchase_projectitem_name', store=True)
    purchase_projectitem = fields.Many2one('saaspms.decoritem.project', string='定额项',
                                  compute='_compute_purchase_projectitem')

    decorproject_id = fields.Many2one('saaspms.decorproject', string='项目ID',
                                      default=lambda self: self.env.context.get('decorproject_id'),
                                      index=True, tracking=True, change_default=True)



class DecorTaskZone(models.Model):
    _name = 'saaspms.decorpretask.zone'
    _description = 'Decor Task Zone'

    name = fields.Char(string='区域名称')
    style = fields.Char(string='区域风格')