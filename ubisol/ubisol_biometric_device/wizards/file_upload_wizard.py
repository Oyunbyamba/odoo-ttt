# -*- coding: utf-8 -*-
from odoo import models, fields, api
import csv
import base64
import pytz
import sys
from datetime import datetime
import logging
import binascii


class LogFileImportWizard(models.TransientModel):
    _name = 'log_file_import_wizard'
    # your file will be stored here:
    dat_file = fields.Binary(string='.dat файл', required=True)

    def import_dat(self):

        device_id = self.env.context.get('active_ids')
        # reader = csv.DictReader(f.split('\n'), delimiter='\t')
        reader = csv.reader(base64.b64decode(
            self.dat_file).decode('utf-8').split('\n'), delimiter='\t')
        for row in reader:
            if(len(row) > 0):
                self.import_attendance(row)

        return {}

    def import_attendance(self, row):

        atten_time = row[1]
        atten_time = datetime.strptime(
            atten_time, '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(
            self.env.user.partner_id.tz or 'GMT')
        local_dt = local_tz.localize(atten_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        atten_time = datetime.strptime(
            utc_dt, "%Y-%m-%d %H:%M:%S")
        att_obj = self.env['hr.attendance']

        get_user_id = self.env['hr.employee'].search(
            [('pin', '=', str(row[0]).strip())])
        if get_user_id:
            duplicate_atten_ids = self.env['hr.attendance'].search(
                [('employee_id', '=', str(get_user_id.id)),  ('check_in', '=', atten_time)])
            if duplicate_atten_ids:
                return {}
            else:
                status = self.check_in_out(get_user_id, atten_time)
                print(atten_time)
                if(status == 'check_out'):
                    att_obj.create(
                        {'employee_id': get_user_id.id, 'check_out': atten_time})
                else:
                    att_obj.create(
                        {'employee_id': get_user_id.id, 'check_in': atten_time})

        return {}

    def check_in_out(self, get_user_id, dt):

        d1 = datetime.strftime(dt, "%Y-%m-%d 00:00:00")
        d2 = datetime.strftime(dt, "%Y-%m-%d 23:59:59")
        shift_start = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('start_work', '>=', d1), ('start_work', '<=', d2)])
        shift_end = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('end_work', '>=', d1), ('end_work', '<=', d2)])
        if(shift_end & shift_start):
            check_out = abs(dt - shift_end.end_work).total_seconds()
            check_in = abs(dt - shift_start.start_work).total_seconds()
            if(check_out < check_in):
                return "check_out"
            else:
                return "check_in"
        elif(shift_end):
            return "check_out"
        elif(shift_start):
            return "check_in"
        else:
            att_var = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_out', '=', False)])
            if not att_var:
                return "check_in"
            else:
                return "check_out"
