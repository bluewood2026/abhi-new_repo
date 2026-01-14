from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    accounts_email = fields.Char(
        string="Accounts Email",
        help="Reply-To email when Accounts user sends mails"
    )

    default_cc_emails = fields.Char(
        string="Default CC Emails",
        help="Comma separated CC emails for outgoing mails"
    )
