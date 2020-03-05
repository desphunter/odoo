from odoo import api, fields, models
from odoo.tools.misc import format_date


class decoritemtype(models.Model):
    _name = 'saaspms.decoritem.type'
    _description = 'Managing the type type of decor item'

    name = fields.Char(string='Item Type Name', required=True, translate=True)
    active = fields.Boolean(default=True, help="some")
    type_category = fields.Selection([
        ('input', 'input'),
        ('output', 'output'),
    ], default='input')
    decription = fields.Text(string='Item Type Description')


class decoritemunit(models.Model):
    _name = 'saaspms.decoritem.unit'
    _description = 'Managing the unit of decor item'

    name = fields.Char(string='Unit Name', required=True)
    type_category = fields.Selection([
        ('input', 'input'),
        ('output', 'output'),
    ], default='output')


class decoriteminput(models.Model):
    _name = 'saaspms.decoriteminput'
    _description = 'Managing the decor items template to be selected '

    name = fields.Char(string='Input Item Name', required=True, translate=True)
    active = fields.Boolean(default=True, help="some")
    customer = fields.Char('Ziroom')
    type = fields.Many2one('saaspms.decoritem.type', string='Select Input Item Type',
                           domain="[('type_category', '=', 'input')]",
                           help="some")
    unit_name = fields.Many2one('saaspms.decoritem.unit', string='Select a unit',
                                domain="[('type_category', '=', 'input')]",
                                help="some")
    unit_type = fields.Selection([
        ('Integer', 'Integer'),
        ('Float', 'Float'),
    ], default='Integer')
    description = fields.Text(string='Input Item Decription')

