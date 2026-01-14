from odoo import api, fields, models

from collections import defaultdict


class PoSoWizard(models.TransientModel):
    _name = 'po.so.wizard'
    _description = 'PO SO Report Wizard'

    project_ids = fields.Many2many('project.project', string='Projects', required=True)
    report_type = fields.Selection([
        ('sale', 'Sale Order'),
        ('purchase', 'Purchase Order')
    ], string='Report Type', default='sale', required=True)

    def generate_report(self):
        # Clear any context that might cause issues with account.move views
        ctx = self.env.context.copy()
        ctx.pop('default_project_id', None)
        ctx.pop('project_id', None)

        if self.report_type == 'sale':
            return self.env.ref('po_so_report.action_report_sale_order').with_context(ctx).report_action(self)
        else:
            return self.env.ref('po_so_report.action_report_purchase_order').with_context(ctx).report_action(self)


class ReportSaleOrder(models.AbstractModel):
    _name = 'report.po_so_report.report_sale_order_template'
    _description = 'Sale Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['po.so.wizard'].browse(docids)
        projects = wizard.project_ids

        report_data = []

        for project in projects:
            data = self._process_sale_orders(project)
            report_data.extend(data)

        # Calculate max invoices and payments for dynamic columns
        max_invoices = 0
        max_payments = 0

        for rec in report_data:
            max_invoices = max(max_invoices, len(rec.get('invoices', [])))
            max_payments = max(max_payments, len(rec.get('payments', [])))

        # Calculate totals grouped by project
        project_totals = {}
        for rec in report_data:
            project_name = rec.get('project_name', '')
            if project_name not in project_totals:
                project_totals[project_name] = {
                    'total_so_po': 0.0,
                    'total_invoice': 0.0,
                    'total_payment': 0.0,
                    'total_diff_so_invoice': 0.0,
                    'total_diff_invoice_payment': 0.0,
                }
            project_totals[project_name]['total_so_po'] += rec.get('so_po_total', 0.0)
            project_totals[project_name]['total_invoice'] += rec.get('invoice_total', 0.0)
            project_totals[project_name]['total_payment'] += rec.get('payment_total', 0.0)
            project_totals[project_name]['total_diff_so_invoice'] += rec.get('diff_so_invoice', 0.0)
            project_totals[project_name]['total_diff_invoice_payment'] += rec.get('diff_invoice_payment', 0.0)

        return {
            'doc_ids': docids,
            'doc_model': 'po.so.wizard',
            'docs': wizard,
            'report_data': report_data,
            'max_invoices': max_invoices,
            'max_payments': max_payments,
            'invoice_range': list(range(max_invoices)) if max_invoices > 0 else [],
            'payment_range': list(range(max_payments)) if max_payments > 0 else [],
            'project_totals': project_totals,
        }

    def _process_sale_orders(self, project):
        """Process Sale Orders for the project"""
        result = []

        # Get all sale orders linked to the project
        sale_orders = self.env['sale.order'].search([
            ('project_id', '=', project.id)
        ])

        if not sale_orders:
            # Project has no sale orders, show empty row
            result.append({
                'vendor_name': '',
                'project_name': project.name,
                'so_po_number': '',
                'so_po_total': 0.0,
                'invoices': [],
                'invoice_total': 0.0,
                'invoice_items': '',
                'diff_so_invoice': 0.0,
                'payments': [],
                'payment_total': 0.0,
                'diff_invoice_payment': 0.0
            })
            return result

        for sale_order in sale_orders:
            # Get invoices for this sale order
            invoices = self.env['account.move'].search([
                ('invoice_origin', '=', sale_order.name),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], order='invoice_date asc')

            # Process invoices dynamically
            invoices_list = []
            invoice_total = 0.0
            invoice_items = []

            for invoice in invoices:
                invoice_info = {
                    'name': invoice.name,
                    'amount': invoice.amount_total,
                    'date': invoice.invoice_date
                }
                invoices_list.append(invoice_info)
                invoice_total += invoice.amount_total

                # Get invoice items
                for line in invoice.invoice_line_ids:
                    if line.product_id:
                        invoice_items.append(line.product_id.name)

            # Get all payments for these invoices
            payments_list = []
            payment_total = 0.0
            processed_payments = set()

            for invoice in invoices:
                # Get payments via invoice reference
                payment_moves = self.env['account.payment'].search([
                    ('memo', '=', invoice.name),
                    ('state', '=', 'paid'),
                    ('partner_type', '=', 'customer')
                ])

                for payment in payment_moves:
                    if payment.id not in processed_payments:
                        payment_info = {
                            'date': payment.date,
                            'amount': payment.amount,
                            'name': payment.name
                        }
                        payments_list.append(payment_info)
                        payment_total += payment.amount
                        processed_payments.add(payment.id)

            # Sort payments by date
            payments_list.sort(key=lambda x: x['date'])

            result.append({
                'vendor_name': sale_order.partner_id.name,
                'project_name': project.name,
                'so_po_number': sale_order.name,
                'so_po_total': sale_order.amount_total,
                'invoices': invoices_list,
                'invoice_total': invoice_total,
                'invoice_items': ', '.join(set(invoice_items)),
                'diff_so_invoice': sale_order.amount_total - invoice_total,
                'payments': payments_list,
                'payment_total': payment_total,
                'diff_invoice_payment': invoice_total - payment_total
            })

        return result


