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
    'depends': ['base', 'hr', 'hr_skills'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/report.xml',
        'report/bank_definition.xml',
        'report/salary_specification.xml',
        'wizards/create_bank_definition.xml',
        'views/hr_resume_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
