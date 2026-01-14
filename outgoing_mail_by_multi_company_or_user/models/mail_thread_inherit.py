from odoo import models, api

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)

        user = self.env.user
        company = user.company_id

        user_email = (user.email or '').strip().lower()
        accounts_email = (company.accounts_email or '').strip().lower()
        company_email = (company.email or '').strip()
        cc_emails = (company.default_cc_emails or '').strip()

        mail = self.env['mail.mail'].search(
            [('mail_message_id', '=', message.id)],
            limit=1
        )

        if mail:
            # -------------------------------------------------
            # Reply-To logic (email comparison based)
            # -------------------------------------------------
            if user_email and accounts_email and user_email == accounts_email:
                # Accounts user → company email
                if company_email:
                    mail.reply_to = company_email
            elif user_email:
                # Normal user → user email
                mail.reply_to = user_email

            # -------------------------------------------------
            # CC logic
            # -------------------------------------------------
            if user_email != 'info@nextgengrannyflats.com.au' and cc_emails:
                existing_cc = mail.email_cc or ''
                mail.email_cc = (
                    f"{existing_cc},{cc_emails}" if existing_cc else cc_emails
                )
            else:
                mail.email_cc = False

        return message
