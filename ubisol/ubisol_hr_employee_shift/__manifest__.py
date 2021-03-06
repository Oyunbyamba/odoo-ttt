# -*- coding: utf-8 -*-
{
    'name': "ubisol_hr_employee_shift",

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
    'installable': True,
    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'ubisol_hr_employee_upgrade', 'resource'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/schedule_view.xml',
        'views/workplan_view.xml',
        'wizards/create_datetime_filter.xml',
        'wizards/extend_shift_date.xml',
    ],
    'qweb': [
        "static/src/xml/datetime_filter.xml",
        "static/src/xml/call_wizard.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
