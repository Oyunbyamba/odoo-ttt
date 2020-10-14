# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class AttendanceRequest(models.Model):
    _name = "hr.attendance.request"
    _description = "Attendance request"
    _order = "start_datetime desc"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env.user.employee_id

    # def _default_get_request_parameters(self, values):
    #     new_values = dict(values)
        # global_from, global_to = False, False
        # # TDE FIXME: consider a mapping on several days that is not the standard
        # # calendar widget 7-19 in user's TZ is some custom input
        # if values.get('date_from'):
        #     user_tz = self.env.user.tz or 'UTC'
        #     localized_dt = timezone('UTC').localize(values['date_from']).astimezone(timezone(user_tz))
        #     global_from = localized_dt.time().hour == 7 and localized_dt.time().minute == 0
        #     new_values['request_date_from'] = localized_dt.date()
        # if values.get('date_to'):
        #     user_tz = self.env.user.tz or 'UTC'
        #     localized_dt = timezone('UTC').localize(values['date_to']).astimezone(timezone(user_tz))
        #     global_to = localized_dt.time().hour == 19 and localized_dt.time().minute == 0
        #     new_values['request_date_to'] = localized_dt.date()
        # if global_from and global_to:
        #     new_values['request_unit_custom'] = True
        # return new_values    

    name = fields.Char('Name', required=True)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),  # YTI This state seems to be unused. To remove
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
        ], string='Status', copy=False, default='draft',
        help="The status is set to 'To Submit', when a time off request is created." +
        "\nThe status is 'To Approve', when time off request is confirmed by user." +
        "\nThe status is 'Refused', when time off request is refused by manager." +
        "\nThe status is 'Approved', when time off request is approved by manager.")
    user_id = fields.Many2one('res.users', string='User')
    request_status_type = fields.Selection([
        ('overtime', 'Илүү цаг'),
        ('outside_work', 'Гадуур ажил')
        ], string="Request Status Type")
    validation_type = fields.Selection([
        ('both', '2 алхамт'),
        ('manager', 'Ахлах')
        ], string="Validation Type")

    def _employee_id_domain(self):
        if self.user_has_groups('hr_holidays.group_hr_holidays_user') or self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return []
        if self.user_has_groups('hr_holidays.group_hr_holidays_responsible'):
            return ['|', ('parent_id', '=', self.env.user.employee_id.id), ('user_id', '=', self.env.user.id)]
        return [('user_id', '=', self.env.user.id)]

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_default_employee, domain=_employee_id_domain)
    notes = fields.Text('Reasons')
    description = fields.Text('Description')
    # duration
    start_datetime = fields.Datetime(
        'Start Date', required=True,
        default=fields.Datetime.now)
    end_datetime = fields.Datetime(
        'End Date', required=True,
        default=fields.Datetime.now)
    request_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Allocation Mode', required=True, default='employee')
    category_id = fields.Many2one(
        'hr.employee.category', string='Employee Tag')
    mode_company_id = fields.Many2one(
        'res.company', string='Company')
    department_id = fields.Many2one(
        'hr.department', string='Department')
    first_approver_id = fields.Many2one(
        'hr.employee', string='First Approval')
    second_approver_id = fields.Many2one(
        'hr.employee', string='Second Approval')
    can_reset = fields.Boolean('Can reset', compute='_compute_can_reset')
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')    
    

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        for attendance in self:
            val_type = attendance.validation_type
            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if attendance.state == 'refuse':
                        raise UserError(_('Only a Leave Manager can reset a refused leave.'))
                    if attendance.start_datetime and attendance.end_datetime.date() <= fields.Date.today():
                        raise UserError(_('Only a Leave Manager can reset a started leave.'))
                    if attendance.employee_id != current_employee:
                        raise UserError(_('Only a Leave Manager can reset other people leaves.'))
                else:
                    # if val_type == 'no_validation' and current_employee == attendance.employee_id:
                    #     continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    attendance.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if attendance.employee_id == current_employee:
                        raise UserError(_('Only a Leave Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and attendance.request_type == 'employee':
                        if not is_officer and self.env.user != attendance.employee_id.leave_manager_id:
                            raise UserError(_('You must be either %s\'s manager or Leave manager to approve this leave') % (attendance.employee_id.name))
                   
    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_reset(self):
        for attendance in self:
            try:
                attendance._check_approval_update('draft')
            except (AccessError, UserError):
                attendance.can_reset = False
            else:
                attendance.can_reset = True

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        for attendance in self:
            try:
                if attendance.state == 'confirm':
                    attendance._check_approval_update('validate1')
                else:
                    attendance._check_approval_update('validate')
            except (AccessError, UserError):
                attendance.can_approve = False
            else:
                attendance.can_approve = True            

    @api.model
    
    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})
        holidays = self.filtered(lambda leave: leave.validation_type == 'no_validation')
        if holidays:
            # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
            holidays.sudo().action_validate()
        self.activity_update()
        return True