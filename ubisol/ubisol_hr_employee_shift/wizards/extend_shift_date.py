# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ExtendHrEmployeeShift(models.TransientModel):
    _name = 'hr.employee.shift.extend'
    _description = 'Extend employee shift'

    date_to = fields.Date(string="Дуусах хугацаа")

    def _prepare_schedule_values(self, shift, date_from, date_to):
        hr_department = [[6, False, [shift.hr_department.id]]]
        hr_employee = [[6, False, [shift.hr_employee.id]]]
        values = {
            'name': shift.name,
            'assign_type': shift.assign_type,
            'hr_department': hr_department,
            'hr_employee': hr_employee,
            'resource_calendar_ids': shift.resource_calendar_ids.id,
            'date_from': str(date_from),
            'date_to': str(date_to)
        }

        return values

    def action_extend_shift(self):
        shift_ids = self.env.context.get('active_ids', [])
        log_obj = self.env['hr.employee.shift'].search([])
        extend_date_to = self.date_to
        if len(shift_ids) > 0:
            for shift_id in shift_ids:
                shift = self.env['hr.employee.shift'].browse([shift_id])
                if shift.date_to < extend_date_to:
                    extend_date_from = datetime.strptime(str(shift.date_to), '%Y-%m-%d')
                    extend_date_from = extend_date_from.date()+relativedelta(days=1)

                    shift.date_to = extend_date_to

                    # values = self._prepare_schedule_values(shift, extend_date_from, extend_date_to)
                    # log_obj._create_schedules(values, shift)

        return {}
