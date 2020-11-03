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

class HrAttendance(models.Model):
    _inherit = 'hr.attendance' 

class AttendanceRequest(models.Model):
    _name = "hr.attendance.request"
    _description = "Overtime request"
    _order = "start_datetime desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
        ('confirm', 'Батлах ёстой'),
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
        ('outside_work', 'Гадуур ажил'),
        ('attendance', 'Ирцийн хүсэлт')
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
        'Эхлэх хугацаа', tracking=True,
        default=fields.Datetime.now)
    end_datetime = fields.Datetime(
        'Дуусах хугацаа', tracking=True,
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
    is_frequency_request = fields.Boolean(string='Is frequency request', default=1)
    attendance_date = fields.Datetime(
        'Нөхөх цаг', tracking=True)
    attendance_in_out = fields.Selection([
        ('check_in', 'Ирсэн'),
        ('check_out', 'Явсан')
        ], string='Ирсэн/явсан')    

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

    @api.onchange('request_status_type')
    def _onchange_request_type(self):
        now = datetime.now()
        if self.request_status_type == 'attendance':
            if not self.attendance_date:
                self.attendance_date = now
            self.start_datetime = False
            self.end_datetime = False
        else:
            self.attendance_date = False       
            if not self.start_datetime:        
                self.start_datetime = now
                self.end_datetime = now

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
            ('start_datetime', '<', attendance_req.end_datetime),
            ('end_datetime', '>', attendance_req.start_datetime),
            ('employee_id', '=', attendance_req.employee_id.id),
            ('request_status_type', '=', attendance_req.request_status_type),
            ('id', '!=', attendance_req.id),
        ] for attendance_req in self.filtered('employee_id')]
        domain = expression.AND([
            [('state', 'not in', ['cancel', 'refuse'])],
            expression.OR(domains)
        ])
        if self.search_count(domain):
            raise ValidationError(_('Ажилтанд ижил хугацааны завсар хүсэлт давхардуулан бүртгэх боломжгүй.'))    

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
                        raise UserError(_('Only a Overtime Manager can reset a refused overtime.'))
                    if attendance.request_status_type != 'attendance' and attendance.start_datetime and attendance.end_datetime.date() <= fields.Date.today():
                        raise UserError(_('Only a Overtime Manager can reset a started overtime.'))
                    if attendance.employee_id.id != current_employee:
                        raise UserError(_('Only a Overtime Manager can reset other people overtimes.'))
                else:
                    attendance.check_access_rule('write')

                    if attendance.employee_id.id == current_employee:
                        raise UserError(_('Only a Overtime Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and attendance.request_type == 'employee':
                        if not is_officer and current_employee != attendance.employee_id.parent_id.id:
                            raise UserError(_('You must be either %s\'s manager or attendance manager to approve this leave') % (attendance.employee_id.name))         

    def _check_double_validation_rules(self, employees, state):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.user_has_groups('hr_holidays.group_hr_holidays_user')
        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.parent_id.user_id != self.env.user)
            if employees and not is_leave_user:
                raise AccessError(_('You cannot first approve a leave for %s, because you are not his leave manager' % (employees[0].name,)))
        elif state == 'validate' and not is_leave_user:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a leave request'))                        


    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.user_id:
            self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)                                

    @api.model
    def create(self, vals):
        attendance = super(AttendanceRequest, self).create(vals)
        if(attendance.request_status_type == 'overtime' and attendance.is_frequency_request == 1):
            self.multiple_overtime(attendance)        
        elif(attendance.request_status_type == 'attendance'):
            attendance.start_datetime = attendance.attendance_date     

        attendance_sudo = attendance.sudo()
        attendance_sudo.add_follower(attendance.employee_id.id)
        attendance_sudo.message_subscribe(partner_ids=attendance.employee_id.parent_id.user_id.partner_id.ids)
        attendance_sudo.activity_update()      

        return attendance

    def write(self, values):
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')

        if not is_officer:
            if any(att.start_datetime.date() < fields.Date.today() for att in self):
                raise UserError(_('You must have manager rights to modify/validate a time off that already begun'))

        employee_id = values.get('employee_id', False)
        print("write values get employee_id")
        # if not self.env.context.get('leave_fast_create'):
        if values.get('state'):
            self._check_approval_update(values['state'])
            if any(attendance.validation_type == 'both' for attendance in self):
                if values.get('employee_id'):
                    employees = self.env['hr.employee'].browse(values.get('employee_id'))
                else:
                    employees = self.mapped('employee_id')
                self._check_double_validation_rules(employees, values['state'])
        
        result = super(AttendanceRequest, self).write(values)
        # if not self.env.context.get('leave_fast_create'):
        for attendance in self:
            if employee_id:
                attendance.add_follower(employee_id)
            
        return result
    

    def unlink(self):
        for attendance in self:
            error_message = _('You cannot delete a request which is in %s state')
            state_description_values = {elem[0]: elem[1] for elem in attendance._fields['state']._description_selection(attendance.env)}

            if not attendance.user_has_groups('hr_holidays.group_hr_holidays_user'):
                if any(attendance.state != 'draft'):
                    raise UserError(error_message % state_description_values.get(attendance[:1].state))
            else:
                for att in attendance.filtered(lambda att: att.state not in ['draft', 'cancel', 'confirm']):
                    raise UserError(error_message % (state_description_values.get(att.state),))
        return super(AttendanceRequest, attendance).unlink()

    def create_overtime(self, attendance, s_date, start_time, end_time, employee, req_type):
        attendance_values = []
        attendance_values.append({
            'name': attendance.name,
            'employee_id': employee.id,
            'notes': attendance.notes,
            'description': attendance.description,
            'start_datetime': str(s_date) + ' ' + str(start_time),
            'end_datetime': str(s_date) + ' ' + str(end_time),
            'state': attendance.state,
            'request_status_type': attendance.request_status_type,
            'validation_type': attendance.validation_type,
            'request_type': attendance.request_type,
            'department_id': employee.department_id.id
        }) 
        hr_att_req = attendance.env['hr.attendance.request'].create(attendance_values)
        if(req_type == 'dep'):
            hr_att_req.write({'request_type': 'employee'})  

        return True

    def _get_department_child(self, department, res):
        if(department.child_ids):
            for child in department.child_ids:
                res.append(child.id)
                self._get_department_child(child, res)
        return res            

    def multiple_overtime(self, attendance):
        request_type = attendance.request_type
        start_date = attendance.start_datetime.date()
        end_date = attendance.end_datetime.date()
        start_time =  attendance.start_datetime.time()
        end_time =  attendance.end_datetime.time()
        first_att = 1
        delta = end_date-start_date
        count = 0

        while count <= delta.days:
            s_date =  start_date + timedelta(days=+count)
            if(request_type == 'department'):
                department_ids = self._get_department_child(attendance.department_id, [attendance.department_id.id])
                department_employees = attendance.env['hr.employee'].search([('department_id', 'in', department_ids)])
                if len(department_employees) > 0:
                    for department_employee in department_employees:
                        if(first_att == 1 and department_employees[0].id == department_employee.id):
                            attendance.request_type = 'employee'
                            attendance.employee_id = department_employee.id
                            attendance.start_datetime = str(s_date) + ' ' + str(start_time)
                            attendance.end_datetime = str(s_date) + ' ' + str(end_time)
                            first_att = 2
                        else:
                            self.create_overtime(attendance, s_date, start_time, end_time, department_employee, 'dep')
            elif(request_type == 'employee'):
                if(first_att == 1):
                    attendance.start_datetime = str(s_date) + ' ' + str(start_time)
                    attendance.end_datetime = str(s_date) + ' ' + str(end_time)
                    first_att = 2
                else:
                    self.create_overtime(attendance, s_date, start_time, end_time, attendance.employee_id, 'emp')

            count = count+1     

    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not self.user_has_groups('hr_holidays.group_hr_holidays_user') and 'name' in groupby:
            raise UserError(_('Such grouping is not allowed.'))
        return super(AttendanceRequest, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def action_draft(self):
        if any(attendance.state not in ['confirm', 'refuse'] for attendance in self):
            raise UserError(_('Overtime request state must be "Refused" or "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })

        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_draft()
            linked_requests.unlink()
        self.activity_update()

        return True

    def action_confirm(self):
        if self.filtered(lambda attendance: attendance.state != 'draft'):
            raise UserError(_('Overtime request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})

        self.activity_update()
        return True

    def action_approve(self):
        for attendance in self:
            if(attendance.state != 'confirm'):
                raise UserError(_('Overtime request must be confirmed ("To Approve") in order to approve it.'))
            
            if(attendance.request_status_type == 'overtime'):  
                if attendance.department_id.id:
                    conflicting_requests = attendance.env['hr.attendance.request'].search([
                        ('start_datetime', '<=', attendance.end_datetime),
                        ('end_datetime', '>', attendance.start_datetime),
                        ('state', 'not in', ['cancel', 'refuse']),
                        ('request_status_type', '=', 'overtime'),
                        ('employee_id', '=', attendance.employee_id.id),
                        ('id', '!=', attendance.id)
                        ])
                    if conflicting_requests:
                        raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

            current_employee = attendance.env.user.employee_id
            attendance.filtered(lambda att: att.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})        
  
            if(attendance.employee_id.user_id):
                attendance.message_post(
                    body=_('Your %s planned on %s has been accepted' % (attendance.name, attendance.start_datetime)),
                    partner_ids=attendance.employee_id.user_id.partner_id.ids)

                attendance.filtered(lambda att: not att.validation_type == 'both').action_validate() 
                attendance.activity_update()

                if(attendance.request_status_type == 'attendance'):
                    attendance.calc_attendance()

        return True    

    def action_validate(self):
        for attendance in self:
            current_employee = attendance.env.user.employee_id
            if (attendance.state not in ['confirm', 'validate1']):
                raise UserError(_('Overtime request must be confirmed in order to approve it.'))

            attendance.write({'state': 'validate'})
            attendance.filtered(lambda att: att.validation_type == 'both').write({'second_approver_id': current_employee.id})
            attendance.filtered(lambda att: att.validation_type != 'both').write({'first_approver_id': current_employee.id})  
            attendance.activity_update()

            if(attendance.request_status_type == 'attendance'):
                attendance.calc_attendance()

        return True   

    def calc_attendance(self):
        att_obj = self.env['hr.attendance']
        now = datetime.now()
        sdate = datetime.strftime(now, "%Y-%m-%d 00:00:00")
        edate = datetime.strftime(now, "%Y-%m-%d 23:59:59")
        request_datetime = self.attendance_date

        hr_attendance_check_in = self.env['hr.attendance'].search(
            [('employee_id', '=', self.employee_id.id), ('check_in', '>=', sdate), ('check_in', '<=', edate)])
        hr_attendance_check_out = self.env['hr.attendance'].search(
            [('employee_id', '=', self.employee_id.id), ('check_out', '>=', sdate), ('check_out', '<=', edate)])   
        if(len(hr_attendance_check_in) == 0 or len(hr_attendance_check_out) == 0): 
            if hr_attendance_check_in:
                self.update_attendance(hr_attendance_check_in, request_datetime)
            elif hr_attendance_check_out:
                self.update_attendance(hr_attendance_check_out, request_datetime)
            else:
                if(self.attendance_in_out == 'check_in'):                        
                    att_obj.create({'employee_id': self.employee_id.id, 'check_in': request_datetime })
                else:
                    att_obj.create({'employee_id': self.employee_id.id, 'check_out': request_datetime })
        elif(hr_attendance_check_in and hr_attendance_check_out):
            self.update_attendance(hr_attendance_check_in, request_datetime)

        return True    

    def update_attendance(self, attendance, request_datetime):
        if(self.attendance_in_out == 'check_in'):
            if(attendance.check_in == False or (attendance.check_in and request_datetime < attendance.check_in)):
                attendance.write({'check_in': request_datetime})     
        elif(self.attendance_in_out == 'check_out'):
            if(attendance.check_out == False or (attendance.check_out and attendance.check_out and request_datetime > attendance.check_out)):
                attendance.write({'check_out': request_datetime}) 

        return True        

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(attendance.state not in ['draft', 'confirm', 'validate', 'validate1'] for attendance in self):
            raise UserError(_('Overtime request must be confirmed or validated in order to refuse it.'))

        validated_attendances = self.filtered(lambda att: att.state == 'validate1')
        validated_attendances.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_attendances).write({'state': 'refuse', 'second_approver_id': current_employee.id})

        # Delete the meeting
        self.mapped('meeting_id').unlink()
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        for attendance in self:
            if attendance.employee_id.user_id:
                attendance.message_post(
                    body=_('Your %s planned on %s has been refused') % (attendance.name, attendance.start_datetime),
                    partner_ids=attendance.employee_id.user_id.partner_id.ids)

        self.activity_update()
        return True    

    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------

    def _get_responsible_for_approval(self):
        self.ensure_one()
        responsible = self.env['res.users'].browse(SUPERUSER_ID)

        if self.employee_id.parent_id.user_id:
            responsible = self.employee_id.parent_id.user_id

        return responsible

    def activity_update(self):
        to_clean, to_do = self.env['hr.attendance.request'], self.env['hr.attendance.request']
        for attendance in self:
            if(attendance.request_status_type != 'attendance'):
                note = _('New %s Request created by %s from %s to %s') % (attendance.name, attendance.create_uid.name, fields.Datetime.to_string(attendance.start_datetime), fields.Datetime.to_string(attendance.end_datetime))
            else:
                note = _('New %s Request created by %s from %s') % (attendance.name, attendance.create_uid.name, fields.Datetime.to_string(attendance.start_datetime))
            if attendance.state == 'draft':
                to_clean |= attendance
            elif attendance.state == 'confirm':
                attendance.activity_schedule(
                    'ubisol_hr_attendance_request.mail_act_attendance_approval',
                    note=note,
                    user_id=attendance.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif attendance.state == 'validate1':
                attendance.activity_feedback(['ubisol_hr_attendance_request.mail_act_attendance_approval'])
                attendance.activity_schedule(
                    'ubisol_hr_attendance_request.mail_act_attendance_second_approval',
                    note=note,
                    user_id=attendance.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif attendance.state == 'validate':
                to_do |= attendance
            elif attendance.state == 'refuse':
                to_clean |= attendance
        if to_clean:
            to_clean.activity_unlink(['ubisol_hr_attendance_request.mail_act_attendance_approval', 'ubisol_hr_attendance_request.mail_act_attendance_second_approval'])
        if to_do:
            to_do.activity_feedback(['ubisol_hr_attendance_request.mail_act_attendance_approval', 'ubisol_hr_attendance_request.mail_act_attendance_second_approval'])


    ####################################################
    # Messaging methods
    #################################################### 

    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'validate':
            # leave_notif_subtype = self.holiday_status_id.leave_notif_subtype_id
            # return leave_notif_subtype or self.env.ref('ubisol_hr_attendance_request.mt_leave')
            self.env.ref('ubisol_hr_attendance_request.mt_attendance_overtime')
        return super(AttendanceRequest, self)._track_subtype(init_values)           

    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        # due to record rule can not allow to add follower and mention on validated leave so subscribe through sudo
        if self.state in ['validate', 'validate1']:
            self.check_access_rights('read')
            self.check_access_rule('read')
            return super(AttendanceRequest, self.sudo()).message_subscribe(partner_ids=partner_ids, channel_ids=channel_ids, subtype_ids=subtype_ids)
        return super(AttendanceRequest, self).message_subscribe(partner_ids=partner_ids, channel_ids=channel_ids, subtype_ids=subtype_ids)