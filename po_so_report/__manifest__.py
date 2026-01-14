{
    'name': 'PO/SO Report',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'author' : 'Ebitda Solutions',
    'website' : 'https://www.ebitdasolutions.com/',
    'summary': 'Generate PO/SO Reports based on Projects',
    'description': """
        This module allows you to generate Purchase Order and Sale Order reports
        based on project invoices and payments.
    """,
    'depends': [
        'base',
        'account',
        'sale',
        'purchase',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/po_so_template.xml',
        'wizard/eway_report_wizard.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}