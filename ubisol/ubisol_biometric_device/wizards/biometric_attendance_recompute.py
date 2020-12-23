# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class BiometricAttendanceRecompute(models.TransientModel):
    _name = 'biometric.attendance.wizard'
    _description = 'Biometric Attendance Wizard'

    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2many('hr.employee', string="Employee", help="Employee")

    def action_compute(self):
        log_obj = self.env["log_file_import_wizard"].search([])
        att_obj = self.env['hr.attendance']
        setting_obj = self.env['hr.attendance.settings'].search([], limit=1, order='id desc')
        shift_obj = self.env['hr.employee.shift']
        shift_type = self.env['resource.calendar'].search([('shift_type', '=', 'days')], limit=1, order='id asc')
        
        for emp in self.employee_id:
            general_shift = self.env['hr.employee.schedule'].search(
                [('day_period', '!=', 3), ('hr_employee', '=', int(emp.id))], limit=1, order='id asc')
            biometrics = self.env["biometric.attendance"].search([
                ('punch_date_time', '>=', self.start_date), 
                ('punch_date_time', '<=', self.end_date),
                ('pin_code', '=', emp.pin)
            ])
            # print(biometrics)
            for b in biometrics:
                atten_time = b.punch_date_time

                att = self.env['hr.attendance'].search([('employee_id', '=', emp.id), ('check_in', '=', atten_time)])
                if not att:
                    att = self.env['hr.attendance'].search([('employee_id', '=', emp.id), ('check_out', '=', atten_time)])
                    if not att:
                        [att_id, status] = log_obj.check_in_out(att_obj, emp, atten_time, setting_obj, general_shift, shift_obj, shift_type)
                        # print(atten_time, status, emp.pin, att_id)
                        if(status == 'check_out'):
                            if att_id != 0:
                                att_var = att_obj.browse(att_id)
                                att_var.write({'check_out': atten_time})
                            else:
                                att_var1 = att_obj.search(
                                    [('employee_id', '=', emp.id)],order="id desc")
                                if att_var1:
                                    att_var1[0].write({'check_out': atten_time})
                        elif (status == "update_check_out"):
                            att_var = att_obj.browse(att_id)
                            att_var.write({'check_out': atten_time})
                        elif (status == "update_check_in"):
                            att_var = att_obj.browse(att_id)
                            att_var.write({'check_in': atten_time})
                        elif status == "new_check_in":
                            att_var = att_obj.browse(att_id)
                            att_var.write({'check_in': atten_time})
                        elif status == "new_check_out":
                            att_obj.create({'employee_id': emp.id, 'check_out': atten_time})
                        elif status == "pass":
                            pass
                        else:
                            att_obj.create(
                                {'employee_id': emp.id, 'check_in': atten_time})
        
        action = {}
        return action
