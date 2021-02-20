# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models


class UbisolHolidaysType(models.Model):
    _inherit = 'hr.leave.type' 
    _description = "Leave type"
   
    request_status_type = fields.Selection([
        ('paid', 'Цалинтай'),
        ('unpaid', 'Цалингүй'),
        ('sick', 'Өвчтэй'),
        ('vacation', 'Ээлжийн амралт'),
        ('overtime', 'Илүү цаг'),
        ('attendance', 'Ирц нөхөлт'),
        ('outside_work', 'Гадуур ажил'),
        ('long_leave', 'Уртын чөлөө'),
        ('responsible_watchman', 'Хариуцлагатай жижүүр'),
        ], string='Чөлөөний төрөл', required=True)
    one_step_days = fields.Integer('1 шатлалт чөлөөнд тооцох хоног', default=3)
    overtime_type = fields.Selection([
        ('basic_overtime_request', 'Илүү цагийн хүсэлт'),
        ('total_allowed_overtime', 'Тушаалаар хязгаарлагдах илүү цаг'),
        ('manager_proved_overtime', 'Хүсэлтээр баталгаажсан илүү цаг')
        ], default='basic_overtime_request', string='Илүү цагийн төрөл', required=True)    


