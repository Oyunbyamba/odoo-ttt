# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class HrAttendanceSettings(models.TransientModel):
    _name = 'hr.attendance.settings'

    late_subtrack = fields.Float(string='Be late from work', default='2')
    late_min = fields.Float(string='Be late from work', default='0.16666666666')
    start_work_date_from = fields.Float(string='Date from of Start Date', default='5')
    start_work_date_to = fields.Float(string='Date to of Start Date', default='14')
    end_work_date_from = fields.Float(string='Date from of End Date', default='14.01666666666')
    end_work_date_to = fields.Float(string='Date to of End Date', default='4.98333333333')