class ReportPurchaseOrder(models.AbstractModel):
    _name = 'report.po_so_report.report_purchase_order_template'
    _description = 'Purchase Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['po.so.wizard'].browse(docids)
        projects = wizard.project_ids

        report_data = []

        for project in projects:
            report_data.extend(self._process_purchase_orders(project))

        max_invoices = max((len(r['invoices']) for r in report_data), default=0)
        max_payments = max((len(r['payments']) for r in report_data), default=0)

        # Calculate totals grouped by project
        project_totals = {}
        for rec in report_data:
            project_name = rec.get('project_name', '')
            if project_name not in project_totals:
                project_totals[project_name] = {
                    'total_quote': 0.0,
                    'total_invoice': 0.0,
                    'total_payment': 0.0,
                    'total_amount': 0.0,
                }
            project_totals[project_name]['total_quote'] += rec.get('quote', 0.0)
            project_totals[project_name]['total_invoice'] += rec.get('total_invoice', 0.0)
            project_totals[project_name]['total_payment'] += rec.get('total_payment', 0.0)
            project_totals[project_name]['total_amount'] += (rec.get('quote', 0.0) - rec.get('total_payment', 0.0))

        return {
            'doc_ids': docids,
            'doc_model': 'po.so.wizard',
            'docs': wizard,
            'report_data': report_data,
            'max_invoices': max_invoices,
            'max_payments': max_payments,
            'invoice_range': list(range(max_invoices)),
            'payment_range': list(range(max_payments)),
            'project_totals': project_totals,
        }

    # ---------------------------------------------------------
    # MAIN LOGIC (ODOO 19 OFFICIAL)
    # ---------------------------------------------------------
    def _process_purchase_orders(self, project):
        result = []

        po_lines = self.env['purchase.order.line'].search([
            ('analytic_distribution', 'in', project.account_id.ids),
        ])
        purchase_orders = po_lines.mapped('order_id')

        for po in purchase_orders:
            bills = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'posted'),
                ('invoice_origin', '=', po.name),
            ], order='invoice_date')

            invoices_list = []
            payments_list = []
            total_invoice = 0.0
            total_payment = 0.0
            processed_payment_moves = set()

            for bill in bills:
                # -------------------------
                # INVOICE
                # -------------------------
                invoices_list.append({
                    'name': bill.name,
                    'amount': bill.amount_total,
                    'date': bill.invoice_date,
                })
                total_invoice += bill.amount_total

                # -------------------------
                # PAYMENTS (ODOO DEFAULT WAY)
                # -------------------------
                payable_lines = bill.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'liability_payable'
                )

                for line in payable_lines:
                    for match in line.matched_debit_ids:
                        payment_move = match.debit_move_id.move_id

                        if not payment_move:
                            continue

                        if payment_move.id in processed_payment_moves:
                            continue

                        payments_list.append({
                            'name': payment_move.name,
                            'amount': abs(match.amount),
                            'date': payment_move.date,
                        })

                        total_payment += abs(match.amount)
                        processed_payment_moves.add(payment_move.id)

            # -------------------------
            # DATE-WISE SORTING
            # -------------------------
            invoices_list.sort(key=lambda x: x['date'] or False)
            payments_list.sort(key=lambda x: x['date'] or False)

            result.append({
                'vendor_name': po.partner_id.name,
                'project_name': project.name,
                'so_po_number': po.name,
                'quote': po.amount_total,
                'invoices': invoices_list,
                'total_invoice': total_invoice,
                'payments': payments_list,
                'total_payment': total_payment,
            })

        return result


