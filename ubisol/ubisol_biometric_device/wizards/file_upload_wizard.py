# -*- coding: utf-8 -*-
from odoo import models, fields, api
import csv
import base64
import pytz
import sys
from datetime import datetime, timedelta
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

        device_id = self.env.context.get('active_ids')

        atten_time = row[1]
        atten_time = datetime.strptime(atten_time, '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(self.env.user.tz or 'GMT')
        local_dt = local_tz.localize(atten_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
        att_obj = self.env['hr.attendance']

        # if str(row[0]).strip() != '70':
        #     return {}

        get_user_id = self.env['hr.employee'].search(
            [('pin', '=', str(row[0]).strip())])

        if not get_user_id:
            record = self.env['hr.employee'].create({'name': str(row[0]).strip(), 'pin': str(row[0]).strip()})
            get_user_id = record

        duplicate_atten_ids = self.env['biometric.attendance'].search(
            [('pin_code', '=', str(row[0]).strip()),  ('punch_date_time', '=', atten_time)])
        if duplicate_atten_ids:
            return {}
        else:
            self.env['biometric.attendance'].create({'device_id': device_id[0],
                                                     'pin_code': str(row[0]).strip(),
                                                     'punch_date_time': atten_time,
                                                     'attendance_data': str(row[2]),
                                                     'attendance_data1': str(row[3]),
                                                     'attendance_data2': str(row[4]),
                                                     'attendance_data3': str(row[5])})

        # Herev hereglegch oldson bol
        if get_user_id:
            status = self.check_in_out(att_obj, get_user_id, atten_time)
            print(atten_time, status)
            if(status == 'check_out'):
                att_var1 = att_obj.search(
                    [('employee_id', '=', get_user_id.id)],order="id desc")
                if att_var1:
                    att_var1[0].write({'check_out': atten_time})
            elif (status == "update_check_out"):
                att_var = att_obj.search(
                    [('employee_id', '=', get_user_id.id)],order="id desc")
                att_var[0].write({'check_out': atten_time})
            elif status == "new_check_out":
                att_obj.create({'employee_id': get_user_id.id, 'check_out': atten_time})
            else:
                att_obj.create(
                    {'employee_id': get_user_id.id, 'check_in': atten_time})

        return {}

    def check_in_out(self, att_obj, get_user_id, dt):
        dt1 = dt + timedelta(hours=8)
        dt_diff = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        dt_diff = datetime.strptime(dt_diff, "%Y-%m-%d %H:%M:%S")
        if abs(dt1 - dt_diff).total_seconds() < 5 * 3600 and abs(dt1 - dt_diff).total_seconds() > 0:
            dt1 = dt1 - timedelta(days=1)
        ds1 = datetime.strftime(dt1, "%Y-%m-%d 05:00:00")
        ds2 = datetime.strftime(dt1, "%Y-%m-%d 14:00:00")
        de1 = datetime.strftime(dt1, "%Y-%m-%d 14:00:01")
        de2 = datetime.strftime(dt1, "%Y-%m-%d 04:59:59")

        ds1 = datetime.strptime(ds1, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
        ds2 = datetime.strptime(ds2, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
        de1 = datetime.strptime(de1, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)
        de2 = datetime.strptime(de2, "%Y-%m-%d %H:%M:%S") + timedelta(days=1) - timedelta(hours=8)

        shift_start = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('start_work', '>=', ds1), ('start_work', '<=', ds2)])
        shift_end = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('end_work', '>=', de1), ('end_work', '<=', de2)])
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
            work_start = datetime.strptime(
                datetime.strftime(dt1, "%Y-%m-%d  00:30:00"), "%Y-%m-%d %H:%M:%S")
            work_end = datetime.strptime(datetime.strftime(
                dt1, "%Y-%m-%d 09:30:00"), "%Y-%m-%d %H:%M:%S")

            check_out = abs(dt - work_end).total_seconds()
            check_in = abs(dt - work_start).total_seconds()

            if(check_out < check_in):
                days = 0
                self._cr.execute('select id from hr_attendance where employee_id = '+str(get_user_id.id)+' order by id desc limit 1')
                last_id = self._cr.fetchone()

                if last_id:
                    new_check_out = self.env['hr.attendance'].search([('id', '=', last_id[0])])
                    if new_check_out and new_check_out.check_in:
                        seconds = abs(dt - new_check_out.check_in).total_seconds()
                        days = seconds / (24* 3600)
                else:
                    new_check_out = None

                update_check_out = self.env['hr.attendance'].search(
                    [('employee_id', '=', get_user_id.id), ('check_out', '>=', work_start), ('check_out', '<', dt)])

                if(update_check_out):
                    return "update_check_out"
                elif new_check_out:
                    if not new_check_out.check_in:
                        return "new_check_out"
                    elif days >= 1:
                        return "new_check_out"
                    else:
                        return "check_out"
                elif not last_id:
                    return "new_check_out"
                return "check_out"
            else:
                update_check_out = self.env['hr.attendance'].search(
                    [('employee_id', '=', get_user_id.id), ('check_in', '>=', work_start), ('check_out', '<', dt)])
                if(update_check_out):
                    return "update_check_in"
                return "check_in"

            # att_var = att_obj.search(
            #     [('employee_id', '=', get_user_id.id), ('check_out', '=', False)])
            # if not att_var:
            #     return "check_in"
            # elif len(att_var) == 1:
            #     print("1 oldson")
            #     return "update"
            # else:
            #     return "check_out"
