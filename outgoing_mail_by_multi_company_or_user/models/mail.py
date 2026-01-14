# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from odoo import models, api


class Mail(models.Model):
    _inherit = "mail.mail"

    @api.model
    def create(self, vals):

        for val in vals:

            user = False

            if 'uid' in self._context:
                user = self.env['res.users'].browse(
                    self._context.get('uid', 0))
            elif self.env.user:
                user = self.env.user
            elif self.uid:
                user = self.env['res.users'].browse(
                    self._context.get('uid', 0))

            ICPSudo = self.env['ir.config_parameter'].sudo()

            smtp_by_company = bool(ICPSudo.get_param(
                'send_mail_company_wish_ext.smtp_by_company'))
            smtp_by_user = bool(ICPSudo.get_param(
                'send_mail_company_wish_ext.smtp_by_user'))

            active_company_id = self.env.company and self.env.company.id or 0

            if smtp_by_company and smtp_by_user and user:
                out_mail_sever = self.env['ir.mail_server'].search(
                    [('company_ids', '=', active_company_id), ('user_ids', 'in', [user.id])], limit=1)
            elif smtp_by_company and active_company_id:
                out_mail_sever = self.env['ir.mail_server'].search(
                    [('company_ids', '=', active_company_id)], limit=1)
            elif smtp_by_user and user:
                out_mail_sever = self.env['ir.mail_server'].search(
                    [('user_ids', 'in', [user.id])], limit=1)
            else:
                return super(Mail, self).create(val)

            if out_mail_sever:
                active_u_name = user.partner_id and user.partner_id.name or ''
                active_u_email = user.partner_id and user.partner_id.email or ''
                active_u_user = out_mail_sever.smtp_user or ''

                if active_u_user != '':
                    email_from = active_u_name + " " + "<" + active_u_user + ">"
                    reply_to = active_u_name + " " + "<" + \
                               active_u_email or active_u_user
                    val.update({
                        'email_from': email_from, 'reply_to': reply_to
                    })
                val.update({'mail_server_id': out_mail_sever.id})

            result = super(Mail, self).create(val)
            return result

class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):
        for val in vals:

            user = False

            if 'uid' in self._context:
                user = self.env['res.users'].browse(
                    self._context.get('uid', 0))
            elif self.env.user:
                user = self.env.user
            elif self.uid:
                user = self.env['res.users'].browse(
                    self._context.get('uid', 0))

            ICPSudo = self.env['ir.config_parameter'].sudo()

            smtp_by_company = bool(ICPSudo.get_param(
                'send_mail_company_wish_ext.smtp_by_company'))
            smtp_by_user = bool(ICPSudo.get_param(
                'send_mail_company_wish_ext.smtp_by_user'))

            if user:
                active_company_id = self.env.company and self.env.company.id or 0

                if smtp_by_company and smtp_by_user:
                    mail_server = self.env['ir.mail_server'].sudo().search(
                        [('user_ids', 'in', [user.id]), ('company_ids', 'in', [active_company_id])], limit=1)
                    if mail_server:
                        val.update({'mail_server_id': mail_server.id})
                elif smtp_by_company:
                    mail_server = self.env['ir.mail_server'].sudo().search(
                        [('is_smtp_by_company', '=', True)])
                    if mail_server:
                        out_mail_sever = self.env['ir.mail_server'].sudo().search([])
                        for mail_server in out_mail_sever:
                            for company in mail_server.company_ids:
                                if active_company_id == company.id:
                                    val.update({'mail_server_id': mail_server.id})
                else:
                    out_mail_sever = self.env['ir.mail_server'].sudo().search(
                        [('user_ids', 'in', [user.id])], limit=1)
                    if out_mail_sever:
                        val.update({'mail_server_id': out_mail_sever.id})

            result = super(MailMessage, self).create(val)
            return result