class ReportPoSo(models.AbstractModel):
    _name = 'report.po_so_report.report_po_so_template'
    _description = 'PO/SO Report'


class PurchaseBillWizard(models.TransientModel):
    _name = 'purchase.bill.wizard'
    _description = 'Purchase Bill Report Wizard'

    project_id = fields.Many2one('project.project', string='Project', required=True)

    def generate_report(self):
        # Clear any context that might cause issues with account.move views
        ctx = self.env.context.copy()
        ctx.pop('default_project_id', None)
        ctx.pop('project_id', None)
        return self.env.ref('po_so_report.action_report_purchase_bill').with_context(ctx).report_action(self)


class ReportPurchaseBill(models.AbstractModel):
    _name = 'report.po_so_report.report_purchase_bill_template'
    _description = 'Purchase Bill Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['purchase.bill.wizard'].browse(docids)
        project = wizard.project_id

        report_data = self._process_purchase_bills(project)

        # Calculate max payments for dynamic columns
        max_payments = max((len(r.get('payments', [])) for r in report_data), default=0)

        # Calculate totals
        total_bill_amount = sum(r.get('bill_amount', 0.0) for r in report_data)
        total_payment = sum(r.get('payment_total', 0.0) for r in report_data)
        total_balance = sum((r.get('bill_amount', 0.0) - r.get('payment_total', 0.0)) for r in report_data)

        return {
            'doc_ids': docids,
            'doc_model': 'purchase.bill.wizard',
            'docs': wizard,
            'report_data': report_data,
            'max_payments': max_payments,
            'payment_range': list(range(max_payments)) if max_payments > 0 else [],
            'total_bill_amount': total_bill_amount,
            'total_payment': total_payment,
            'total_balance': total_balance,
        }

    # def _process_purchase_bills(self, project):
    #     """Process Purchase Bills for the project - date-wise with payments"""
    #     result = []

    #     # Get all purchase bills (in_invoice) linked to the project via analytic distribution
    #     # In Odoo 19, analytic_distribution is a JSON field with account IDs as keys
    #     project_account_id = project.account_id.id if project.account_id else False
        
    #     if not project_account_id:
    #         return result

    #     # Get all bills and filter by analytic distribution
    #     all_bills = self.env['account.move'].search([
    #         ('move_type', '=', 'in_invoice'),
    #         ('state', '=', 'posted'),
    #     ], order='invoice_date asc')

    #     # Filter bills that have analytic distribution matching the project
    #     project_bills = []
    #     for bill in all_bills:
    #         # Check if bill has analytic distribution for this project
    #         bill_lines = bill.invoice_line_ids.filtered(
    #             lambda l: l.analytic_distribution and 
    #             isinstance(l.analytic_distribution, dict) and
    #             str(project_account_id) in l.analytic_distribution
    #         )
    #         if bill_lines:
    #             project_bills.append(bill)

    #     if not project_bills:
    #         # Project has no bills, show empty row
    #         result.append({
    #             'bill_number': '',
    #             'bill_date': False,
    #             'vendor_name': '',
    #             'bill_amount': 0.0,
    #             'payments': [],
    #             'payment_total': 0.0,
    #         })
    #         return result

    #     # Process each bill date-wise
    #     for bill in project_bills:
    #         # Get payments for this bill
    #         payments_list = []
    #         payment_total = 0.0
    #         processed_payment_moves = set()

    #         # Get payments via matched debit (Odoo standard way)
    #         payable_lines = bill.line_ids.filtered(
    #             lambda l: l.account_id.account_type == 'liability_payable'
    #         )

    #         for line in payable_lines:
    #             for match in line.matched_debit_ids:
    #                 payment_move = match.debit_move_id.move_id

    #                 if not payment_move:
    #                     continue

    #                 if payment_move.id in processed_payment_moves:
    #                     continue

    #                 # Get payment account (journal account or payment account)
    #                 payment_account = ''
    #                 # Try to get from payment move lines first (more accurate)
    #                 payment_lines = payment_move.line_ids.filtered(
    #                     lambda l: l.account_id.account_type in ['asset_cash', 'asset_bank', 'liability_payable']
    #                 )
    #                 if payment_lines:
    #                     # Get the account code and name
    #                     account = payment_lines[0].account_id
    #                     payment_account = account.code or account.name
    #                 elif payment_move.journal_id and payment_move.journal_id.default_account_id:
    #                     # Fallback to journal default account
    #                     account = payment_move.journal_id.default_account_id
    #                     payment_account = account.code or account.name

    #                 payments_list.append({
    #                     'name': payment_move.name,
    #                     'amount': abs(match.amount),
    #                     'date': payment_move.date,
    #                     'account': payment_account,
    #                 })

    #                 payment_total += abs(match.amount)
    #                 processed_payment_moves.add(payment_move.id)

    #         # Sort payments by date
    #         payments_list.sort(key=lambda x: x['date'] or False)

    #         result.append({
    #             'bill_number': bill.name,
    #             'bill_date': bill.invoice_date,
    #             'vendor_name': bill.partner_id.name if bill.partner_id else '',
    #             'bill_amount': bill.amount_total,
    #             'payments': payments_list,
    #             'payment_total': payment_total,
    #         })

    #     # Sort bills by date
    #     result.sort(key=lambda x: x['bill_date'] or False)

    #     return result

    def _process_purchase_bills(self, project):
        result = []

        project_account_id = project.account_id.id if project.account_id else False
        if not project_account_id:
            return result

        # ---------------------------------------------------------
        # Get posted vendor bills
        # ---------------------------------------------------------
        bills = self.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
        ], order='invoice_date asc')

        project_bills = []
        for bill in bills:
            lines = bill.invoice_line_ids.filtered(
                lambda l: isinstance(l.analytic_distribution, dict)
                and str(project_account_id) in l.analytic_distribution
            )
            if lines:
                project_bills.append(bill)

        if not project_bills:
            return result

        # =========================================================
        # PROCESS EACH BILL
        # =========================================================
        for bill in project_bills:

            payments_list = []
            payment_total = 0.0
            processed_payment_moves = set()

            payable_lines = bill.line_ids.filtered(
                lambda l: l.account_id.account_type == 'liability_payable'
            )

            # -----------------------------------------------------
            # 1️⃣ PAID PAYMENTS (RECONCILED)
            # -----------------------------------------------------
            for line in payable_lines:
                for match in line.matched_debit_ids:
                    payment_move = match.debit_move_id.move_id

                    if not payment_move or payment_move.id in processed_payment_moves:
                        continue

                    # Payment account
                    account = payment_move.line_ids.filtered(
                        lambda l: l.account_id.account_type in ['asset_cash', 'asset_bank']
                    )[:1].account_id
                    payment_account = account.code or account.name if account else ''

                    amount = abs(match.amount or 0.0)

                    payments_list.append({
                        'name': payment_move.name,
                        'amount': amount,
                        'date': payment_move.date,
                        'account': payment_account,
                    })

                    payment_total += amount
                    processed_payment_moves.add(payment_move.id)

            # -----------------------------------------------------
            # 2️⃣ IN-PROCESS PAYMENT (NOT RECONCILED YET)
            # -----------------------------------------------------
            for line in payable_lines:
                if line.matched_debit_ids:
                    continue  # already paid

                if bill.status_in_payment != 'in_payment':
                    continue

                amount = abs(
                    line.amount_residual_currency
                    if line.amount_residual_currency
                    else line.amount_residual
                )

                if not amount:
                    continue

                payments_list.append({
                    'name': 'In Process',
                    'amount': float(amount),
                    'date': bill.invoice_date,
                    'account': line.account_id.code or line.account_id.name,
                })

                payment_total += float(amount)

                break  # ON

            # -----------------------------------------------------
            # FINALIZE BILL DATA
            # -----------------------------------------------------
            payments_list.sort(key=lambda x: x['date'] or False)

            result.append({
                'bill_number': bill.name,
                'bill_date': bill.invoice_date,
                'vendor_name': bill.partner_id.name or '',
                'bill_amount': float(bill.amount_total),
                'payments': payments_list,
                'payment_total': float(payment_total),
            })

        return result
