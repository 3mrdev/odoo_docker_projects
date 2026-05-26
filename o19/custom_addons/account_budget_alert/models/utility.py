from odoo import _
from odoo.tools import formatLang
from dateutil.relativedelta import relativedelta

def get_analytic_json(self,analytic_distribution):
    distribution = []
    for analytic_account_ids, percentage in (analytic_distribution or {}).items():
        dist_dict = {'rate': float(percentage) / 100}
        for analytic_account in self.env['account.analytic.account'].browse(map(int, analytic_account_ids.split(","))).exists():
            root_plan = analytic_account.root_plan_id
            dist_dict[root_plan._column_name()] = analytic_account.id
        distribution.append(dist_dict)
    return distribution

def get_analytic_accounts(self, analytic_distribution):
    analytic_account_ids = []
    analytic_account_rate = {}
    analytic_json = get_analytic_json(self,analytic_distribution)
    if analytic_json:
        for json in analytic_json:
            for key, value in json.items():
                if key in self.env['budget.line']._fields:
                    analytic_account_ids.append(value)
                    analytic_account_rate[value] = json['rate']
    return self.env['account.analytic.account'].browse(analytic_account_ids),analytic_account_rate

def get_budget_lines(self, date, analytic_account_id):
    budget_lines = self.env["budget.line"].sudo().search([
        ('budget_analytic_id', 'any', (
            ('budget_type', '!=', 'revenue'),
            ('state', '=', 'confirmed'),
        )),
        ('date_from', '<=', date),
        ('date_to', '>=', date),
        # ('budget_alert_type', '!=', 'none'),
        (analytic_account_id.plan_id._column_name(), '=', analytic_account_id.id),
    ])
    return budget_lines

