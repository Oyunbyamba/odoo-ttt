# -*- coding: utf-8 - *-
from odoo import http
import os
import base64
from zk import ZK, const
import json

from odoo.modules.module import get_module_resource


class UbisolBiometricDevice(http.Controller):
    @http.route('/ubisol_biometric_device/ubisol_biometric_device/', auth='public')
    def index(self, **kw):

        # image insert from uploaded folder

        # image_dir = os.path.join(os.path.dirname(
        #     os.path.abspath(__file__)))+'/image'

        # for root, dirs, filenames in os.walk(image_dir):
        #     for f in filenames:
        #         print(f)
        #         pin_code = int(f.split('.')[0])
        #         get_user_id = http.request.env['hr.employee'].search(
        #             [('pin', '=', str(pin_code).strip())])

        #         if not get_user_id:
        #             continue
        #         else:
        #             get_user_id[0].write({
        #                 'image_1920': base64.encodestring(open(os.path.join(root, f), 'rb').read())})

        # conn = None
        # zk = ZK('192.168.0.119', port=4370, timeout=5)
        # try:
        #     print("Connecting to device ...")
        #     conn = zk.connect()
        #     print('Disabling device ...')
        #     conn.disable_device()
        #     print('Firmware Version: : {}'.format(conn.get_firmware_version()))
        #     # print '--- Get User ---'
        #     users = conn.get_users()
        #     attendances = conn.get_attendance()
        #     for attendance in attendances:
        #         print(attendance.__dir__())

        #     for user in users:
        #         privilege = 'User'
        #         if user.privilege == const.USER_ADMIN:
        #             privilege = 'Admin'

        #         print('- UID #{}'.format(user.uid))
        #         print('  Name       : {}'.format(user.name))
        #         print('  Privilege  : {}'.format(privilege))
        #         print('  Password   : {}'.format(user.password))
        #         print('  Group ID   : {}'.format(user.group_id))
        #         print('  User  ID   : {}'.format(user.user_id))

        #         # template = conn.get_user_template(
        #         #     uid=user.uid, user_id=user.user_id, temp_id=6)
        #         # print("Size     : %s" % template.size)
        #         # print("UID      : %s" % template.uid)
        #         # print("FID      : %s" % template.fid)
        #         # print("Valid    : %s" % template.valid)
        #         # print("Template : %s" % template.json_pack())
        #         # print("Mark     : %s" % template.mark)

        #     fingers = conn.get_templates()
        #     for finger in fingers:
        #         print("Size     : %s" % finger.size)
        #         print("UID      : %s" % finger.uid)
        #         print("FID      : %s" % finger.fid)
        #         print("Valid    : %s" % finger.valid)
        #         print("Template : %s" % finger.json_pack())
        #         print("Mark     : %s" % finger.mark)

        #     # conn.test_voice()
        #     print('Enabling device ...')
        #     conn.enable_device()
        # except Exception as e:
        #     print("Process terminate : {}".format(e))
        # finally:
        #     if conn:
        #         conn.disconnect()
        return "Hello, world"

    # @http.route('/ubisol_biometric_device/ubisol_biometric_device/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('ubisol_biometric_device.listing', {
    #         'root': '/ubisol_biometric_device/ubisol_biometric_device',
    #         'objects': http.request.env['ubisol_biometric_device.ubisol_biometric_device'].search([]),
    #     })

    # @http.route('/ubisol_biometric_device/ubisol_biometric_device/objects/<model("ubisol_biometric_device.ubisol_biometric_device"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('ubisol_biometric_device.object', {
    #         'object': obj
    #     })
