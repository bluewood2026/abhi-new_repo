# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    smtp_by_company = fields.Boolean(string="SMTP BY COMPANY", default=False)
    smtp_by_user = fields.Boolean(string="SMTP BY USER", default=False)

    # @api.onchange('smtp_by_company')
    # def onchange_smtp_config_company(self):
    #     if self.smtp_by_company:
    #         self.smtp_by_user = False
    #
    # @api.onchange('smtp_by_user')
    # def onchange_smtp_config_user(self):
    #     if self.smtp_by_user:
    #         self.smtp_by_company = False

    @api.constrains('smtp_by_company', 'smtp_by_user')
    def _check_smtp_by_company_and_user(self):
        for smtp in self:
            if smtp.smtp_by_company == True and smtp.smtp_by_user == True:
                raise ValidationError(_('Outgoing Mail Configuration must be set by either the user or the company, but not both at the same time.'))


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        smtp_by_company = ICPSudo.get_param(
            'send_mail_company_wish_ext.smtp_by_company')
        smtp_by_user = ICPSudo.get_param(
            'send_mail_company_wish_ext.smtp_by_user')

        res.update(
            smtp_by_company=smtp_by_company,
            smtp_by_user=smtp_by_user
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            "send_mail_company_wish_ext.smtp_by_company", self.smtp_by_company)
        ICPSudo.set_param(
            "send_mail_company_wish_ext.smtp_by_user", self.smtp_by_user)
        mail_server_config = self.env['ir.mail_server'].sudo().search([])
        for mail_server in mail_server_config:
            mail_server.is_smtp_by_company = self.smtp_by_company
            mail_server.is_smtp_by_user = self.smtp_by_user
