from odoo import api, fields, models
from odoo.tools.misc import format_date
from . import idem_engtask

class decoritemunit(models.Model):
    _name = 'saaspms.decoritem.unit'
    _description = '计量单位'

    name = fields.Char(string='计量单位', required=True)
    type_category = fields.Selection([
        ('输入', 'input'),
        ('输出', 'output'),
    ], string='计量单位类型', default='输出')



class decoriteminput(models.Model):
    _name = 'saaspms.decoritem.input'
    _description = '预填模版项'

    name = fields.Char(string='预填模版项名称', required=True, translate=True)
    code = fields.Char(string='预填模板项代码')
    active = fields.Boolean(default=True, string='生效', help="some")

    item_project = fields.Many2one('saaspms.decoritem.project', string='所属定额项',
                           help="some")
    unit_name = fields.Many2one('saaspms.decoritem.unit', string='计量单位',
                                domain="[('type_category', '=', 'input')]",
                                help="some")
    unit_type = fields.Selection([
        ('整数', 'Integer'),
        ('浮点', 'Float'),
    ], string='计量单位类型', default='整数')
    description = fields.Text(string='Input Item Decription')



class decoritemproject(models.Model):
    _name = 'saaspms.decoritem.project'
    _description = '定额模版项'

    name = fields.Char(string='定额模版名称', required=True, translate=True)
    code = fields.Char(string='定额模版代码')
    active = fields.Boolean(default=True, string='生效', help="some")

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     recs = self.browse()
    #     if not recs:
    #         recs = self.search([('code', operator, name)] + args, limit=limit)
    #     return recs.name_get()

    schedule_stage = fields.Char(string='计划阶段')
    priority = fields.Selection([
        ('一般', '0'),
        ('紧急', '1'),
    ], string='优先级', default='一般')
    period_type = fields.Selection([
        ('固定', '1'),
        ('系数', '2'),
    ], string='工期取值', default='固定')
    period_base = fields.Char(string='基数(天)')
    period_arrange = fields.Selection([
        ('正常', '0'),
        ('加班', '1'),
        ('夜班', '2'),
    ], string='排班', default='加班')
    schedule_stage_seq = fields.Char(string='阶段序号')
    description = fields.Text(string='描述')