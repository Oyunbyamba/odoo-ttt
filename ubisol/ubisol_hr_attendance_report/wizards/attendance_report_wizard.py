# -*- coding: utf-8 -*-

from odoo import models, fields


class AttendanceReport(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Attendance Report Wizard'

    start_date = fields.Date(string="Эхлэх хугацаа")
    end_date = fields.Date(string="Дуусах хугацаа")

    def action_compute(self):
        reports = self.env["hr.attendance.report"].search([])
        reports.calculate_report(self.start_date, self.end_date)
        
        action = {
          "name": "Ирцийн график",
          "type": "ir.actions.act_window",
          "res_model": "hr.attendance.report",
          "view_mode": "pivot",
        }
        return action
