# -*- coding: utf-8 -*-
{
    'name': "ubisol_hr_employee_upgrade",

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
    'depends': ['base', 'hr', 'hr_skills', 'ubisol_hr_holidays'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/ubisol_hr_employee_security.xml',
        'views/views.xml',
        'views/hr_department.xml',
        'report/report.xml',
        'report/employee_detail.xml',
        'report/bank_definition.xml',
        'report/salary_specification.xml',
        'report/print_employee_badge_inherit.xml',
        'report/employee_working_definition.xml',
        'wizards/create_bank_definition.xml',
        'wizards/print_employee_definition.xml',
        'wizards/quarantine_working_definition.xml',
        'wizards/hr_departure_views.xml',
        'views/hr_resume_views.xml',
        'views/hr_departure.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