def get_budget_alert(self,record,is_expense=False,state_field_name='state',date_field_name='date_order',product_qty_field_name='product_qty',line_field_name='order_line',states=['draft','sent']):
    analytic_account_display = ""
    is_above_budget = False
    block_budget = False
    if getattr(record,state_field_name) in states:
        
        analytic_accounts_ids = []
        if is_expense:
            analytic_accounts , analytic_account_rate = get_analytic_accounts(self,record.analytic_distribution)
            for ac in analytic_accounts:
                if ac.id not in analytic_accounts_ids:
                    analytic_accounts_ids.append(ac.id)
        else:
            for line in getattr(record,line_field_name,[]):
                analytic_accounts , analytic_account_rate = get_analytic_accounts(self,line.analytic_distribution)
                for ac in analytic_accounts:
                    if ac.id not in analytic_accounts_ids:
                        analytic_accounts_ids.append(ac.id)

        analytic_accounts_outer = self.env['account.analytic.account'].browse(analytic_accounts_ids)
        for analytic_account_outer in analytic_accounts_outer:
            budget_lines = get_budget_lines(self,getattr(record,date_field_name), analytic_account_outer)
            record_line_display = ""
            analytic_account_uncommitted_amount = 0
            
            if is_expense:
                analytic_accounts_inner , analytic_account_rate = get_analytic_accounts(self,record.analytic_distribution)
                total_amount = getattr(record,'total_amount_currency',0)
                uncommitted_amount = total_amount * analytic_account_rate.get(analytic_account_outer.id,1)
                for analytic_account_inner in analytic_accounts_inner:
                    if analytic_account_outer.id == analytic_account_inner.id:
                        analytic_account_uncommitted_amount += uncommitted_amount
                        record_line_display += _(
                            "-- Product: %(product)s Uncommitted Amount: %(uncommitted)s Rate: %(rate)s %%\n",
                            product=record.product_id.name,
                            uncommitted=formatLang(self.env, uncommitted_amount, currency_obj=record.company_id.currency_id),
                            rate=analytic_account_rate.get(analytic_account_inner.id,1)*100,
                        )
            else:
                for line in getattr(record,line_field_name,[]):
                    analytic_accounts_inner , analytic_account_rate = get_analytic_accounts(self,line.analytic_distribution)
                    product_qty = getattr(line,product_qty_field_name) - getattr(line,'qty_invoiced',0)
                    uncommitted_amount = (line.price_unit * product_qty) * analytic_account_rate.get(analytic_account_outer.id,1)
                    for analytic_account_inner in analytic_accounts_inner:
                        if analytic_account_outer.id == analytic_account_inner.id:
                            analytic_account_uncommitted_amount += uncommitted_amount
                            record_line_display += _(
                                "-- Product: %(product)s Uncommitted Amount: %(uncommitted)s Rate: %(rate)s %%\n",
                                product=line.product_id.name,
                                uncommitted=formatLang(self.env, uncommitted_amount, currency_obj=record.company_id.currency_id),
                                rate=analytic_account_rate.get(analytic_account_inner.id,1)*100,
                            )

            budget_display = ""
            for budget in budget_lines:
                if budget.committed_amount + analytic_account_uncommitted_amount > budget.budget_amount:
                    budget_display += _(
                        "- Budget: %(name)s with amount: %(budget_amount)s (Left: %(budget_amount)s - %(committed)s - %(uncommitted)s = %(budget_left)s)\n"
                        "%(record_line_display)s"
                        "- Committed: %(committed)s Uncommitted: %(uncommitted)s\n\n",
                        name=budget.budget_analytic_id.name,
                        budget_amount=formatLang(self.env, budget.budget_amount, currency_obj=record.company_id.currency_id),
                        record_line_display=record_line_display,
                        committed=formatLang(self.env, budget.committed_amount, currency_obj=record.company_id.currency_id),
                        uncommitted=formatLang(self.env, analytic_account_uncommitted_amount, currency_obj=record.company_id.currency_id),
                        budget_left=formatLang(self.env, budget.budget_amount - (budget.committed_amount + analytic_account_uncommitted_amount), currency_obj=record.company_id.currency_id),
                    )

                    if budget.budget_analytic_id.budget_alert_type == 'block':
                        is_above_budget = True
                        block_budget = True
                    elif budget.budget_analytic_id.budget_alert_type == 'warning':
                        is_above_budget = True
                    elif budget.budget_analytic_id.budget_alert_type == 'none':
                        if budget.budget_alert_type == 'block':
                            is_above_budget = True
                            block_budget = True
                        elif budget.budget_alert_type == 'warning':
                            is_above_budget = True
            
            if budget_display:
                analytic_account_display += _(
                    "[X] Analytic Account: %(analytic)s\n"
                    "%(budget_display)s",
                    analytic=analytic_account_outer.name,
                    budget_display=budget_display,
                )

                if not is_expense:
                    for line in getattr(record,line_field_name,[]):
                        analytic_accounts_inner , analytic_account_rate = get_analytic_accounts(self,line.analytic_distribution)
                        for analytic_account_inner in analytic_accounts_inner:
                            if analytic_account_outer.id == analytic_account_inner.id:
                                line.is_above_budget_alert = is_above_budget
            else:
                if not is_expense:
                    for line in getattr(record,line_field_name,[]):
                        analytic_accounts_inner , analytic_account_rate = get_analytic_accounts(self,line.analytic_distribution)
                        for analytic_account_inner in analytic_accounts_inner:
                            if analytic_account_outer.id == analytic_account_inner.id:
                                line.is_above_budget_alert = is_above_budget
            
    return block_budget,is_above_budget, analytic_account_display

def get_budget_committed_amount(self, item):
    AccountMoveLine = self.env['account.move.line']
    account_id = get_account_id(self,item)
    
    committed = 0.0
    if account_id and item.date:
        # Calculate the first and last day of the month
        date_from = item.date.replace(day=1)
        # Get last day of month
        if item.date.month == 12:
            date_to = item.date.replace(day=31)
        else:
            date_to = (item.date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1))
        
        # Build domain for the period
        domain = [
            ('account_id', '=', account_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('parent_state', '=', 'posted'),
        ]
        
        # if item.company_id:
        #     domain.append(('company_id', '=', item.company_id.id))
        
        # Get balance using read_group (this is efficient!)
        result = AccountMoveLine.read_group(
            domain=domain,
            fields=['balance:sum'],
            groupby=[],
        )
        
        balance = result[0]['balance'] if result else 0.0
        
        # Adjust for account type
        if account_id.account_type in ['expense', 'expense_depreciation', 'expense_direct_cost', 'income', 'income_other']:
            committed = abs(balance)
        else:
            committed = balance
    
    return committed

def get_financial_budget_lines(self, date, account_id):

    if not date:
        return []

    # Calculate the first and last day of the month
    date_from = date.replace(day=1)
    # Get last day of month
    if date.month == 12:
        date_to = date.replace(day=31)
    else:
        date_to = (date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1))
    financial_budget_lines = self.env["account.report.budget.item"].sudo().search([
        ('date', '>=', date_from),
        ('date', '<=', date_to),
        ('account_id', '=', account_id.id)
    ])
    return financial_budget_lines

