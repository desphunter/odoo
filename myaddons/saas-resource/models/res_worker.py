from datetime import timedelta

from odoo import api, fields, models,
from odoo.tools.misc import format_date


class DecorWorker(models.Model):
    _name = 'saaspms.decorworker'
    _description = 'Saas Worker'

    name = fields.Char('Name', index=True, required=True)
    mobile = fields.Char(string='Mobile No.', index=True, required=True)
    address = fields.Char(string='Address')
    qq = fields.Char(string='QQ No.')
    wechat = fields.Char(string='WeChat No.')

    type = fields.Many2many(
        'saaspms.decorworker.type', 'decor_worker_type_ref', 'decorworker_id', 'type_id',
        string='Worker Type')
    status = fields.Selection([
            ('available', 'worker is available now'),
            ('unavailable', 'Worker is unavailable now'),
        ],
        string='Availability', required=True,
        default='available')



class DecorWorkerType(models.Model):
    _name = 'saaspms.decorworker.type'
    _description = 'the type of worker'

    name = fields.Char("Type Name", required=True)
    color = fields.Integer(string='Type Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Type name already exists!"),
    ]