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

    @api.model
    def default_get(self, fields_list):
        defaults = super(AttendanceRequest, self).default_get(fields_list)
        defaults = self._default_get_request_parameters(defaults)

        # defaults['state'] = 'confirm' if lt and lt.validation_type != 'no_validation' else 'draft'
        defaults['state'] = 'confirm'
        return defaults

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env.user.employee_id

    def _default_get_request_parameters(self, values):
        new_values = dict(values)
        global_from, global_to = False, False
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
        return new_values    

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
        ('both', '2 шатлалт'),
        ('manager', 'Ахлах')
        ], string="Validation Type", default='both')

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
        ('department', 'By Department')],
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
                        if not is_officer and current_employee != attendance.employee_id.parent_id:
                            raise UserError(_('You must be either %s\'s manager or attendance manager to approve this leave') % (attendance.employee_id.name))
                   
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
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not self.user_has_groups('hr_holidays.group_hr_holidays_user') and 'name' in groupby:
            raise UserError(_('Such grouping is not allowed.'))
        return super(AttendanceRequest, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def action_draft(self):
        if any(attendance.state not in ['confirm', 'refuse'] for attendance in self):
            raise UserError(_('Attendance request state must be "Refused" or "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })
        # linked_requests = self.mapped('linked_request_ids')
        # if linked_requests:
        #     linked_requests.action_draft()
        #     linked_requests.unlink()
        # self.activity_update()
        return True

    def action_confirm(self):
        if self.filtered(lambda attendance: attendance.state != 'draft'):
            raise UserError(_('Attendance request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})
        # attendances = self.filtered(lambda attendance_req: attendance_req.validation_type == 'no_validation')
        # if attendances:
        #     # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
        #     attendances.sudo().action_validate()
        # self.activity_update()
        return True

    def action_approve(self):
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(attendance.state != 'confirm' for attendance in self):
            raise UserError(_('Attendance request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda att: att.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})

        # Post a second message, more verbose than the tracking message
        # for attendance in self.filtered(lambda attendance: attendance.employee_id.user_id):
        #     attendance.message_post(
        #         body=_('Your %s planned on %s has been accepted' % (attendance.name, attendance.start_datetime)),
        #         partner_ids=attendance.employee_id.user_id.partner_id.ids)

        self.filtered(lambda att: not att.validation_type == 'both').action_validate()
        # if not self.env.context.get('leave_fast_create'):
        #     self.activity_update()
        return True    

    def action_validate(self):
        current_employee = self.env.user.employee_id
        if any(attendance.state not in ['confirm', 'validate1'] for attendance in self):
            raise UserError(_('Attendance request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.filtered(lambda attendance: attendance.validation_type == 'both').write({'second_approver_id': current_employee.id})
        self.filtered(lambda attendance: attendance.validation_type != 'both').write({'first_approver_id': current_employee.id})
        # for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
            # if holiday.holiday_type == 'category':
            #     employees = holiday.category_id.employee_ids
            # elif holiday.holiday_type == 'company':
            #     employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
            # else:
            #     employees = holiday.department_id.member_ids

            # conflicting_leaves = self.env['hr.leave'].with_context(
            #     tracking_disable=True,
            #     mail_activity_automation_skip=True,
            #     leave_fast_create=True
            # ).search([
            #     ('date_from', '<=', holiday.date_to),
            #     ('date_to', '>', holiday.date_from),
            #     ('state', 'not in', ['cancel', 'refuse']),
            #     ('holiday_type', '=', 'employee'),
            #     ('employee_id', 'in', employees.ids)])

            # if conflicting_leaves:
            #     # YTI: More complex use cases could be managed in master
            #     if holiday.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
            #         raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

            #     # keep track of conflicting leaves states before refusal
            #     target_states = {l.id: l.state for l in conflicting_leaves}
            #     conflicting_leaves.action_refuse()
            #     split_leaves_vals = []
            #     for conflicting_leave in conflicting_leaves:
            #         if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
            #             continue

            #         # Leaves in days
            #         if conflicting_leave.date_from < holiday.date_from:
            #             before_leave_vals = conflicting_leave.copy_data({
            #                 'date_from': conflicting_leave.date_from.date(),
            #                 'date_to': holiday.date_from.date() + timedelta(days=-1),
            #                 'state': target_states[conflicting_leave.id],
            #             })[0]
            #             before_leave = self.env['hr.leave'].new(before_leave_vals)
            #             before_leave._onchange_request_parameters()
            #             # Could happen for part-time contract, that time off is not necessary
            #             # anymore.
            #             # Imagine you work on monday-wednesday-friday only.
            #             # You take a time off on friday.
            #             # We create a company time off on friday.
            #             # By looking at the last attendance before the company time off
            #             # start date to compute the date_to, you would have a date_from > date_to.
            #             # Just don't create the leave at that time. That's the reason why we use
            #             # new instead of create. As the leave is not actually created yet, the sql
            #             # constraint didn't check date_from < date_to yet.
            #             if before_leave.date_from < before_leave.date_to:
            #                 split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
            #         if conflicting_leave.date_to > holiday.date_to:
            #             after_leave_vals = conflicting_leave.copy_data({
            #                 'date_from': holiday.date_to.date() + timedelta(days=1),
            #                 'date_to': conflicting_leave.date_to.date(),
            #                 'state': target_states[conflicting_leave.id],
            #             })[0]
            #             after_leave = self.env['hr.leave'].new(after_leave_vals)
            #             after_leave._onchange_request_parameters()
            #             # Could happen for part-time contract, that time off is not necessary
            #             # anymore.
            #             if after_leave.date_from < after_leave.date_to:
            #                 split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

            #     split_leaves = self.env['hr.leave'].with_context(
            #         tracking_disable=True,
            #         mail_activity_automation_skip=True,
            #         leave_fast_create=True,
            #         leave_skip_state_check=True
            #     ).create(split_leaves_vals)

            #     split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

            # values = holiday._prepare_employees_holiday_values(employees)
            # leaves = self.env['hr.leave'].with_context(
            #     tracking_disable=True,
            #     mail_activity_automation_skip=True,
            #     leave_fast_create=True,
            #     leave_skip_state_check=True,
            # ).create(values)

            # leaves._validate_leave_request()

        # employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        # employee_requests._validate_leave_request()
        # if not self.env.context.get('leave_fast_create'):
        #     employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        return True    

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(attendance.state not in ['draft', 'confirm', 'validate', 'validate1'] for attendance in self):
            raise UserError(_('Attendance request must be confirmed or validated in order to refuse it.'))

        validated_attendances = self.filtered(lambda att: att.state == 'validate1')
        validated_attendances.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_attendances).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # # Delete the meeting
        # self.mapped('meeting_id').unlink()
        # # If a category that created several holidays, cancel all related
        # linked_requests = self.mapped('linked_request_ids')
        # if linked_requests:
        #     linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        # for attendance in self:
        #     if attendance.employee_id.user_id:
        #         attendance.message_post(
        #             body=_('Your %s planned on %s has been refused') % (holiday.holiday_status_id.display_name, holiday.date_from),
        #             partner_ids=holiday.employee_id.user_id.partner_id.ids)

        # self._remove_resource_leave()
        # self.activity_update()
        return True    