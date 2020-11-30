# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class CreateDatetimeFilter(models.TransientModel):
    _name = 'create.datetime.filter'
    _description = 'Create Datetime Filter Wizard'

    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))

    search_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], default="department", tracking=True)
    department_id = fields.Many2many('hr.department', string="Хэлтэс", help="Хэлтэс")
    employee_id = fields.Many2many('hr.employee', string="Ажилтан", help="Ажилтан")

    def create_datetime_filter(self):
      if self.search_type == 'department':
        if self.department_id:
          domain = [('work_day', '>=', self.start_date), ('work_day', '<=', self.end_date), ('hr_department', '=', self.department_id.id)]
        else:
          domain = [('work_day', '>=', self.start_date), ('work_day', '<=', self.end_date)]
      else:
        if self.employee_id:
          domain = [('work_day', '>=', self.start_date), ('work_day', '<=', self.end_date), ('hr_employee', '=', self.employee_id.id)]
        else:
          domain = [('work_day', '>=', self.start_date), ('work_day', '<=', self.end_date)]

      print(domain)

      action = {
        "name": "Ажиллах график",
        "type": "ir.actions.act_window",
        "res_model": "hr.employee.schedule",
        'domain': domain,
        'context': {"search_default_is_rest":1},
        "view_mode": "timeline",
      }
      return action
