# -*- coding: utf-8 -*-

import logging
import math
import copy

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

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')

class UbisolHolidaysRequest(models.Model): 
    _inherit = 'hr.leave'
    _description = "Time Off"

    holiday_type = fields.Selection(selection=[
        ('employee', 'Ажилтан'),
        ('department', 'Хэлтэс'),
        ('company', 'Компани'),
    ])
    # holiday_type = fields.Selection(selection='_holiday_type_selection')
    years_of_worked_state = fields.Integer('Улсад ажилласан жил', compute='_compute_years_of_worked_state', readonly=True)
    years_of_worked_company = fields.Float('Байгууллагад ажилласан жил', digits=(2,1), compute='_compute_years_of_worked_company', readonly=True)
    employee_holiday = fields.Integer('Ажилласан жил', compute='_compute_employee_holiday', readonly=True)
    warning_of_vacation = fields.Char('Ээлжийн амралт боломжтой эсэх', compute='_compute_warning_of_vacation', readonly=True)    
    base_vacation_days = fields.Integer('Суурь амралтын хоног', compute='_compute_base_vacation_days', default=15, readonly=True)
    request_status_type = fields.Selection(related='holiday_status_id.request_status_type', readonly=True)
    request_unit_hours = fields.Boolean('Custom Hours')
    request_unit_custom = fields.Boolean('Days-long custom hours')
    frequency_request = fields.Boolean('Давтамжтай үүсгэх эсэх', default=False)
    attendance_in_out = fields.Selection([
        ('check_in', 'Ирсэн'),
        ('check_out', 'Явсан')
        ], string='Ирсэн/явсан')
    leave_overtime_type = fields.Selection(related='holiday_status_id.overtime_type', readonly=True)   
    allowed_overtime_time = fields.Integer('Батлах илүү цаг', required=True, default='')

    _sql_constraints = [
        ('type_value',
         "CHECK((holiday_type='employee' AND employee_id IS NOT NULL) or "
         "(holiday_type='department' AND department_id IS NOT NULL) )",
         "The employee or department of this request is missing. Please make sure that your user login is linked to an employee."),
        ('date_check2', "CHECK ((date_from <= date_to))", "The start date must be anterior to the end date."),
        ('duration_check', "CHECK ( number_of_days >= 0 )", "If you want to change the number of days you should use the 'period' mode"),
    ]


    def get_filtered_record(self):
        record_ids = []
        user = self.env['res.users'].browse(self._uid)
        employee_pool = self.env['hr.employee']
        employee = employee_pool.search([('user_id', '=', user.id)])
        if user.has_group('hr_holidays.group_hr_holidays_manager') | user.has_group('hr_holidays.group_hr_holidays_user'):
            record_ids = self.env['hr.leave'].search(['|', ('state', '=', "validate1"), ('employee_id.leave_manager_id', '=', user.id)]).ids
        elif user.has_group('hr_holidays.group_hr_holidays_responsible'):
            record_ids = self.env['hr.leave'].search([('employee_id.leave_manager_id', '=', user.id)]).ids
        return {
            'name': _('Leaves'),
            'domain': [('id', 'in', record_ids)],
            'res_model': 'hr.leave',
            'view_type': 'form',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }    

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        self.request_unit_half = False
        self.request_unit_custom = False
        self.request_unit_hours = False
        self.state = 'confirm' if self.validation_type != 'no_validation' else 'draft'    

    @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
                  'request_date_from', 'request_date_to',
                  'employee_id')
    def _onchange_request_parameters(self):
        if not self.request_date_from:
            self.date_from = False
            return

        if self.request_status_type == 'attendance':
            self.request_date_to = self.request_date_from
            self.request_hour_to = self.request_hour_from

        if not self.request_date_to:
            self.date_to = False
            return
       
        resource_calendar_id = self.employee_id.resource_calendar_id or self.env.company.resource_calendar_id
        domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
        attendances = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)

        # Must be sorted by dayofweek ASC and day_period DESC
        attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))

        default_value = DummyAttendance(0, 0, 0, 'morning', False)

        if resource_calendar_id.two_weeks_calendar:
            # find week type of start_date
            start_week_type = int(math.floor((self.request_date_from.toordinal() - 1) / 7) % 2)
            attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == start_week_type]
            attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != start_week_type]
            # First, add days of actual week coming after date_from
            attendance_filtred = [att for att in attendance_actual_week if int(att.dayofweek) >= self.request_date_from.weekday()]
            # Second, add days of the other type of week
            attendance_filtred += list(attendance_actual_next_week)
            # Third, add days of actual week (to consider days that we have remove first because they coming before date_from)
            attendance_filtred += list(attendance_actual_week)

            end_week_type = int(math.floor((self.request_date_to.toordinal() - 1) / 7) % 2)
            attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == end_week_type]
            attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != end_week_type]
            attendance_filtred_reversed = list(reversed([att for att in attendance_actual_week if int(att.dayofweek) <= self.request_date_to.weekday()]))
            attendance_filtred_reversed += list(reversed(attendance_actual_next_week))
            attendance_filtred_reversed += list(reversed(attendance_actual_week))

            # find first attendance coming after first_day
            attendance_from = attendance_filtred[0]
            # find last attendance coming before last_day
            attendance_to = attendance_filtred_reversed[0]
        else:
            # find first attendance coming after first_day
            attendance_from = next((att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()), attendances[0] if attendances else default_value)
            
            # find last attendance coming before last_day
            attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()), attendances[-1] if attendances else default_value)
        
        compensated_request_date_from = self.request_date_from
        compensated_request_date_to = self.request_date_to

        if self.request_unit_half:
            if self.request_date_from_period == 'am':
                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_from.hour_to)
            else:
                hour_from = float_to_time(attendance_to.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)
        elif self.request_unit_custom:
            if(self.leave_type_request_unit == 'hour'):
                hour_from = float_to_time(float(self.request_hour_from))
                hour_to = float_to_time(float(self.request_hour_to))
            else:
                hour_from = self.date_from.time()
                hour_to = self.date_to.time()
            compensated_request_date_from = self._adjust_date_based_on_tz(self.request_date_from, hour_from)
            compensated_request_date_to = self._adjust_date_based_on_tz(self.request_date_to, hour_to)
        elif self.leave_type_request_unit == 'hour':
            hour_from = float_to_time(float(self.request_hour_from))
            hour_to = float_to_time(float(self.request_hour_to))    
        else:
            hour_from = float_to_time(attendance_from.hour_from)
            hour_to = float_to_time(attendance_to.hour_to)

        tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC

        date_from = timezone(tz).localize(datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
        date_to = timezone(tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)

        self.update({'date_from': date_from, 'date_to': date_to})
        self._onchange_leave_dates()    

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self._sync_employee_details()
        # if self.employee_id.user_id != self.env.user and self._origin.employee_id != self.employee_id:
        #     self.holiday_status_id = False
        
    @api.onchange('holiday_status_id')
    def _compute_base_vacation_days(self):
        for holiday in self:
            if(holiday.request_status_type == 'vacation'):
                holiday.base_vacation_days = 15
                contract_date = holiday.employee_id.contract_signed_date
                if(contract_date):
                    today = fields.Date.today()
                    months = (today.year - contract_date.year)*12+today.month-contract_date.month
                    if(months < 11): 
                        holiday.base_vacation_days = round((months*15)/11)
   
    @api.onchange('holiday_status_id')
    def _compute_years_of_worked_state(self):
        for holiday in self:
            if(holiday.request_status_type == 'vacation'):
                holiday.years_of_worked_state = holiday.employee_id.years_of_civil_service
            else:
                holiday.years_of_worked_state = 0

    @api.onchange('holiday_status_id')
    def _compute_years_of_worked_company(self):
        for holiday in self:
            years = 0
            text = ''
            if(holiday.request_status_type == 'vacation'):
                contract_date = holiday.employee_id.contract_signed_date
                if(contract_date):
                    today = fields.Date.context_today(self)
                    months = (today.year - contract_date.year)*12+today.month-contract_date.month
                    if(months < 11): 
                        text = 'Ажилласан сар 11-с бага байна.'
                    years = months/12
            
            holiday.years_of_worked_company = years
            holiday.warning_of_vacation = text
                
    @api.onchange('holiday_status_id')
    def _compute_employee_holiday(self):
        for holiday in self:
            if(holiday.request_status_type == 'vacation'):
                if(holiday.employee_id.years_of_civil_service <= 5):  
                    holiday.employee_holiday = holiday.base_vacation_days
                elif(holiday.employee_id.years_of_civil_service >= 6 and holiday.employee_id.years_of_civil_service <= 10):
                    holiday.employee_holiday = holiday.base_vacation_days+3
                elif(holiday.employee_id.years_of_civil_service >= 11 and holiday.employee_id.years_of_civil_service <= 15):
                    holiday.employee_holiday = holiday.base_vacation_days+5
                elif(holiday.employee_id.years_of_civil_service >= 16 and holiday.employee_id.years_of_civil_service <= 20):
                    holiday.employee_holiday = holiday.base_vacation_days+7                 
                elif(holiday.employee_id.years_of_civil_service >= 21 and holiday.employee_id.years_of_civil_service <= 25):
                    holiday.employee_holiday = holiday.base_vacation_days+9
                elif(holiday.employee_id.years_of_civil_service >= 26 and holiday.employee_id.years_of_civil_service <= 31):
                    holiday.employee_holiday = holiday.base_vacation_days+11        
                elif(holiday.employee_id.years_of_civil_service >= 32):
                    holiday.employee_holiday = holiday.base_vacation_days+14    
            else:
                holiday.employee_holiday = 0  

    @api.onchange('holiday_status_id')
    def _change_frequency_request(self):
        for holiday in self:
            if holiday.leave_overtime_type == 'manager_proved_overtime':
                holiday.frequency_request = True 

    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for holiday in self:
            holiday.number_of_days_display = holiday.number_of_days  

    @api.constrains('date_from', 'date_to', 'state', 'employee_id')
    def _check_date(self):
        domains = [[
            ('date_from', '<=', holiday.date_to),
            ('date_to', '>=', holiday.date_from),
            ('employee_id', '=', holiday.employee_id.id),
            ('id', '!=', holiday.id),
        ] for holiday in self.filtered('employee_id')]
        domain = expression.AND([
            [('state', 'not in', ['cancel', 'refuse'])],
            expression.OR(domains)
        ])
        if self.search_count(domain):
            raise ValidationError(_('You can not set 2 times off that overlaps on the same day for the same employee.'))    

    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        if not self._context.get('leave_fast_create'):
            leave_types = self.env['hr.leave.type'].browse([values.get('holiday_status_id') for values in vals_list if values.get('holiday_status_id')])
            mapped_validation_type = {leave_type.id: leave_type.validation_type for leave_type in leave_types}

            for values in vals_list:
                employee_id = values.get('employee_id', False)
                leave_type_id = values.get('holiday_status_id')

                # Handle automatic department_id
                if not values.get('department_id'):
                    values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})

                # Handle no_validation
                if mapped_validation_type[leave_type_id] == 'no_validation':
                    values.update({'state': 'confirm'})

                # Handle double validation
                if mapped_validation_type[leave_type_id] == 'both':
                    self._check_double_validation_rules(employee_id, values.get('state', False))

        holidays = super(models.Model, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        for holiday in holidays:
            if self._context.get('import_file'):
                holiday._onchange_leave_dates()
            if not self._context.get('leave_fast_create'):
                # FIXME remove these, as they should not be needed
                if employee_id:
                    holiday.with_user(SUPERUSER_ID)._sync_employee_details()
                if 'number_of_days' not in values and ('date_from' in values or 'date_to' in values):
                    holiday.with_user(SUPERUSER_ID)._onchange_leave_dates()

                # Everything that is done here must be done using sudo because we might
                # have different create and write rights
                # eg : holidays_user can create a leave request with validation_type = 'manager' for someone else
                # but they can only write on it if they are leave_manager_id
                holiday_sudo = holiday.sudo()
                holiday_sudo.add_follower(employee_id)
                if holiday.validation_type == 'manager':
                    holiday_sudo.message_subscribe(partner_ids=holiday.employee_id.leave_manager_id.partner_id.ids)
                if holiday.holiday_status_id.validation_type == 'no_validation':
                    # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
                    holiday_sudo.action_validate()
                    holiday_sudo.message_subscribe(partner_ids=[holiday_sudo._get_responsible_for_approval().partner_id.id])
                    holiday_sudo.message_post(body=_("The time off has been automatically approved"), subtype="mt_comment") # Message from OdooBot (sudo)
                elif not self._context.get('import_file'):
                    holiday_sudo.activity_update()

        return holidays                                

    def _get_department_child(self, department, res):
        if(department.child_ids):
            for child in department.child_ids:
                res.append(child.id)
                self._get_department_child(child, res)
        return res      

    def _prepare_employees_holiday_values(self, employees):
        self.ensure_one()
        work_days_data = employees._get_work_days_data_batch(self.date_from, self.date_to)
        return [{
            'name': self.name,
            'holiday_type': 'employee',
            'holiday_status_id': self.holiday_status_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'request_date_from': self.date_from,
            'request_date_to': self.date_to,
            'notes': self.notes,
            'number_of_days': work_days_data[employee.id]['days'],
            'parent_id': self.id,
            'employee_id': employee.id,
            'state': 'validate',
            'allowed_overtime_time': self.allowed_overtime_time,
        } for employee in employees]    

    def action_validate(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['confirm', 'validate1'] for holiday in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.filtered(lambda holiday: holiday.validation_type == 'both').write({'second_approver_id': current_employee.id})
        self.filtered(lambda holiday: holiday.validation_type != 'both').write({'first_approver_id': current_employee.id})

        for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
            # if holiday.holiday_type == 'category':
            #     employees = holiday.category_id.employee_ids
            # elif holiday.holiday_type == 'company':
            #     employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
            # else:
            #     employees = holiday.department_id.member_ids
            if holiday.holiday_type == 'department':
                employees = holiday.department_id.member_ids

            if holiday.holiday_status_id.overtime_type == 'total_allowed_overtime':
                domain = [
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('holiday_status_id.overtime_type', '=', 'total_allowed_overtime'),
                    ('id', '!=', holiday.id)]
            else:
                domain = [
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('employee_id', 'in', employees.ids),
                    ('holiday_type', '=', 'employee'),
                    ('holiday_status_id.overtime_type', '!=', 'total_allowed_overtime')]   

            conflicting_leaves = self.env['hr.leave'].with_context(
                tracking_disable=True,
                mail_activity_automation_skip=True,
                leave_fast_create=True
            ).search(domain)

            if conflicting_leaves:
                # YTI: More complex use cases could be managed in master
                if holiday.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                    raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

                # keep track of conflicting leaves states before refusal
                target_states = {l.id: l.state for l in conflicting_leaves}
                conflicting_leaves.action_refuse()
                split_leaves_vals = []
                for conflicting_leave in conflicting_leaves:
                    if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
                        continue

                    # Leaves in days
                    if conflicting_leave.date_from < holiday.date_from:
                        before_leave_vals = conflicting_leave.copy_data({
                            'date_from': conflicting_leave.date_from.date(),
                            'date_to': holiday.date_from.date() + timedelta(days=-1),
                            'state': target_states[conflicting_leave.id],
                        })[0]
                        before_leave = self.env['hr.leave'].new(before_leave_vals)
                        before_leave._onchange_request_parameters()
                        
                        if before_leave.date_from < before_leave.date_to:
                            split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
                    if conflicting_leave.date_to > holiday.date_to:
                        after_leave_vals = conflicting_leave.copy_data({
                            'date_from': holiday.date_to.date() + timedelta(days=1),
                            'date_to': conflicting_leave.date_to.date(),
                            'state': target_states[conflicting_leave.id],
                        })[0]
                        after_leave = self.env['hr.leave'].new(after_leave_vals)
                        after_leave._onchange_request_parameters()
                        # Could happen for part-time contract, that time off is not necessary
                        # anymore.
                        if after_leave.date_from < after_leave.date_to:
                            split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

                split_leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                    leave_skip_state_check=True
                ).create(split_leaves_vals)

                split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

            if holiday.holiday_status_id.overtime_type != 'total_allowed_overtime':
                values = holiday._prepare_employees_holiday_values(employees)
                leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                    leave_skip_state_check=True,
                ).create(values)

                leaves._validate_leave_request()

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        return True  

