# -*- coding: utf-8 -*-

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

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')

class UbisolHolidaysRequest(models.Model): 
    _inherit = 'hr.leave'
    _description = "Time Off"

    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('department', 'By Department'),
        ],
        string='Allocation Mode', readonly=True, required=True, default='employee',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    years_of_worked_state = fields.Integer('Улсад ажилласан жил', compute='_compute_years_of_worked_state', readonly=True)
    years_of_worked_company = fields.Float('Байгууллагад ажилласан жил', digits=(2,1), compute='_compute_years_of_worked_company', readonly=True)
    employee_holiday = fields.Integer('Ажилласан жил', compute='_compute_employee_holiday', readonly=True)
    warning_of_vacation = fields.Char('Ээлжийн амралт боломжтой эсэх', compute='_compute_warning_of_vacation', readonly=True)    
    base_vacation_days = fields.Integer('Суурь амралтын хоног', compute='_compute_base_vacation_days', default=15, readonly=True)
    request_status_type = fields.Selection(related='holiday_status_id.request_status_type', readonly=True)
    request_unit_hours = fields.Boolean('Custom Hours')
    request_unit_custom = fields.Boolean('Days-long custom hours')
    frequency_request = fields.Boolean('Давтамжтай үүсгэх эсэх')
    attendance_in_out = fields.Selection([
        ('check_in', 'Ирсэн'),
        ('check_out', 'Явсан')
        ], string='Ирсэн/явсан')
    overtime_type = fields.Selection([
        ('1', 'Илүү цагийн хүсэлт'),
        ('2', 'Тушаалаар хязгаарлагдах цаг'),
        ('3', 'Нийт батлах цаг')
        ], string='Илүү цагийн төрөл')    

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

    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for holiday in self:
            holiday.number_of_days_display = holiday.number_of_days  

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

                if(holiday.request_status_type == 'overtime' and holiday.frequency_request == True):
                    self.multiple_overtime(holiday)

        return holidays                                  

    def _get_department_child(self, department, res):
        if(department.child_ids):
            for child in department.child_ids:
                res.append(child.id)
                self._get_department_child(child, res)
        return res      

    def create_overtime(self, holiday, s_date, start_time, end_time, employee):
        holiday_values = []
        holiday_values.append({
            'name': holiday.name,
            'state': holiday.state,
            'report_note': holiday.report_note,
            'user_id': holiday.user_id.id,
            'manager_id': holiday.manager_id.id,
            'holiday_status_id': holiday.holiday_status_id.id,
            'employee_id': employee.id,
            'department_id': employee.department_id.id,
            'notes': holiday.notes,
            'date_from': str(s_date) + ' ' + str(start_time),
            'date_to': str(s_date) + ' ' + str(end_time),
            'number_of_days': holiday.number_of_days,
            'holiday_type': 'employee',
            'request_date_from': s_date,
            'request_date_to': s_date,
            'request_hour_from': holiday.request_hour_from,
            'request_hour_to': holiday.request_hour_to,
            'request_date_from_period': holiday.request_date_from_period
        }) 
        hr_att_req = self.env['hr.leave'].create(holiday_values)

        return True    

    def multiple_overtime(self, holiday):
        request_type = holiday.holiday_type
        start_date = holiday.request_date_from
        end_date = holiday.request_date_to
        start_time =  holiday.date_from.time()
        end_time =  holiday.date_to.time()
        first_att = 1
        delta = end_date-start_date
        count = 0

        while count <= delta.days:
            s_date =  start_date + timedelta(days=+count)
            if(request_type == 'department'):
                department_ids = self._get_department_child(holiday.department_id, [holiday.department_id.id])
                department_employees = self.env['hr.employee'].search([('department_id', 'in', department_ids)])
                if len(department_employees) > 0:
                    for department_employee in department_employees:
                        if(first_att == 1 and department_employees[0].id == department_employee.id):
                            holiday.holiday_type = 'employee'
                            holiday.employee_id = department_employee.id
                            holiday.date_from = str(s_date) + ' ' + str(start_time)
                            holiday.date_to = str(s_date) + ' ' + str(end_time)
                            holiday.request_date_from = s_date
                            holiday.request_date_to = s_date
                            first_att = 2
                        else:
                            self.create_overtime(holiday, s_date, start_time, end_time, department_employee)
            elif(request_type == 'employee'):
                if(first_att == 1):
                    holiday.date_from = str(s_date) + ' ' + str(start_time)
                    holiday.date_to = str(s_date) + ' ' + str(end_time)
                    holiday.request_date_from = s_date
                    holiday.request_date_to = s_date
                    first_att = 2
                else:
                    self.create_overtime(holiday, s_date, start_time, end_time, holiday.employee_id)

            count = count+1       