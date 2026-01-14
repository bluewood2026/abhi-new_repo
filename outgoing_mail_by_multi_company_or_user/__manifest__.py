# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
{
    'name': 'Outgoing Mail by Multi Company or User',
    'version': '19.0.0.0',
    'category': 'Mail',
    'author': 'Techultra Solutions Private Limited',
    'website': "https://www.techultrasolutions.com/",
    'summary': """Send outgoing emails using the correct mail server based on company or user setup.
    tus
    techultra
    techultra_private_limited_solution
    mail,
    multi company
    email
    user
    sender
    routing
    outgoing mail server
    multi company email
    odoo email routing
    email server by user
    email server by company
    company based mail server
    user based mail server
    outgoing email configuration
    smart email routing
    odoo
    odoo16
    odoo17
    odoo18
    odoo mail server module
    multi company mail setup
    per user smtp
    per company smtp
    email identity control
    odoo multi email account
    email sender rules odoo
    configure smtp in odoo
    dynamic email routing
    odoo multiple mail servers
    separate mail server per company
    outgoing mail
    smtp
    multi company
    odoo mail server
    email routing
    user based email
    mail config
    mail server selection
    odoo smtp
    email management
    odoo outgoing mail by user
    odoo outgoing mail per company
    email server rules odoo
    per user smtp in odoo
    multi domain email odoo
    per company smtp server odoo
    company wise smtp setup
    odoo email routing module
    odoo send mail from user email
    smart mail server switch odoo
    how to use different smtp servers for different users in odoo
    odoo send email from different companies
    set outgoing mail server per user in odoo
    odoo email configuration multi company
    outgoing mail server per user or company odoo
    smart mail server selection in odoo

    """,
    'description': """ 
        Outgoing Mail by Multi Company or User
        ======================================

        This module allows you to select the correct outgoing mail server in multi-company or multi-user environments.

        Each outgoing mail server configuration must be linked to **either a company or a user, but not both**. 
        This prevents ambiguity in email routing and ensures that emails are sent using the correct identity.

        Key Features:
        -------------
        - Automatically selects outgoing mail server based on current user or company
        - Supports multi-company setups
        - Avoids duplicate or conflicting mail server use
        - Enforces validation: only one (company or user) allowed per config

    tus
    techultra
    techultra_private_limited_solution
    mail,
    multi company
    email
    user
    sender
    routing
    outgoing mail server
    multi company email
    odoo email routing
    email server by user
    email server by company
    company based mail server
    user based mail server
    outgoing email configuration
    smart email routing
    odoo
    odoo16
    odoo17
    odoo18
    odoo mail server module
    multi company mail setup
    per user smtp
    per company smtp
    email identity control
    odoo multi email account
    email sender rules odoo
    configure smtp in odoo
    dynamic email routing
    odoo multiple mail servers
    separate mail server per company
    outgoing mail
    smtp
    multi company
    odoo mail server
    email routing
    user based email
    mail config
    mail server selection
    odoo smtp
    email management
    odoo outgoing mail by user
    odoo outgoing mail per company
    email server rules odoo
    per user smtp in odoo
    multi domain email odoo
    per company smtp server odoo
    company wise smtp setup
    odoo email routing module
    odoo send mail from user email
    smart mail server switch odoo
    how to use different smtp servers for different users in odoo
    odoo send email from different companies
    set outgoing mail server per user in odoo
    odoo email configuration multi company
    outgoing mail server per user or company odoo
    smart mail server selection in odoo

    """,
    'depends': ['mail'],
    'data': [
        'views/res_config_views.xml',
        'views/ir_mail_server_view.xml',
        'views/company.xml'
    ],
    "images": [
        "static/description/main_screen.gif",
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
'license': 'OPL-1',
    'price': 10.00,

}
