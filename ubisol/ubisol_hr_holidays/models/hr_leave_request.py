# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models


class UbisolHolidaysRequest(models.Model): 
    _inherit = 'hr.leave'
    _description = "Time Off"

    @api.depends('number_of_days')
    def _change_leave_type(self):
        if(self.number_of_days <= 3 and self.holiday_status_id.validation_type == 'both'):
            if(self.holiday_status_id.unpaid == True):
                self.holiday_status_id = 7
            else:
                self.holiday_status_id = 9
        elif(self.number_of_days > 3 and self.holiday_status_id.validation_type != 'both'):
            if(self.holiday_status_id.unpaid == True):
                self.holiday_status_id = 8
            else:
                self.holiday_status_id = 10
    
   
