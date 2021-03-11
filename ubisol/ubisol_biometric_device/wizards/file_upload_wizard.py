# -*- coding: utf-8 -*-
from odoo import models, fields, api
import csv
import base64
import pytz
import sys
from datetime import datetime, timedelta
import logging
import binascii

_logger = logging.getLogger(__name__)


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
        _logger.info('device_id')
        _logger.info(device_id)

        atten_time = row[1]
        atten_time = datetime.strptime(atten_time, '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(self.env.user.tz or 'GMT')
        local_dt = local_tz.localize(atten_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")

        if str(row[0]).strip() == '9999':
            return {}

        get_user_id = self.env['hr.employee'].search(
            [('pin', '=', str(row[0]).strip())])

        # ene code iig tur comment hiiv.
        if not get_user_id:
            # record = self.env['hr.employee'].create({'name': str(row[0]).strip(), 'pin': str(row[0]).strip()})
            # get_user_id = record
            pass

        duplicate_atten_ids = self.env['biometric.attendance'].search(
            [('pin_code', '=', str(row[0]).strip()),  ('punch_date_time', '=', atten_time)])
        if duplicate_atten_ids:
            return {}
        else:
            biometric = self.env['biometric.attendance'].create({'device_id': device_id[0],
                                                                 'pin_code': str(row[0]).strip(),
                                                                 'punch_date_time': atten_time,
                                                                 'attendance_data': str(row[2]),
                                                                 'attendance_data1': str(row[3]),
                                                                 'attendance_data2': str(row[4]),
                                                                 'attendance_data3': str(row[5])})

        prev_date = self.checking_prev_att_within_thirty_sec(
            get_user_id, atten_time)
        if not prev_date:
            return {}

        self.write_to_attendance(get_user_id, atten_time)

        return {}

    def checking_prev_att_within_thirty_sec(self, get_user_id, atten_time):
        prev_user = self.env['ir.config_parameter'].sudo(
        ).get_param('my.global.prev_user')
        prev_date = self.env['ir.config_parameter'].sudo(
        ).get_param('my.global.prev_date')

        if get_user_id:
            if not prev_user and not prev_date:
                prev_user = get_user_id.id
                prev_date = atten_time
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_user', prev_user)
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_date', prev_date)
            if int(prev_user) == int(get_user_id.id):
                if type(prev_date) is str:
                    prev_date = datetime.strptime(
                        prev_date, '%Y-%m-%d %H:%M:%S')
                if prev_date != atten_time:
                    diff = (atten_time - prev_date).total_seconds()
                    if abs(diff) <= 30:
                        return {}
                    else:
                        prev_user = get_user_id.id
                        prev_date = atten_time
                        self.env['ir.config_parameter'].sudo().set_param(
                            'my.global.prev_user', prev_user)
                        self.env['ir.config_parameter'].sudo().set_param(
                            'my.global.prev_date', prev_date)
                else:
                    prev_user = get_user_id.id
                    prev_date = atten_time
                    self.env['ir.config_parameter'].sudo().set_param(
                        'my.global.prev_user', prev_user)
                    self.env['ir.config_parameter'].sudo().set_param(
                        'my.global.prev_date', prev_date)
            elif prev_user != get_user_id.id:
                prev_user = get_user_id.id
                prev_date = atten_time
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_user', prev_user)
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_date', prev_date)
            return prev_date
        else:
            return {}

    def write_to_attendance(self, get_user_id, atten_time):
        att_obj = self.env['hr.attendance']

        # Herev hereglegch oldson bol
        if get_user_id:
            setting_obj = self.env['hr.attendance.settings'].search(
                [], limit=1, order='id desc')
            # ajiltan bolgonoor udur buriin ajillah huwaari orson table
            general_shift = self.env['hr.employee.schedule'].search(
                [('day_period', '!=', 3), ('hr_employee', '=', int(get_user_id.id))], limit=1, order='id asc')
            # tuhain ajiltan or helteseer uusgesen shiftuudiin 1 mor table
            shift_obj = self.env['hr.employee.shift']
            # tuhain ajillah huwaariudiin master table
            shift_type = self.env['resource.calendar'].search(
                [('shift_type', '=', 'days')], limit=1, order='id asc')

            if general_shift:
                [att_id, status] = self.check_in_out(
                    att_obj, get_user_id, atten_time, setting_obj, general_shift, shift_obj, shift_type)

                if(status == 'check_out'):
                    if att_id != 0:
                        att_var = att_obj.browse(att_id)
                        att_var.write({'check_out': atten_time})
                    else:
                        att_var1 = att_obj.search(
                            [('employee_id', '=', get_user_id.id)], order="id desc")
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
                    att_obj.create(
                        {'employee_id': get_user_id.id, 'check_out': atten_time})
                elif status == "pass":
                    return {}
                else:
                    att_obj.create(
                        {'employee_id': get_user_id.id, 'check_in': atten_time})

        return {}

    def check_in_out(self, att_obj, get_user_id, dt, setting_obj, general_shift, shift_obj, shift_type):
        [ds1, ds2, de1, de2, dt1, s_type] = self._calculate_dates(
            get_user_id, setting_obj, general_shift, dt)

        week_index = self._find_week_day_index(dt1.strftime("%A"))
        calendar_leaves = self.env['resource.calendar.leaves'].search(
            [('date_from', '<=', dt), ('date_to', '>=', dt)])
        # herev shift ni office tsagaar bgaad hagas buten saind irsen bol
        if (week_index >= 5 and general_shift.shift_type == 'days') or (calendar_leaves and general_shift.shift_type == 'days'):
            end = datetime.strptime(datetime.strftime(
                dt1, "%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S")
            end = end + \
                timedelta(seconds=setting_obj.start_work_date_from * 3600)
            if end < dt1:
                [att_id, status] = self._check_status_holiday(
                    setting_obj, get_user_id, dt)
                return [att_id, status]

        attendance_req = self._is_overtime(get_user_id, dt, dt1)
        if attendance_req:
            [ds1, ds2, de1, de2, dt1, s_type] = self._calculate_dates(
                get_user_id, setting_obj, general_shift, attendance_req)

        # ajiltanii ajil ehleh tsag - ajillah huwaarias
        shift_start = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('day_period', '!=', 3), ('start_work', '>=', ds1), ('start_work', '<=', ds2)], limit=1, order='id desc')
        # ajiltanii ajil duusah tsag - ajillah huwaarias
        shift_end = self.env['hr.employee.schedule'].search(
            [('hr_employee', '=', int(get_user_id.id)), ('day_period', '!=', 3), ('end_work', '>=', de1), ('end_work', '<=', de2)], limit=1, order='id desc')

        if(shift_end & shift_start):
            check_out = abs(dt - shift_end.end_work).total_seconds()
            check_in = abs(dt - shift_start.start_work).total_seconds()

            [att_id, status] = self._check_status(
                get_user_id, dt, shift_start.start_work, check_out, check_in, ds1, ds2, de1, de2)
            return [att_id, status]
        elif(shift_end):
            return [0, "check_out"]
        elif(shift_start):
            return [0, "check_in"]
        else:
            # amraltiin udur bish shift bhgui bol daraahaar tootsoolol hiih
            [start_work, end_work] = self._create_schedule(
                get_user_id, dt1, shift_obj, shift_type)
            work_start = datetime.strptime(datetime.strftime(
                dt1, "%Y-%m-%d  00:00:00"), "%Y-%m-%d %H:%M:%S")

            work_end = datetime.strptime(datetime.strftime(
                dt1, "%Y-%m-%d 00:00:00"), "%Y-%m-%d %H:%M:%S")

            work_start = work_start - \
                timedelta(hours=8) + timedelta(seconds=start_work * 3600)

            work_end = work_end - \
                timedelta(hours=8) + timedelta(seconds=end_work * 3600)

            check_out = abs(dt - work_end).total_seconds()
            check_in = abs(dt - work_start).total_seconds()

            [att_id, status] = self._check_status(
                get_user_id, dt, work_start, check_out, check_in, ds1, ds2, de1, de2)

            return [att_id, status]

    def _find_week_day_index(self, week_day):
        week = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        return week.get(week_day, -1)

    def _is_overtime(self, get_user_id, dt, dt1):
        ds = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        de = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        de = datetime.strptime(de, "%Y-%m-%d %H:%M:%S") + \
            timedelta(hours=23, minutes=59, seconds=59)
        # attendance_reqs = self.env['hr.attendance.request'].search([
        #     ('end_datetime', '>=', ds),
        #     ('end_datetime', '<=', de),
        #     ('employee_id', '=', get_user_id.id),
        #     ('request_type', '=', 'employee'),
        # ])

        attendance_reqs = self.env['hr.leave'].search([
            ('date_from', '>=', ds),
            ('date_to', '<=', de),
            ('employee_id', '=', get_user_id.id),
            ('holiday_type', '=', 'employee'),
        ])
        if attendance_reqs and attendance_reqs.end_datetime > dt:
            return attendance_reqs.start_datetime + timedelta(hours=8)
        else:
            return None

    def _calculate_dates(self, get_user_id, setting_obj, general_shift, dt):
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

            ds1 = datetime.strptime(ds1, '%Y-%m-%d %H:%M:%S') - timedelta(
                hours=8) + timedelta(seconds=setting_obj.start_work_date_from * 3600)
            ds2 = datetime.strptime(ds2, '%Y-%m-%d %H:%M:%S') - timedelta(
                hours=8) + timedelta(seconds=setting_obj.start_work_date_to * 3600 + 59)
            de1 = datetime.strptime(de1, "%Y-%m-%d %H:%M:%S") - timedelta(
                hours=8) + timedelta(seconds=setting_obj.end_work_date_from * 3600)
            de2 = datetime.strptime(de2, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8) + timedelta(
                days=1) + timedelta(seconds=setting_obj.end_work_date_to * 3600 + 59)
        else:
            ds1 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            ds2 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            de1 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
            de2 = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")

            days = 0

            dt2 = dt1.date()
            schedule = self.env['hr.employee.schedule'].search([
                ('hr_employee', '=', int(get_user_id.id)),
                ('work_day', '=', dt2)], limit=1, order='id desc')
            if schedule:
                if schedule.day_period_int == 3:
                    dt2 = dt1 - timedelta(days=1)
                    schedule = self.env['hr.employee.schedule'].search([
                        ('hr_employee', '=', int(get_user_id.id)),
                        ('work_day', '=', dt2.date())], limit=1, order='id desc')
                    if schedule.day_period_int != 3:
                        days = 1
                s_work = schedule.start_work.time()
                s_work = s_work.hour + s_work.minute/60.0
                e_work = schedule.end_work.time()
                e_work = e_work.hour + e_work.minute/60.0
            else:
                s_work = 0.0
                e_work = 9.0
            if schedule and s_work >= e_work:
                ds1 = datetime.strptime(
                    ds1, '%Y-%m-%d %H:%M:%S') - timedelta(hours=6) + timedelta(seconds=s_work * 3600)
                ds2 = datetime.strptime(
                    ds2, '%Y-%m-%d %H:%M:%S') + timedelta(hours=6) + timedelta(seconds=s_work * 3600 - 1)
                de1 = datetime.strptime(de1, "%Y-%m-%d %H:%M:%S") - timedelta(
                    hours=6) + timedelta(seconds=e_work * 3600) + timedelta(days=1)
                de2 = datetime.strptime(de2, "%Y-%m-%d %H:%M:%S") + timedelta(
                    hours=6) + timedelta(seconds=e_work * 3600 - 1) + timedelta(days=1)
            elif schedule:
                ds1 = datetime.strptime(
                    ds1, '%Y-%m-%d %H:%M:%S') - timedelta(hours=6) + timedelta(seconds=s_work * 3600)
                ds2 = datetime.strptime(
                    ds2, '%Y-%m-%d %H:%M:%S') + timedelta(hours=6) + timedelta(seconds=s_work * 3600 - 1)
                de1 = datetime.strptime(
                    de1, "%Y-%m-%d %H:%M:%S") - timedelta(hours=6) + timedelta(seconds=e_work * 3600)
                de2 = datetime.strptime(
                    de2, "%Y-%m-%d %H:%M:%S") + timedelta(hours=6) + timedelta(seconds=e_work * 3600 - 1)
            else:
                ds1 = datetime.strptime(
                    ds1, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8) + timedelta(seconds=s_work * 3600)
                ds2 = datetime.strptime(
                    ds2, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8) + timedelta(seconds=s_work * 3600 + 59)
                de1 = datetime.strptime(
                    de1, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8) + timedelta(seconds=e_work * 3600)
                de2 = datetime.strptime(
                    de2, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8) + timedelta(seconds=e_work * 3600 + 59)
            ds1 = ds1 - timedelta(days=days)
            ds2 = ds2 - timedelta(days=days)
            de1 = de1 - timedelta(days=days)
            de2 = de2 - timedelta(days=days)
        return [ds1, ds2, de1, de2, dt1, s_type]

    def _check_status(self, get_user_id, dt, work_start, check_out, check_in, ds1, ds2, de1, de2):
        if(check_out < check_in):
            days = 0
            self._cr.execute('select id from hr_attendance where employee_id = ' +
                             str(get_user_id.id)+' order by id desc limit 1')
            last_id = self._cr.fetchone()

            if last_id:
                new_check_out = self.env['hr.attendance'].search(
                    [('id', '=', last_id[0])])
                if new_check_out and new_check_out.check_in:
                    seconds = abs(dt - new_check_out.check_in).total_seconds()
                    days = seconds / (24 * 3600)
                    if days >= 1:
                        new_check_out = None
                elif new_check_out and new_check_out.check_out and dt > new_check_out.check_out:
                    seconds = abs(dt - new_check_out.check_out).total_seconds()
                    days = seconds / (24 * 3600)
                    if days >= 1:
                        new_check_out = None
            else:
                new_check_out = None

            # update_check_out = self.env['hr.attendance'].search(
            #     [('employee_id', '=', get_user_id.id), ('check_out', '>=', work_start), ('check_out', '<', dt)])
            update_check_out = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_out', '>=', work_start), ('check_out', '<', de2)], limit=1, order='check_out desc')

            check_out = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_in', '>=', ds1), ('check_in', '<=', ds2)])

            if update_check_out:
                if update_check_out.check_out < dt:
                    return [update_check_out.id, "update_check_out"]
                else:
                    return [0, "pass"]
            elif check_out:
                return [check_out.id, "check_out"]
            elif new_check_out:
                if new_check_out.check_out and new_check_out.check_out > dt:
                    return [new_check_out.id, "update_check_out"]
                elif new_check_out.check_out and new_check_out.check_out <= dt:
                    return [0, "pass"]
                if not new_check_out.check_in:
                    return [new_check_out.id, "new_check_out"]
                else:
                    return [check_out.id, "check_out"]
            return [0, "new_check_out"]
        else:
            update_check_in = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_in', '>=', ds1), ('check_in', '<=', ds2)], limit=1, order='check_in asc')
            new_check_in = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_out', '>=', de1), ('check_out', '<=', de2)], limit=1, order='check_out desc')

            if update_check_in:
                if update_check_in.check_in > dt:
                    return [update_check_in.id, "update_check_in"]
                else:
                    return [0, "pass"]
            elif new_check_in:
                if new_check_in.check_in and new_check_in.check_in < dt:
                    return [new_check_in.id, "update_check_in"]
                elif new_check_in.check_in and new_check_in.check_in >= dt:
                    return [0, "pass"]
                return [new_check_in.id, "new_check_in"]
            return [0, "check_in"]

    def _get_attendance(self, get_user_id, check_in, check_out, date1, date2):
        if not check_in:
            att = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_out', '>=', date1), ('check_out', '<', date1)])
        else:
            att = self.env['hr.attendance'].search(
                [('employee_id', '=', get_user_id.id), ('check_in', '>=', date1), ('check_in', '<', date1)])
        return att

    def _check_status_holiday(self, setting_obj, get_user_id, dt):
        dt1 = dt + timedelta(hours=8)
        work_start = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        work_start = datetime.strptime(work_start, '%Y-%m-%d %H:%M:%S')
        work_start = work_start - \
            timedelta(hours=8) + \
            timedelta(seconds=setting_obj.start_work_date_from * 3600)
        work_start_end = datetime.strftime(dt1, "%Y-%m-%d 00:00:00")
        work_start_end = datetime.strptime(work_start_end, '%Y-%m-%d %H:%M:%S') - timedelta(
            hours=8) + timedelta(seconds=setting_obj.start_work_date_to * 3600 + 59)

        att = self.env['hr.attendance'].search(
            [('employee_id', '=', get_user_id.id), ('check_in', '>=', work_start), ('check_in', '<', dt)], limit=1, order='create_date desc')
        if att:
            if att.check_out:
                return [att.id, "update_check_out"]
            else:
                return [att.id, "check_out"]
        else:

            if work_start_end < dt:
                return [0, "new_check_out"]
            else:
                return [0, "check_in"]

    def _create_schedule(self, emp_id, date, shift_obj, shift_type):
        d = datetime.strftime(date, "%Y-%m-%d")
        # shift = self.env['hr.employee.shift'].search([('resource_calendar_ids', '=', shift_type.id)], limit=1, order='id desc')

        values = {}
        values['type'] = 'employee'
        if emp_id.department_id:
            values['hr_department'] = emp_id.department_id.id
            values['hr_employee'] = emp_id.id
        else:
            values['hr_department'] = False
            values['hr_employee'] = emp_id.id
        values['resource_calendar_ids'] = shift_type.id
        values['date_from'] = str(d)
        values['date_to'] = str(d)

        # shift_obj._create_schedules(values, shift)

        res = self.env['resource.calendar.shift'].search(
            [('shift_id', '=', shift_type.id)], limit=1, order='id asc')
        # return [res.start_work, res.end_work]
        return [8, 17]
