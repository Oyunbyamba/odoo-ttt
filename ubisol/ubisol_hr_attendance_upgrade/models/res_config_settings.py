# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_attendance_use_pin = fields.Boolean(string='Employee PIN',
        implied_group="hr_attendance.group_hr_attendance_use_pin")
    late_subtrack = fields.Float(string='Be late from work', default='2')
    late_min = fields.Float(string='Be late from work', default='0.16666666666')
    start_work_date_from = fields.Float(string='Date from of Start Date', default='5')
    start_work_date_to = fields.Float(string='Date to of Start Date', default='14')
    end_work_date_from = fields.Float(string='Date from of End Date', default='14.01666666666')
    end_work_date_to = fields.Float(string='Date to of End Date', default='4.98333333333')

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        hr_attendance = self.env.ref('res.groups', False)
        hr_attendance and hr_attendance.write({
            'late_subtrack': self.late_subtrack,
            'late_min': self.late_min,
            'start_work_date_from': self.start_work_date_from,
            'start_work_date_to': self.start_work_date_to,
            'end_work_date_from': self.end_work_date_from,
            'end_work_date_to': self.end_work_date_to,
        })