def get_account_id(self,line):
    account_id = False
    if getattr(line,'account_id',False):
        account_id = line.account_id
    else:
        account = line.product_id.product_tmpl_id._get_product_accounts()['expense']
        if account:
            account_id = account
    return account_id

def get_financial_budget_alert(self,record,is_expense=False,state_field_name='state',date_field_name='date_order',product_qty_field_name='product_qty',line_field_name='order_line',states=['draft','sent']):
    account_display = ""
    is_above_budget = False
    block_budget = False
    if getattr(record,state_field_name) in states:
        
        accounts_ids = []
        if is_expense:
            account_id = get_account_id(self,record)
            if account_id:
                accounts_ids.append(account_id.id)
        else:
            for line in getattr(record,line_field_name,[]):
                account_id = get_account_id(self,line)
                if account_id:
                    if account_id.id not in accounts_ids:
                        accounts_ids.append(account_id.id)

        accounts_outer = self.env['account.account'].browse(accounts_ids)
        for account_outer in accounts_outer:
            budget_lines = get_financial_budget_lines(self,getattr(record,date_field_name), account_outer)
            record_line_display = ""
            account_uncommitted_amount = 0
            
            if is_expense:
                total_amount = getattr(record,'total_amount_currency',0)
                uncommitted_amount = total_amount
                account_uncommitted_amount += uncommitted_amount
                record_line_display += _(
                    "-- Product: %(product)s Uncommitted Amount: %(uncommitted)s\n",
                    product=record.product_id.name,
                    uncommitted=formatLang(self.env, uncommitted_amount, currency_obj=record.company_id.currency_id),
                )
            else:
                for line in getattr(record,line_field_name,[]):
                    product_qty = getattr(line,product_qty_field_name) - getattr(line,'qty_invoiced',0)
                    uncommitted_amount = (line.price_unit * product_qty)
                    account_uncommitted_amount += uncommitted_amount
                    record_line_display += _(
                        "-- Product: %(product)s Uncommitted Amount: %(uncommitted)s\n",
                        product=line.product_id.name,
                        uncommitted=formatLang(self.env, uncommitted_amount, currency_obj=record.company_id.currency_id),
                    )

            budget_display = ""
            for budget in budget_lines:
                committed_amount = get_budget_committed_amount(self,budget)
                if committed_amount + account_uncommitted_amount > budget.amount:
                    budget_display += _(
                        "- Budget: %(name)s with amount: %(budget_amount)s (Left: %(budget_amount)s - %(committed)s - %(uncommitted)s = %(budget_left)s)\n"
                        "%(record_line_display)s"
                        "- Committed: %(committed)s Uncommitted: %(uncommitted)s\n\n",
                        name=budget.budget_id.name,
                        budget_amount=formatLang(self.env, budget.amount, currency_obj=record.company_id.currency_id),
                        record_line_display=record_line_display,
                        committed=formatLang(self.env, committed_amount, currency_obj=record.company_id.currency_id),
                        uncommitted=formatLang(self.env, account_uncommitted_amount, currency_obj=record.company_id.currency_id),
                        budget_left=formatLang(self.env, budget.amount - (committed_amount + account_uncommitted_amount), currency_obj=record.company_id.currency_id),
                    )
                    if budget.budget_id.budget_alert_type == 'block':
                        is_above_budget = True
                        block_budget = True
                    elif budget.budget_id.budget_alert_type == 'warning':
                        is_above_budget = True
                    elif budget.budget_id.budget_alert_type == 'none':
                        if budget.budget_alert_type == 'block':
                            is_above_budget = True
                            block_budget = True
                        elif budget.budget_alert_type == 'warning':
                            is_above_budget = True
        
            if budget_display:
                account_display += _(
                    "[X] Account: %(account)s\n"
                    "%(budget_display)s",
                    account=account_outer.name,
                    budget_display=budget_display,
                )

                if not is_expense:
                    for line in getattr(record,line_field_name,[]):
                        line.is_above_financial_budget_alert = is_above_budget
            else:
                if not is_expense:
                    for line in getattr(record,line_field_name,[]):
                        line.is_above_financial_budget_alert = is_above_budget
            
    return block_budget,is_above_budget, account_display