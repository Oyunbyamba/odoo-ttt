# -*- coding: utf-8 -*-
{
    'name': "ubisol_hr_attendance_upgrade",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "UBISOL.LLC",
    'website': "http://www.ubisol.mn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_attendance'],

    # always loaded
    'data': [
        'security/ubisol_hr_attendance_security.xml',
        'security/ir.model.access.csv',

        'views/views.xml',
        'views/hr_attendance_settings_views.xml',
        'wizards/my_attendance.xml',
        'wizards/create_attendance_filter.xml',
    ],
    'qweb': [
        "static/src/xml/call_wizard.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
