# -*- coding: utf-8 -*-
{
    'name': "内装工程项目管理系统",

    'summary': """
        Interior Decoration Engineering Management System
        """,

    'description': """
        This performances the interior decoration engineering management
        for mass production.
    """,

    'author': "维声公司",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'data/idem_default_config.xml',
        'security/ir.model.access.csv',
        'views/idem_views_menus.xml',
        'views/templates.xml',
        'views/idem_engproduceorder',
        'views/idem_engtask',
        'views/idem_engpretask',
        'views/idem_engbom',
        'views/idem_engchangeplan',
        'views/idem_engplan',
        'views/idem_engproduceroute',
        'views/idem_engproject',
        'views/idem_engreport',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
