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

        # if str(row[0]).strip() != '747':
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
            # print(atten_time, status)
            if(status == 'check_out'):
                att_var1 = att_obj.search(
                    [('employee_id', '=', get_user_id.id)],order="id desc")
                if att_var1:
                    att_var1[0].write({'check_out': atten_time})
            elif (status == "update_check_out"):
                att_var = att_obj.search(
                    [('employee_id', '=', get_user_id.id)],order="id desc")
                att_var[0].write({'check_out': atten_time})
            elif (status == "update_check_in"):
                # att_var = att_obj.search(
                #     [('employee_id', '=', get_user_id.id)],order="id desc")
                # att_var[0].write({'check_in': atten_time})
                pass
            elif status == "new_check_out":
                att_obj.create({'employee_id': get_user_id.id, 'check_out': atten_time})
            else:
                att_obj.create(
                    {'employee_id': get_user_id.id, 'check_in': atten_time})

        return {}

    def check_in_out(self, att_obj, get_user_id, dt):
        setting_obj = self.env['res.config.settings'].search([], limit=1, order='id desc')
        general_shift = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id))], limit=1, order='id desc')

        [ds1, ds2, de1, de2, dt1, s_type] = self._calculate_dates(setting_obj, general_shift, dt)
        attendance_req = self._is_overtime(get_user_id, dt, dt1)
        if attendance_req:
            [ds1, ds2, de1, de2, dt1, s_type] = self._calculate_dates(setting_obj, general_shift, attendance_req)

        shift_start = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('day_period', '!=', 3), ('start_work', '>=', ds1), ('start_work', '<=', ds2)])
        shift_end = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('day_period', '!=', 3), ('end_work', '>=', de1), ('end_work', '<=', de2)])

        if attendance_req:
            return "check_out"
        if s_type == 'shift' and not shift_end:
            shift_end = shift_start

        if(shift_end & shift_start):
            check_out = abs(dt - shift_end.end_work).total_seconds()
            check_in = abs(dt - shift_start.start_work).total_seconds()
            status = self._check_status(general_shift, get_user_id, dt, shift_start.start_work, shift_end.end_work, check_out, check_in)
            return status
        elif(shift_end):
            return "check_out"
        elif(shift_start):
            return "check_in"
        else:
            shift_obj = self.env['hr.employee.shift']
            shift_type = self.env['resource.calendar'].search([('shift_type', '=', 'days')], limit=1, order='id desc')
            [start_work, end_work] = self._create_schedule(get_user_id, dt1, shift_obj, shift_type)
            work_start = datetime.strptime(datetime.strftime(dt1, "%Y-%m-%d  00:00:00"), "%Y-%m-%d %H:%M:%S")
            work_end = datetime.strptime(datetime.strftime(dt1, "%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S")
            work_start = work_start - timedelta(hours=8) + timedelta(seconds=start_work * 3600)
            work_end = work_end - timedelta(hours=8) + timedelta(seconds=end_work * 3600)

            check_out = abs(dt - work_end).total_seconds()
            check_in = abs(dt - work_start).total_seconds()
            status = self._check_status(general_shift, get_user_id, dt, work_start, work_end, check_out, check_in)
            return status

    def _is_overtime(self, get_user_id, dt, dt1):
        ds = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        de = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        de = datetime.strptime(de, "%Y-%m-%d %H:%M:%S") + timedelta(hours=23, minutes=59, seconds=59)
        attendance_reqs = self.env['hr.attendance.request'].search([
            ('end_datetime', '>=', ds),
            ('end_datetime', '<=', de),
            ('employee_id', '=', get_user_id.id),
            ('request_type', '=', 'employee'),
        ])
        if attendance_reqs and attendance_reqs.end_datetime > dt:
            return attendance_reqs.start_datetime + timedelta(hours=8)
        else:
            return None

    def _calculate_dates(self, setting_obj, general_shift, dt):
        dt1 = dt + timedelta(hours=8)
        dt_diff = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        dt_diff = datetime.strptime(dt_diff, "%Y-%m-%d %H:%M:%S")
        s_type = 'days'
        if general_shift:
            if general_shift.shift_type == 'shift':
                s_type = 'shift'
            else:
                s_type = 'days'
        else:
            s_type = 'days'
            
        if s_type == 'days':
            if abs(dt1 - dt_diff).total_seconds() < setting_obj.start_work_date_from * 3600 and abs(dt1 - dt_diff).total_seconds() > 0:
                dt1 = dt1 - timedelta(days=1)
            ds1 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            ds2 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            de1 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            de2 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")

            ds1 = datetime.strptime(ds1, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8) + timedelta(seconds=setting_obj.start_work_date_from * 3600)
            ds2 = datetime.strptime(ds2, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8) + timedelta(seconds=setting_obj.start_work_date_to * 3600 + 59)
            de1 = datetime.strptime(de1, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8) + timedelta(seconds=setting_obj.end_work_date_from * 3600)
            de2 = datetime.strptime(de2, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8) + timedelta(days=1) + timedelta(seconds=setting_obj.end_work_date_to * 3600 + 59)
        else:
            ds1 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            ds2 = datetime.strftime(dt1, "%Y-%m-%d 23:59:59")
            de1 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            de2 = datetime.strftime(dt1, "%Y-%m-%d 23:59:59")

            ds1 = datetime.strptime(ds1, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
            ds2 = datetime.strptime(ds2, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
            de1 = datetime.strptime(de1, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)
            de2 = datetime.strptime(de2, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)
        return [ds1, ds2, de1, de2, dt1, s_type]

    def _check_status(self, general_shift, get_user_id, dt, work_start, work_end, check_out, check_in):
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
            update_check_in = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_in', '>=', work_start - timedelta(hours=3)), ('check_in', '<', dt)])
            if(update_check_in):
                return "update_check_in"
            return "check_in"

    def _create_schedule(self, emp_id, date, shift_obj, shift_type):
        d = datetime.strftime(date, "%Y-%m-%d")
        shift = self.env['hr.employee.shift'].search([('resource_calendar_ids', '=', shift_type.id)], limit=1, order='id desc')

        values = {}
        values['hr_department'] = False
        values['hr_employee'] = emp_id.id
        values['resource_calendar_ids'] = shift_type.id
        values['date_from'] = str(d)
        values['date_to'] = str(d)
        
        shift_obj._create_schedules(values, shift)

        res = self.env['resource.calendar.shift'].search([('shift_id', '=', shift_type.id)], limit=1, order='id desc')
        return [res.start_work, res.end_work]