# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta

class CreateAttendanceFilter(models.TransientModel):
  _name = 'create.attendance.filter'
  _description = 'Create Attendance Filter Wizard'

  start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
  end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))

  def _default_employee(self):
        return self.env.user.employee_id

  def _employee_id_domain(self):
      if self.user_has_groups('hr_attendance.group_hr_attendance_user') or self.user_has_groups('hr_attendance.group_hr_attendance_manager'):
          return []
      if self.user_has_groups('ubisol_hr_attendance_upgrade.group_hr_attendance_responsible'):
          return ['|', ('parent_id', '=', self.env.user.employee_id.id), ('user_id', '=', self.env.user.id)]
      return [('user_id', '=', self.env.user.id)]

  search_type = fields.Selection([
      ('department', 'Хэлтэс'),
      ('employee', 'Ажилтан')
  ], default="department", tracking=True)
  department_id = fields.Many2many('hr.department', string="Хэлтэс", help="Хэлтэс")
  employee_id = fields.Many2many('hr.employee', string="Ажилтан", help="Ажилтан")

  def create_attendance_filter(self):
    start_date = datetime.combine(self.start_date, time())
    end_date = datetime.combine(self.end_date, time())
    end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
    if self.search_type == 'department':
      if self.department_id:
        domain = [('check_in', '>=', start_date), ('check_in', '<=', end_date), ('department_id', '=', self.department_id.id)]
      else:
        domain = [('check_in', '>=', start_date), ('check_in', '<=', end_date)]
    else:
      if self.employee_id:
        domain = [('check_in', '>=', start_date), ('check_in', '<=', end_date), ('employee_id', '=', self.employee_id.id)]
      else:
        domain = [('check_in', '>=', start_date), ('check_in', '<=', end_date)]

    action = {
      "name": "Ирц",
      "type": "ir.actions.act_window",
      "res_model": "hr.attendance",
      'domain': domain,
      'context': {"search_default_today":1, "search_default_employee": 1, "search_default_department": 1},
      "view_mode": "tree,kanban,timeline,form",
    }

    return action
