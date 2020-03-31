from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from . import decortask

class DecorProjectStage(models.Model):
    _name = 'saaspms.decorproject.stage'
    _description = '流程阶段'
    _order = 'sequence, id'

    # def _get_default_decorproject_ids(self):
    #     default_decorproject_id = self.env.context.get('default_decorproject_id')
    #     return [default_decorproject_id] if default_decorproject_id else None

    name = fields.Char(string='阶段名称', required=True, translate=True)
    sequence = fields.Integer(string='阶段序号', default=1)
    active = fields.Boolean(string='生效', default=True)
    fold = fields.Boolean(string='收起', default=False)
    state = fields.Selection([
        ('正在进行', 'ongoing'),
        ('完成', 'finished'),
        ('确认', 'confirmed'),
    ], string='状态', default='ongoing')



class DecorProject(models.Model):
    _name = "saaspms.decorproject"
    _description = "装修项目"
    _order = "sequence, name, id"

    def _compute_pretask_count(self):
        task_data = self.env['saaspms.decorpretask'].read_group([('decorproject_id', 'in', self.ids)], ['decorproject_id'], ['decorproject_id'])
        result = dict((data['decorproject_id'][0], data['decorproject_id_count']) for data in task_data)
        for project in self:
            project.pretask_count = result.get(project.id, 0)

    def _compute_scheduletask_count(self):
        task_data = self.env['saaspms.decorschedulepretask'].read_group([('decorproject_id', 'in', self.ids)],
                                                                    ['decorproject_id'], ['decorproject_id'])
        result = dict((data['decorproject_id'][0], data['decorproject_id_count']) for data in task_data)
        for project in self:
            project.scheduletask_count = result.get(project.id, 0)


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


    name = fields.Char(string="项目名称", index=True, required=True, tracking=True, translate=True)
    active = fields.Boolean(default=True, string='生效',
                            help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of Projects.")

    date_start = fields.Date(string='起始日期')
    date_required = fields.Date(string='截止日期', index=True, tracking=True)
    decor_address = fields.Text(string='装修地址')

    stage_id = fields.Many2one('saaspms.decorproject.stage', default=_default_stage, string='阶段ID',
                               group_expand='_group_expand_stage_id')
    state = fields.Selection(string='状态', related='stage_id.state')

    color = fields.Integer(string='色标')

    city_id = fields.Many2one('saaspms.decorproject.city', string='城市ID')

    pretask_count = fields.Integer(compute='_compute_pretask_count', string="预填任务个数")
    decorpretasks = fields.One2many('saaspms.decorpretask', 'decorproject_id', string='预填单')
    decorpretask_ids = fields.One2many('saaspms.decorpretask', 'decorproject_id', string='预填单ID集')

    scheduletask_count = fields.Integer(compute='_compute_scheduletask_count', string='计划任务个数')
    decorscheduletasks = fields.One2many('saaspms.decorscheduletask', 'decorproject_id', string="计划任务集")
    decorscheduletask_ids = fields.One2many('saaspms.decorscheduletask', 'decorproject_id', string='计划任务ID集')

    # _sql_constraints = [
    #     ('project_date_greater', 'check(date >= date_start)', 'Error! project start-date must be lower than project end-date.')
    # ]

    # def _compute_access_url(self):
    #     super(Project, self)._compute_access_url()
    #     for project in self:
    #         project.access_url = '/my/project/%s' % project.id
    #
    # def _compute_access_warning(self):
    #     super(Project, self)._compute_access_warning()
    #     for project in self.filtered(lambda x: x.privacy_visibility != 'portal'):
    #         project.access_warning = _(
    #             "The project cannot be shared with the recipient(s) because the privacy of the project is too restricted. Set the privacy to 'Visible by following customers' in order to make it accessible by the recipient(s).")


    # ---------------------------------------------------
    #  CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        # Prevent double project creation
        self = self.with_context(mail_create_nosubscribe=True)
        project = super(Project, self).create(vals)
        if not vals.get('subtask_project_id'):
            project.subtask_project_id = project.id
        if project.privacy_visibility == 'portal' and project.partner_id:
            project.message_subscribe(project.partner_id.ids)
        return project


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

    def open_decorscheduletasks(self):
        ctx = dict(self._context)
        ctx.update({'search_default_decorproject_id': self.id})
        action = self.env['ir.actions.act_window'].for_xml_id('saas-pms', 'view_decorproject_decorscheduletasks_all')
        return dict(action, context=ctx)

    def trans_pretoschedule_tasks(self):
        pretasks = self.env['saaspms.decorpretask'].read_group(
            [('decorproject_id', '=', self.id)],
            ['purchase_projectitem_code', 'sum_quantity:sum(quantity)'],
            ['purchase_projectitem_code'])

        # delete the existed scheduled tasks for this project, in order to prepare for the newly created ones.
        oldtasks = self.env['saaspms.decorscheduletask'].search([('decorproject_id', '=', self.id)])
        for ot in oldtasks:
            ot.unlink()

        # transfer pretasks to scheduled tasks
        # the prefilled information include: task_code, task_name, stage_sequence
        # the period of work task can be calculated automatically

        # retrieve the project_item template information and save them to a dictionary


        for pretask in pretasks:
            project_item_code = pretask['purchase_projectitem_code']
            offset_days = pretask['sum_quantity']

            project_item = self.env['saaspms.decoritem.project'].search([('code', '=', project_item_code)])
            for pi in project_item:
                project_item_name = project_item.name
                project_schedule_stage_seq = project_item.schedule_stagezh_CN.mo

                if project_item.period_type == 'fixed':
                    offset_days = project_item.period_base
                elif project_item.period_type == 'coefficient':
                    if pi.code == 'P0003':
                        if offset_days <= 20:
                            offset_days = '1'
                        elif offset_days > 20:
                            offset_days = '2'
                    elif pi.code == 'P0010':
                        offset_days = str(int(round(offset_days/20))+1)
                    elif pi.code == 'P0011':
                        offset_days = str(int(round(offset_days/100))+1)
                    elif pi.code =='P0012':
                        offset_days = '3'


            self.env['saaspms.decorscheduletask'].create({
                'decorproject_id': self.id,
                'code': project_item_code,
                'name': project_item_name,
                'stage_sequence': project_schedule_stage_seq,
                'offset_days': offset_days
            })


    def automake_schedule(self):
        scheduletasks = self.env['saaspms.decorscheduletask'].search([('decorproject_id', '=', self.id)])
        scheduletasks = sorted(scheduletasks, key=lambda x: x.stage_sequence)
        start_stage_seq = scheduletasks[0].stage_sequence

        offset_date_start = self.date_start
        for scheduletask in scheduletasks:
            if scheduletask.stage_sequence == start_stage_seq:
                scheduletask.date_start = self.date_start
                date_end = fields.Date.from_string(self.date_start) + timedelta(days=2)
                scheduletask.date_end = fields.Date.to_string(date_end)
                offset_date_start = fields.Date.to_string(date_end)
            else:
                scheduletask.date_start = offset_date_start
                date_end = fields.Date.from_string(offset_date_start) + timedelta(days=2)
                scheduletask.date_end = fields.Date.to_string(date_end)
                offset_date_start = fields.Date.to_string(date_end)


class ProjectTags(models.Model):
    """ Tags of project's tasks """
    _name = "saaspms.tags"
    _description = "标签"

    name = fields.Char('标签名称', required=True)
    color = fields.Integer(string='颜色')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]


class ProjectCity(models.Model):
    _name = "saaspms.decorproject.city"
    _description = "所在城市"

    name = fields.Char('城市名称', required=True)
    province = fields.Char('省份名称')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "City name already exists!"),
    ]
