# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import date_utils, float_round, float_is_zero


class EngProduce(models.Model):
    """ Manufacturing Orders """
    _name = 'idem.eng.produce'
    _description = 'IDEM Engineering Project Producing Order'
    _date_name = 'date_planned_start'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_planned_start asc,id'


    @api.model
    def _get_default_date_planned_finished(self):
        if self.env.context.get('default_date_planned_start'):
            return fields.Datetime.to_datetime(self.env.context.get('default_date_planned_start')) + datetime.timedelta(days=1)
        return datetime.datetime.now() + datetime.timedelta(hours=1)

    name = fields.Char(
        'Reference', copy=False, readonly=True, default=lambda x: _('New'))
    origin = fields.Char(
        'Source', copy=False,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Reference of the document that generated this production order request.")

    """
    Task1 : add idem.eng.project
    T2: eng.project type
    """
    engproject_id = fields.Many2one(
        'idem.eng.project', '工程项目',
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        readonly=True, required=True, check_company=True,
        states={'draft': [('readonly', False)]})

    """
    T3: Add project template
    """
    engproject_tmpl_id = fields.Many2one('idem.eng.project.template', 'Project Template', related='engproject_id.engproject_tmpl_id')


    # 量房日期
    date_measuring = fields.Datetime(
        '量房日期', copy=False, default=fields.Datetime.now,
        help="Date at which you get engineerning project basic metrics.",
        index=True, required=True, store=True
    )

    date_planned_start = fields.Datetime(
        '计划开始日期', copy=False, default=fields.Datetime.now,
        help="Date at which you plan to start the engineering project.",
        index=True, required=True, store=True)
    date_planned_finished = fields.Datetime(
        '计划完工日期',
        default=_get_default_date_planned_finished,
        help="Date at which you plan to finish the engineering project.",
        copy=False, store=True)
    date_deadline = fields.Datetime(
        'Deadline', copy=False, index=True,
        help="Informative date allowing to define when the manufacturing order should be processed at the latest to fulfill delivery on time.")
    date_start = fields.Datetime('Start Date', copy=False, index=True, readonly=True)
    date_finished = fields.Datetime('End Date', copy=False, index=True, readonly=True)


    # T4: develop the default function _get_default_date_planned_period
    # T5: modify the funtion of _get_default_date_planned_finished
    engproject_planned_period = fields.Integer(
        '工期',
        default=_get_default_date_planned_period,
        help="Period on which you plan to finish the engineering project.",
        copy=False, store=True)

    # T6: develop engbom
    # T7: develop engrouting - this would be very difficult
    engbom_id = fields.Many2one(
        'idem.engbom', '物料清单',
        readonly=True, states={'draft': [('readonly', False)]},
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
        check_company=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")
    engrouting_id = fields.Many2one(
        'idem.engrouting', '施工路径',
        readonly=True, compute='_compute_routing', store=True,
        help="The list of operations (list of work centers) to produce the finished product. The routing "
             "is mainly used to compute work center costs during operations and to plan future loads on "
             "work centers based on production planning.")

    # T8: 参考library checkout 还要建立一个idem_engproduce_stage, mapping the states
    # T9: 施工计划变更或者施工过程变更专门处理，都属于施工中的状态
    state = fields.Selection([
        ('draft', '一般立项'),
        ('confirmed', '核量确认'),
        ('planned', '施工计划'),
        ('progress', '施工中'),
        ('to_close', '验收'),
        ('done', '结项'),
        ('cancel', '取消')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: 一般立项.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * Planned: The WO are planned.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
    reservation_state = fields.Selection([
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting', 'Waiting Another Operation')],
        string='Material Availability',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Ready: The material is available to start the production.\n\
            * Waiting: The material is not available to start the production.\n\
            The material availability is impacted by the manufacturing readiness\
            defined on the BoM.")

    workorder_ids = fields.One2many(
        'mrp.workorder', 'production_id', 'Work Orders',
        copy=False, readonly=True)
    workorder_count = fields.Integer('# Work Orders', compute='_compute_workorder_count')
    workorder_done_count = fields.Integer('# Done Work Orders', compute='_compute_workorder_done_count')

    user_id = fields.Many2one(
        'res.users', 'Responsible', default=lambda self: self.env.user,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain=lambda self: [('groups_id', 'in', self.env.ref('mrp.group_mrp_user').id)])
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        index=True, required=True)

    priority = fields.Selection([('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')], 'Priority',
                                readonly=True, states={'draft': [('readonly', False)]}, default='1')
    is_locked = fields.Boolean('Is Locked', default=True, copy=False)
    show_final_lots = fields.Boolean('Show Final Lots', compute='_compute_show_lots')

    confirm_cancel = fields.Boolean(compute='_compute_confirm_cancel')

    @api.depends('move_raw_ids.state', 'move_finished_ids.state')
    def _compute_confirm_cancel(self):
        """ If the manufacturing order contains some done move (via an intermediate
        post inventory), the user has to confirm the cancellation.
        """
        domain = [
            ('state', '=', 'done'),
            '|',
                ('production_id', 'in', self.ids),
                ('raw_material_production_id', 'in', self.ids)
        ]
        res = self.env['stock.move'].read_group(domain, ['state', 'production_id', 'raw_material_production_id'], ['production_id', 'raw_material_production_id'], lazy=False)
        productions_with_done_move = {}
        for rec in res:
            production_record = rec['production_id'] or rec['raw_material_production_id']
            if production_record:
                productions_with_done_move[production_record[0]] = True
        for production in self:
            production.confirm_cancel = productions_with_done_move.get(production.id, False)


    @api.depends('product_id.tracking')
    def _compute_show_lots(self):
        for production in self:
            production.show_final_lots = production.product_id.tracking != 'none'


    # T11：标准工项的那个表，阶段排序和细项排序自动转换成routing
    @api.depends('bom_id.routing_id', 'bom_id.routing_id.operation_ids')
    def _compute_routing(self):
        for production in self:
            if production.bom_id.routing_id.operation_ids:
                production.routing_id = production.bom_id.routing_id.id
            else:
                production.routing_id = False

    @api.depends('workorder_ids')
    def _compute_workorder_count(self):
        data = self.env['mrp.workorder'].read_group([('production_id', 'in', self.ids)], ['production_id'], ['production_id'])
        count_data = dict((item['production_id'][0], item['production_id_count']) for item in data)
        for production in self:
            production.workorder_count = count_data.get(production.id, 0)

    @api.depends('workorder_ids.state')
    def _compute_workorder_done_count(self):
        data = self.env['mrp.workorder'].read_group([
            ('production_id', 'in', self.ids),
            ('state', '=', 'done')], ['production_id'], ['production_id'])
        count_data = dict((item['production_id'][0], item['production_id_count']) for item in data)
        for production in self:
            production.workorder_done_count = count_data.get(production.id, 0)

    @api.depends('move_raw_ids.state', 'move_finished_ids.state', 'workorder_ids', 'workorder_ids.state', 'qty_produced', 'move_raw_ids.quantity_done', 'product_qty')
    def _compute_state(self):
        """ Compute the production state. It use the same process than stock
        picking. It exists 3 extra steps for production:
        - planned: Workorder has been launched (workorders only)
        - progress: At least one item is produced.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        # TODO: duplicated code with stock_picking.py
        for production in self:
            if not production.move_raw_ids:
                production.state = 'draft'
            elif all(move.state == 'draft' for move in production.move_raw_ids):
                production.state = 'draft'
            elif all(move.state == 'cancel' for move in production.move_raw_ids):
                production.state = 'cancel'
            elif all(move.state in ['cancel', 'done'] for move in production.move_raw_ids):
                production.state = 'done'
            elif production.move_finished_ids.filtered(lambda m: m.state not in ('cancel', 'done') and m.product_id.id == production.product_id.id)\
                 and (production.qty_produced >= production.product_qty)\
                 and (not production.routing_id or all(wo_state in ('cancel', 'done') for wo_state in production.workorder_ids.mapped('state'))):
                production.state = 'to_close'
            elif production.workorder_ids and any(wo_state in ('progress') for wo_state in production.workorder_ids.mapped('state'))\
                 or production.qty_produced > 0 and production.qty_produced < production.product_uom_qty:
                production.state = 'progress'
            elif production.workorder_ids:
                production.state = 'planned'
            else:
                production.state = 'confirmed'

            # Compute reservation state
            # State where the reservation does not matter.
            if production.state in ('draft', 'done', 'cancel'):
                production.reservation_state = False
            # Compute reservation state according to its component's moves.
            else:
                relevant_move_state = production.move_raw_ids._get_relevant_state_among_moves()
                if relevant_move_state == 'partially_available':
                    if production.routing_id and production.routing_id.operation_ids and production.bom_id.ready_to_produce == 'asap':
                        production.reservation_state = production._get_ready_to_produce_state()
                    else:
                        production.reservation_state = 'confirmed'
                elif relevant_move_state != 'draft':
                    production.reservation_state = relevant_move_state


    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Reference must be unique per Company!'),
    ]

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            if self.move_raw_ids:
                self.move_raw_ids.update({'company_id': self.company_id})
            if self.picking_type_id and self.picking_type_id.company_id != self.company_id:
                self.picking_type_id = self.env['stock.picking.type'].search([
                    ('code', '=', 'mrp_operation'),
                    ('warehouse_id.company_id', '=', self.company_id.id),
                ], limit=1).id

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        if not self.product_id:
            self.bom_id = False
        else:
            bom = self.env['mrp.bom']._bom_find(product=self.product_id, picking_type=self.picking_type_id, company_id=self.company_id.id, bom_type='normal')
            if bom:
                self.bom_id = bom.id
                self.product_qty = self.bom_id.product_qty
                self.product_uom_id = self.bom_id.product_uom_id.id
            else:
                self.bom_id = False
                self.product_uom_id = self.product_id.uom_id.id
            return {'domain': {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        self.product_qty = self.bom_id.product_qty
        self.product_uom_id = self.bom_id.product_uom_id.id
        self.move_raw_ids = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]
        self.picking_type_id = self.bom_id.picking_type_id or self.picking_type_id

    @api.onchange('date_planned_start')
    def _onchange_date_planned_start(self):
        self.move_raw_ids.update({
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
        })
        if not self.routing_id:
            self.date_planned_finished = self.date_planned_start + datetime.timedelta(hours=1)


    def write(self, vals):
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_start' in vals:
            moves = (self.mapped('move_raw_ids') + self.mapped('move_finished_ids')).filtered(
                lambda r: r.state not in ['done', 'cancel'])
            moves.write({
                'date_expected': fields.Datetime.to_datetime(vals['date_planned_start']),
            })
        for production in self:
            if 'date_planned_start' in vals:
                if production.state in ['done', 'cancel']:
                    raise UserError(_('You cannot move a manufacturing order once it is cancelled or done.'))
                if production.workorder_ids and not self.env.context.get('force_date', False):
                    raise UserError(_('You cannot move a planned manufacturing order.'))
            if 'move_raw_ids' in vals and production.state != 'draft':
                production.move_raw_ids.filtered(lambda m: m.state == 'draft')._action_confirm()
        return res

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            picking_type_id = values.get('picking_type_id') or self._get_default_picking_type()
            picking_type_id = self.env['stock.picking.type'].browse(picking_type_id)
            if picking_type_id:
                values['name'] = picking_type_id.sequence_id.next_by_id()
            else:
                values['name'] = self.env['ir.sequence'].next_by_code('mrp.production') or _('New')
        if not values.get('procurement_group_id'):
            values['procurement_group_id'] = self.env["procurement.group"].create({'name': values['name']}).id
        production = super(MrpProduction, self).create(values)
        # Trigger move_raw creation when importing a file
        if 'import_file' in self.env.context:
            production._onchange_move_raw()
        return production

    def unlink(self):
        if any(production.state == 'done' for production in self):
            raise UserError(_('Cannot delete a manufacturing order in done state.'))
        self.action_cancel()
        not_cancel = self.filtered(lambda m: m.state != 'cancel')
        if not_cancel:
            productions_name = ', '.join([prod.display_name for prod in not_cancel])
            raise UserError(_('%s cannot be deleted. Try to cancel them before.') % productions_name)

        workorders_to_delete = self.workorder_ids.filtered(lambda wo: wo.state != 'done')
        if workorders_to_delete:
            workorders_to_delete.unlink()
        return super(MrpProduction, self).unlink()

    def action_toggle_is_locked(self):
        self.ensure_one()
        self.is_locked = not self.is_locked
        return True


    def _get_ready_to_produce_state(self):
        """ returns 'assigned' if enough components are reserved in order to complete
        the first operation in the routing. If not returns 'waiting'
        """
        self.ensure_one()
        first_operation = self.routing_id.operation_ids[0]
        # Get BoM line related to first opeation in rounting. If there is only
        # one opeation in the routing then it will need all BoM lines.
        bom_line_ids = self.env['mrp.bom.line']
        if len(self.routing_id.operation_ids) == 1:
            bom_line_ids = self.bom_id.bom_line_ids
        else:
            bom_line_ids = self.bom_id.bom_line_ids.filtered(lambda bl: bl.operation_id == first_operation)
        bom_line_ids = bom_line_ids.filtered(lambda bl: not bl._skip_bom_line(self.product_id))

        moves_in_first_operation = self.move_raw_ids.filtered(lambda m: m.bom_line_id in bom_line_ids)
        if all(move.state == 'assigned' for move in moves_in_first_operation):
            return 'assigned'
        return 'confirmed'

    def action_confirm(self):
        self._check_company()
        for production in self:
            if not production.move_raw_ids:
                raise UserError(_("Add some materials to consume before marking this MO as to do."))
            for move_raw in production.move_raw_ids:
                move_raw.write({
                    'group_id': production.procurement_group_id.id,
                    'unit_factor': move_raw.product_uom_qty / production.product_qty,
                    'reference': production.name,  # set reference when MO name is different than 'New'
                })
            production._generate_finished_moves()
            production.move_raw_ids._adjust_procure_method()
            (production.move_raw_ids | production.move_finished_ids)._action_confirm()
        return True

    def action_assign(self):
        for production in self:
            production.move_raw_ids._action_assign()
            production.workorder_ids._refresh_wo_lines()
        return True

    def open_produce_product(self):
        self.ensure_one()
        if self.bom_id.type == 'phantom':
            raise UserError(_('You cannot produce a MO with a bom kit product.'))
        action = self.env.ref('mrp.act_mrp_product_produce').read()[0]
        return action

    def button_plan(self):
        """ Create work orders. And probably do stuff, like things. """
        orders_to_plan = self.filtered(lambda order: order.routing_id and order.state == 'confirmed')
        for order in orders_to_plan:
            order.move_raw_ids.filtered(lambda m: m.state == 'draft')._action_confirm()
            quantity = order.product_uom_id._compute_quantity(order.product_qty, order.bom_id.product_uom_id) / order.bom_id.product_qty
            boms, lines = order.bom_id.explode(order.product_id, quantity, picking_type=order.bom_id.picking_type_id)
            order._generate_workorders(boms)
            order._plan_workorders()
        return True

    def _get_start_date(self):
        return self.date_start_wo or datetime.datetime.now()

    def _plan_workorders(self):
        """ Plan all the production's workorders depending on the workcenters
        work schedule"""
        self.ensure_one()

        # Schedule all work orders (new ones and those already created)
        qty_to_produce = max(self.product_qty - self.qty_produced, 0)
        qty_to_produce = self.product_uom_id._compute_quantity(qty_to_produce, self.product_id.uom_id)
        start_date = self._get_start_date()
        for workorder in self.workorder_ids:
            workcenters = workorder.workcenter_id | workorder.workcenter_id.alternative_workcenter_ids

            best_finished_date = datetime.datetime.max
            vals = {}
            for workcenter in workcenters:
                # compute theoretical duration
                time_cycle = workorder.operation_id.time_cycle
                cycle_number = float_round(qty_to_produce / workcenter.capacity, precision_digits=0, rounding_method='UP')
                duration_expected = workcenter.time_start + workcenter.time_stop + cycle_number * time_cycle * 100.0 / workcenter.time_efficiency

                # get first free slot
                # planning 0 hours gives the start of the next attendance
                from_date = workcenter.resource_calendar_id.plan_hours(0, start_date, compute_leaves=True, resource=workcenter.resource_id, domain=[('time_type', 'in', ['leave', 'other'])])
                # If the workcenter is unavailable, try planning on the next one
                if from_date is False:
                    continue
                to_date = workcenter.resource_calendar_id.plan_hours(duration_expected / 60.0, from_date, compute_leaves=True, resource=workcenter.resource_id, domain=[('time_type', 'in', ['leave', 'other'])])

                # Check if this workcenter is better than the previous ones
                if to_date and to_date < best_finished_date:
                    best_start_date = from_date
                    best_finished_date = to_date
                    best_workcenter = workcenter
                    vals = {
                        'workcenter_id': workcenter.id,
                        'capacity': workcenter.capacity,
                        'duration_expected': duration_expected,
                    }

            # If none of the workcenter are available, raise
            if best_finished_date == datetime.datetime.max:
                raise UserError(_('Impossible to plan the workorder. Please check the workcenter availabilities.'))

            # Instantiate start_date for the next workorder planning
            if workorder.next_work_order_id:
                if workorder.operation_id.batch == 'no' or workorder.operation_id.batch_size >= qty_to_produce:
                    start_date = best_finished_date
                else:
                    cycle_number = float_round(workorder.operation_id.batch_size / best_workcenter.capacity, precision_digits=0, rounding_method='UP')
                    duration = best_workcenter.time_start + cycle_number * workorder.operation_id.time_cycle * 100.0 / best_workcenter.time_efficiency
                    start_date = best_workcenter.resource_calendar_id.plan_hours(duration / 60.0, best_start_date, compute_leaves=True, resource=best_workcenter.resource_id, domain=[('time_type', 'in', ['leave', 'other'])])

            # Create leave on chosen workcenter calendar
            leave = self.env['resource.calendar.leaves'].create({
                'name': self.name + ' - ' + workorder.name,
                'calendar_id': best_workcenter.resource_calendar_id.id,
                'date_from': best_start_date,
                'date_to': best_finished_date,
                'resource_id': best_workcenter.resource_id.id,
                'time_type': 'other'
            })
            vals['leave_id'] = leave.id
            workorder.write(vals)
        self.with_context(force_date=True).write({
            'date_planned_start': self.workorder_ids[0].date_planned_start,
            'date_planned_finished': self.workorder_ids[-1].date_planned_finished
        })

    def button_unplan(self):
        if any(wo.state == 'done' for wo in self.workorder_ids):
            raise UserError(_("Some work orders are already done, you cannot unplan this manufacturing order."))
        elif any(wo.state == 'progress' for wo in self.workorder_ids):
            raise UserError(_("Some work orders have already started, you cannot unplan this manufacturing order."))
        self.workorder_ids.unlink()

    def _generate_workorders(self, exploded_boms):
        workorders = self.env['mrp.workorder']
        original_one = False
        for bom, bom_data in exploded_boms:
            # If the routing of the parent BoM and phantom BoM are the same, don't recreate work orders, but use one master routing
            if bom.routing_id.id and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.routing_id.id != bom.routing_id.id):
                temp_workorders = self._workorders_create(bom, bom_data)
                workorders += temp_workorders
                if temp_workorders: # In order to avoid two "ending work orders"
                    if original_one:
                        temp_workorders[-1].next_work_order_id = original_one
                    original_one = temp_workorders[0]
        return workorders

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']

        # Initial qty producing
        quantity = max(self.product_qty - sum(self.move_finished_ids.filtered(lambda move: move.product_id == self.product_id).mapped('quantity_done')), 0)
        quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom_id)
        if self.product_id.tracking == 'serial':
            quantity = 1.0

        for operation in bom.routing_id.operation_ids:
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'operation_id': operation.id,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'consumption': self.bom_id.consumption,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
                workorders[-1]._start_nextworkorder()
            workorders += workorder

            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation and move.bom_line_id.bom_id.routing_id == bom.routing_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation)

            # - Raw moves from a BoM where a routing was set but no operation was precised should
            #   be consumed at the last workorder of the linked routing.
            # - Raw moves from a BoM where no rounting was set should be consumed at the last
            #   workorder of the main routing.
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id and move.bom_line_id.bom_id.routing_id == bom.routing_id)
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.workorder_id and not move.bom_line_id.bom_id.routing_id)

                moves_finished |= self.move_finished_ids.filtered(lambda move: move.product_id != self.product_id and not move.operation_id)

            moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
            (moves_finished | moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_wo_lines()
        return workorders

    def _check_lots(self):
        # Check that the components were consumed for lots that we have produced.
        if self.product_id.tracking != 'none':
            finished_lots = self.finished_move_line_ids.mapped('lot_id')
            raw_finished_lots = self.move_raw_ids.mapped('move_line_ids.lot_produced_ids')
            if (raw_finished_lots - finished_lots):
                lots_short = raw_finished_lots - finished_lots
                error_msg = _(
                    'Some components have been consumed for a lot/serial number that has not been produced. '
                    'Unlock the MO and click on the components lines to correct it.\n'
                    'List of the components:\n'
                )
                move_lines = self.move_raw_ids.mapped('move_line_ids').filtered(lambda ml: lots_short & ml.lot_produced_ids)
                for ml in move_lines:
                    error_msg += ml.product_id.display_name + ' (' + ', '.join((lots_short & ml.lot_produced_ids).mapped('name')) + ')\n'
                raise UserError(error_msg)

    def action_cancel(self):
        """ Cancels production order, unfinished stock moves and set procurement
        orders in exception """
        if not self.move_raw_ids:
            self.state = 'cancel'
            return True
        self._action_cancel()
        return True

    def _action_cancel(self):
        documents_by_production = {}
        for production in self:
            documents = defaultdict(list)
            for move_raw_id in self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                iterate_key = self._get_document_iterate_key(move_raw_id)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents({move_raw_id: (move_raw_id.product_uom_qty, 0)}, iterate_key, 'UP')
                    for key, value in document.items():
                        documents[key] += [value]
            if documents:
                documents_by_production[production] = documents

        self.workorder_ids.filtered(lambda x: x.state not in ['done', 'cancel']).action_cancel()
        finish_moves = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        raw_moves = self.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        (finish_moves | raw_moves)._action_cancel()
        picking_ids = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        picking_ids.action_cancel()

        for production, documents in documents_by_production.items():
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if not parent or parent._name == 'stock.picking' and parent.state == 'cancel' or parent == production:
                    continue
                filtered_documents[(parent, responsible)] = rendering_context
            production._log_manufacture_exception(filtered_documents, cancel=True)
        return True

    def _get_document_iterate_key(self, move_raw_id):
        return move_raw_id.move_orig_ids and 'move_orig_ids' or False

    def _cal_price(self, consumed_moves):
        self.ensure_one()
        return True

    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()

        self.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        return self.write({'date_finished': fields.Datetime.now()})

    @api.model
    def get_empty_list_help(self, help):
        self = self.with_context(
            empty_list_help_document_name=_("manufacturing order"),
        )
        return super(MrpProduction, self).get_empty_list_help(help)

    def _log_downside_manufactured_quantity(self, moves_modification):

        def _keys_in_sorted(move):
            """ sort by picking and the responsible for the product the
            move.
            """
            return (move.picking_id.id, move.product_id.responsible_id.id)

        def _keys_in_groupby(move):
            """ group by picking and the responsible for the product the
            move.
            """
            return (move.picking_id, move.product_id.responsible_id)

        def _render_note_exception_quantity_mo(rendering_context):
            values = {
                'production_order': self,
                'order_exceptions': dict((key, d[key]) for d in rendering_context for key in d),
                'impacted_pickings': False,
                'cancel': False
            }
            return self.env.ref('mrp.exception_on_mo').render(values=values)

        documents = {}
        for move, (old_qty, new_qty) in moves_modification.items():
            document = self.env['stock.picking']._log_activity_get_documents(
                {move: (old_qty, new_qty)}, 'move_dest_ids', 'DOWN', _keys_in_sorted, _keys_in_groupby)
            for key, value in document.items():
                if documents.get(key):
                    documents[key] += [value]
                else:
                    documents[key] = [value]
        self.env['stock.picking']._log_activity(_render_note_exception_quantity_mo, documents)

    def _log_manufacture_exception(self, documents, cancel=False):

        def _render_note_exception_quantity_mo(rendering_context):
            visited_objects = []
            order_exceptions = {}
            for exception in rendering_context:
                order_exception, visited = exception
                order_exceptions.update(order_exception)
                visited_objects += visited
            visited_objects = self.env[visited_objects[0]._name].concat(*visited_objects)
            impacted_object = []
            if visited_objects and visited_objects._name == 'stock.move':
                visited_objects |= visited_objects.mapped('move_orig_ids')
                impacted_object = visited_objects.filtered(lambda m: m.state not in ('done', 'cancel')).mapped('picking_id')
            values = {
                'production_order': self,
                'order_exceptions': order_exceptions,
                'impacted_object': impacted_object,
                'cancel': cancel
            }
            return self.env.ref('mrp.exception_on_mo').render(values=values)

        self.env['stock.picking']._log_activity(_render_note_exception_quantity_mo, documents)
