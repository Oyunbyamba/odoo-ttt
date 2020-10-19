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
    _inherit = ['mail.thread']

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
        return new_values    

    name = fields.Char('Name', required=True)
    state = fields.Selection([
        ('draft', 'Илгээх'),
        ('cancel', 'Цуцлагдсан'),  # YTI This state seems to be unused. To remove
        ('confirm', 'Батлах'),
        ('refuse', 'Татгалзсан'),
        ('validate1', '2 дахь Зөвшөөрөл'),
        ('validate', 'Зөвшөөрсөн')
        ], string='Төлөв', copy=False, default='draft', tracking=True,
        help="The status is set to 'To Submit', when a time off request is created." +
        "\nThe status is 'To Approve', when time off request is confirmed by user." +
        "\nThe status is 'Refused', when time off request is refused by manager." +
        "\nThe status is 'Approved', when time off request is approved by manager.")
    user_id = fields.Many2one('res.users', string='User')
    request_status_type = fields.Selection([
        ('overtime', 'Илүү цаг'),
        ('outside_work', 'Гадуур ажил')
        ], default="overtime", string="Хүсэлтийн төрөл", required=True, tracking=True)
    validation_type = fields.Selection([
        ('both', '2 шатлалт'),
        ('manager', 'Ахлах')
        ], string="Зөвшөөрлийн төрөл", default='both')

    def _employee_id_domain(self):
        if self.user_has_groups('hr_holidays.group_hr_holidays_user') or self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return []
        if self.user_has_groups('hr_holidays.group_hr_holidays_responsible'):
            return ['|', ('parent_id', '=', self.env.user.employee_id.id), ('user_id', '=', self.env.user.id)]
        return [('user_id', '=', self.env.user.id)]

    employee_id = fields.Many2one(
        'hr.employee', string='Ажилтан', 
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, 
        default=_default_employee, domain=_employee_id_domain, tracking=True)
    notes = fields.Text('Шалтгаан', tracking=True)
    description = fields.Text('Тодорхойлолт', tracking=True)
    # duration
    start_datetime = fields.Datetime(
        'Эхлэх хугацаа', required=True, tracking=True,
        default=fields.Datetime.now)
    end_datetime = fields.Datetime(
        'Дуусах хугацаа', required=True, tracking=True,
        default=fields.Datetime.now)
    request_type = fields.Selection([
        ('employee', 'Ажилтнаар'),
        ('department', 'Хэлтэсээр')],
        string='Хүсэлтийн горим', required=True, default='employee', tracking=True)
    category_id = fields.Many2one(
        'hr.employee.category', string='Ажилтаны пайз')
    mode_company_id = fields.Many2one(
        'res.company', string='Компани')
    department_id = fields.Many2one(
        'hr.department', string='Хэлтэс')
    first_approver_id = fields.Many2one(
        'hr.employee', string='Эхний зөвшөөрөл')
    second_approver_id = fields.Many2one(
        'hr.employee', string='2 дахь зөвшөөрөл')
    can_reset = fields.Boolean('Can reset', compute='_compute_can_reset')
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')  
    number_of_hours_display = fields.Float(
        'Duration in hours', compute='_compute_number_of_hours_display', readonly=True,
        help='Number of hours of the time off request according to your working schedule. Used for interface.')
    number_of_days = fields.Float(
        'Duration (Days)', copy=False, tracking=True, compute='_onchange_leave_dates', readonly=True)    

    @api.onchange('request_type')
    def _onchange_type(self):
        if self.request_type == 'employee':
            if not self.employee_id:
                self.employee_id = self.env.user.employee_id.id
            self.department_id = False
        elif self.request_type == 'department':
            self.employee_id = False
            if not self.department_id:
                self.department_id = self.env.user.employee_id.department_id.id

    @api.onchange('start_datetime', 'end_datetime', 'employee_id')
    def _onchange_leave_dates(self):
        if self.start_datetime and self.end_datetime:
            self.number_of_days = self._get_number_of_days(self.start_datetime, self.end_datetime, self.employee_id.id)['days']
        else:
            self.number_of_days = 0

    def _get_calendar(self):
        self.ensure_one()
        return self.employee_id.resource_calendar_id or self.env.company.resource_calendar_id

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            return employee._get_work_days_data_batch(date_from, date_to)[employee.id]

        today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)
        hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)
        return {'days': hours / (today_hours or HOURS_PER_DAY), 'hours': hours}
        
    @api.constrains('start_datetime', 'end_datetime', 'state', 'employee_id')
    def _check_date(self):
        if self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError(_('Дуусах хугацаа эхлэх хугацаанаас бага байж болохгүй.'))

        domains = [[
            ('start_datetime', '<', attendance_req.start_datetime),
            ('end_datetime', '>', attendance_req.end_datetime),
            ('employee_id', '=', attendance_req.employee_id.id),
            ('id', '!=', attendance_req.id),
        ] for attendance_req in self.filtered('employee_id')]
        domain = expression.AND([
            [('state', 'not in', ['cancel', 'refuse'])],
            expression.OR(domains)
        ])
        if self.search_count(domain):
            raise ValidationError(_('1 ажилтанд ижил хугацааны завсар давхар ирцийн хүсэлт бүртгэх боломжгүй.'))    

    def _check_approval_update(self, state):
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id.id
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
                    if attendance.employee_id.id != current_employee:
                        raise UserError(_('Only a Leave Manager can reset other people leaves.'))
                else:
                    attendance.check_access_rule('write')

                    if attendance.employee_id.id == current_employee:
                        raise UserError(_('Only a Leave Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and attendance.request_type == 'employee':
                        if not is_officer and current_employee != attendance.employee_id.parent_id.id:
                            raise UserError(_('You must be either %s\'s manager or attendance manager to approve this leave') % (attendance.employee_id.name))

    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        for attendance in self:
            calendar = attendance._get_calendar()
            if attendance.start_datetime and attendance.end_datetime:
                if attendance.state == 'validate':
                    start_dt = attendance.start_datetime
                    end_dt = attendance.end_datetime
                    if not start_dt.tzinfo:
                        start_dt = start_dt.replace(tzinfo=UTC)
                    if not end_dt.tzinfo:
                        end_dt = end_dt.replace(tzinfo=UTC)
                    resource = attendance.employee_id.resource_id
                    intervals = calendar._attendance_intervals_batch(start_dt, end_dt, resource)[resource.id] \
                                - calendar._leave_intervals_batch(start_dt, end_dt, None)[False]  # Substract Global Leaves
                    number_of_hours = sum((stop - start).total_seconds() / 3600 for start, stop, dummy in intervals)
                else:
                    number_of_hours = attendance._get_number_of_days(attendance.start_datetime, attendance.end_datetime, attendance.employee_id.id)['hours']
                attendance.number_of_hours_display = number_of_hours or (attendance.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY))
            else:
                attendance.number_of_hours_display = 0                    
                   
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

        return True

    def action_confirm(self):
        if self.filtered(lambda attendance: attendance.state != 'draft'):
            raise UserError(_('Attendance request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})

        return True

    def action_approve(self):
        if any(attendance.state != 'confirm' for attendance in self):
            raise UserError(_('Attendance request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda att: att.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda att: not att.validation_type == 'both').action_validate()

        return True    

    def action_validate(self):
        current_employee = self.env.user.employee_id
        if any(attendance.state not in ['confirm', 'validate1'] for attendance in self):
            raise UserError(_('Attendance request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.filtered(lambda attendance: attendance.validation_type == 'both').write({'second_approver_id': current_employee.id})
        self.filtered(lambda attendance: attendance.validation_type != 'both').write({'first_approver_id': current_employee.id})

        return True    

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(attendance.state not in ['draft', 'confirm', 'validate', 'validate1'] for attendance in self):
            raise UserError(_('Attendance request must be confirmed or validated in order to refuse it.'))

        validated_attendances = self.filtered(lambda att: att.state == 'validate1')
        validated_attendances.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_attendances).write({'state': 'refuse', 'second_approver_id': current_employee.id})

        return True    

    