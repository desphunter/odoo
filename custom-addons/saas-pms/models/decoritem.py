from odoo import api, fields, models
from odoo.tools.misc import format_date
from . import decortask

class decoritemunit(models.Model):
    _name = 'saaspms.decoritem.unit'
    _description = 'Managing the unit of decor item'

    name = fields.Char(string='Unit Name', required=True)
    type_category = fields.Selection([
        ('input', 'input'),
        ('output', 'output'),
    ], default='output')



class decoriteminput(models.Model):
    _name = 'saaspms.decoritem.input'
    _description = 'Managing the decor items template to be selected '

    name = fields.Char(string='Input Item Name', required=True, translate=True)
    code = fields.Char(string='Input Item Code')
    active = fields.Boolean(default=True, help="some")

    item_project = fields.Many2one('saaspms.decoritem.project', string='Project Item belong to',
                           help="some")
    unit_name = fields.Many2one('saaspms.decoritem.unit', string='Select a unit',
                                domain="[('type_category', '=', 'input')]",
                                help="some")
    unit_type = fields.Selection([
        ('Integer', 'Integer'),
        ('Float', 'Float'),
    ], string='Unit Type', default='Integer')
    description = fields.Text(string='Input Item Decription')



class decoritemproject(models.Model):
    _name = 'saaspms.decoritem.project'
    _description = 'Managing the item of decor project'

    name = fields.Char(string='Item Project Name', required=True, translate=True)
    code = fields.Char(string='Item Project Code')
    active = fields.Boolean(default=True, help="some")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if not recs:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        return recs.name_get()

    schedule_stage = fields.Char(string='Schedule Stage')
    priority = fields.Selection([
        ('Normal', '0'),
        ('Critical', '1'),
    ], string='Schedule Priority', default='0')
    period_type = fields.Selection([
        ('fixed', '1'),
        ('coefficient', '2'),
    ], string='Period Type', default='1')
    period_base = fields.Char(string='Period Base (day)')
    period_arrange = fields.Selection([
        ('None', '0'),
        ('OnWork', '1'),
        ('OffWork', '2'),
    ], string='Period Arrange', default='1')
    schedule_stage_seq = fields.Char(string='Sequence of Schedule Stage')
    description = fields.Text(string='Item Type Description')