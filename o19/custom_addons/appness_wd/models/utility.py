from odoo import fields,_
import datetime
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

def _block_invoice(self, record):

    partner = record.partner_id.commercial_partner_id
    
    # Only block if:
    # 1. Company has credit limit enabled
    # 2. Partner has a credit level assigned
    # 3. Credit limit is greater than 0
    if (record.company_id.account_use_credit_limit 
        and partner.credit_level_id 
        and partner.credit_limit > 0):

        limit_type = partner.credit_level_id.limit_type
        
        # Logic 1: Overdue Only (New Flow)
        if limit_type == 'overdue_only':
            today = fields.Date.today()
            
            # Calculate Mature (Overdue) Debt from existing posted invoices
            domain = [
                ('partner_id', '=', partner.id),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('amount_residual', '>', 0),
                ('date_maturity', '<=', today),
                ('company_id', '=', record.company_id.id)
            ]
            overdue_lines = self.env['account.move.line'].search(domain)
            
            #raise UserError(_("Overdue Lines: %s") % overdue_lines)
            
            # Get grace period from level
            grace_days = partner.credit_level_id.allowed_delay_days
            total_overdue = 0
            total_overdue_posted = 0
            total_overdue_unposted = 0
            for line in overdue_lines:
                # Calculate Reference Date: Today
                grace_date = line.date_maturity + datetime.timedelta(days=grace_days)
                if grace_date <= today:
                    if line.move_id.state == 'posted':
                        total_overdue += line.amount_residual
                        total_overdue_posted += line.amount_residual
                    elif line.move_id.state == 'draft':
                        total_overdue += line.amount_residual
                        total_overdue_unposted += line.amount_residual

            if total_overdue > partner.credit_limit:
                raise UserError(_(
                    "Customer '%(partner)s' has overdue debt exceeding the limit.\n\n"
                    "Credit Level: %(level)s\n"
                    "Overdue Limit: %(limit)s\n"
                    "Grace Period: %(grace)s days\n"
                    "Current Overdue Debt (Posted): %(overdue_posted)s\n"
                    "Current Overdue Debt (Unposted): %(overdue_unposted)s\n"
                    "Current Overdue Debt (Total): %(overdue)s\n"
                    "(Calculated from invoices due at %(date)s)",
                    partner=partner.name,
                    level=partner.credit_level_id.name,
                    limit=formatLang(self.env, partner.credit_limit, currency_obj=record.company_id.currency_id),
                    grace=grace_days,
                    overdue=formatLang(self.env, total_overdue, currency_obj=record.company_id.currency_id),
                    date=grace_date,
                    overdue_posted=formatLang(self.env, total_overdue_posted, currency_obj=record.company_id.currency_id),
                    overdue_unposted=formatLang(self.env, total_overdue_unposted, currency_obj=record.company_id.currency_id),
                ))
                
        # Logic 2: Total Exposure (Original Flow)
        elif limit_type == 'total_exposure':
            # Calculate total credit including this invoice + pending orders
            total_credit = partner.credit + partner.credit_to_invoice + record.amount_total
            
            if total_credit > partner.credit_limit:
                raise UserError(_(
                    "Customer '%(partner)s' exceeds credit limit.\n\n"
                    "Credit Level: %(level)s\n"
                    "Total Exposure Limit: %(limit)s\n"
                    "Current Receivable: %(credit)s\n"
                    "Pending Orders: %(pending)s\n"
                    "This Invoice: %(invoice)s\n"
                    "Total Exposure: %(total)s",
                    partner=partner.name,
                    level=partner.credit_level_id.name,
                    limit=formatLang(self.env, partner.credit_limit, currency_obj=record.company_id.currency_id),
                    credit=formatLang(self.env, partner.credit, currency_obj=record.company_id.currency_id),
                    pending=formatLang(self.env, partner.credit_to_invoice, currency_obj=record.company_id.currency_id),
                    invoice=formatLang(self.env, record.amount_total, currency_obj=record.company_id.currency_id),
                    total=formatLang(self.env, total_credit, currency_obj=record.company_id.currency_id),
                ))
