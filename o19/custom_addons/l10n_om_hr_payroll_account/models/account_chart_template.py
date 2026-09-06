from collections import defaultdict

from odoo import api, models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @api.model
    def _configure_payroll_account_om(self, companies):
        """Configure payroll accounts for Oman localization.

        Maps each Oman salary rule to self-contained payroll accounts.
        Uses independent account codes (2006xx liabilities, 5012xx expenses)
        to avoid conflicts with the l10n_om Chart of Accounts.

        Accounts (created by account_chart_template_data.xml):
        - 200601: Employees Payables
        - 200602: End of Service Provision
        - 200603: PASI Payable
        - 501201: Basic Salary
        - 501202: Housing Allowance
        - 501203: Transportation Allowance
        - 501204: Staff Other Allowances
        - 501205: Air Tickets
        - 501206: Medical Insurance
        - 501207: End of Service Indemnity
        - 501208: PASI Employer Expense
        - 501209: Salary Deductions
        """
        account_codes = [
            # Liability accounts
            '200601',  # Employees Payables
            '200602',  # End of Service Provision
            '200603',  # PASI Payable
            # Expense accounts
            '501201',  # Basic Salary
            '501202',  # Housing Allowance
            '501203',  # Transportation Allowance
            '501204',  # Staff Other Allowances
            '501205',  # Air Tickets
            '501206',  # Medical Insurance
            '501207',  # End of Service Indemnity
            '501208',  # PASI Employer Expense
            '501209',  # Salary Deductions
        ]
        default_account = '200601'  # Employees Payables

        structure = self.env.ref('l10n_om_hr_payroll.om_regular_pay_structure')
        rules_mapping = defaultdict(dict)

        # ================================================ #
        #          Default Rules                           #
        # ================================================ #

        # Basic Salary → Basic Salary Expense
        basic_rule = self.env['hr.salary.rule'].search([
            ('struct_id', '=', structure.id),
            ('code', '=', 'BASIC'),
        ], limit=1)
        rules_mapping[basic_rule]['debit'] = '501201'

        # Net Salary → Credit Employees Payables
        net_rule = self.env['hr.salary.rule'].search([
            ('struct_id', '=', structure.id),
            ('code', '=', 'NET'),
        ], limit=1)
        rules_mapping[net_rule]['credit'] = '200601'

        # ================================================ #
        #          Allowance Rules (A001 - A018)           #
        # ================================================ #

        # Housing Allowance → Housing Allowance Expense
        housing_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_a001_housing')
        rules_mapping[housing_rule]['debit'] = '501202'

        # Transportation Allowance → Transportation Expense
        transport_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_a002_transportation')
        rules_mapping[transport_rule]['debit'] = '501203'

        # Medical Allowance → Medical Insurance Expense
        medical_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_a010_medical')
        rules_mapping[medical_rule]['debit'] = '501206'

        # Air Fare Allowance → Air Tickets Expense
        air_fare_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_a017_air_fare')
        rules_mapping[air_fare_rule]['debit'] = '501205'

        # All other allowances → Staff Other Allowances
        other_allowance_refs = [
            'l10n_om_hr_payroll.salary_rule_a003_telephone',
            'l10n_om_hr_payroll.salary_rule_a004_communication',
            'l10n_om_hr_payroll.salary_rule_a005_utility',
            'l10n_om_hr_payroll.salary_rule_a006_electricity',
            'l10n_om_hr_payroll.salary_rule_a007_meals',
            'l10n_om_hr_payroll.salary_rule_a011_nature_of_work',
            'l10n_om_hr_payroll.salary_rule_a012_technician',
            'l10n_om_hr_payroll.salary_rule_a013_high_cost',
            'l10n_om_hr_payroll.salary_rule_a014_shift',
            'l10n_om_hr_payroll.salary_rule_a015_motivational',
            'l10n_om_hr_payroll.salary_rule_a016_water',
            'l10n_om_hr_payroll.salary_rule_a018_other',
        ]
        for ref in other_allowance_refs:
            rule = self.env.ref(ref)
            rules_mapping[rule]['debit'] = '501204'

        # ================================================ #
        #          PASI / Social Security Rules            #
        # ================================================ #

        # PASI (employee deduction) → Debit PASI Payable
        pasi_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_pasi')
        rules_mapping[pasi_rule]['debit'] = '200603'

        # PASI Employer Contribution → Expense + Payable
        pasi_contr_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_pasi_contr')
        rules_mapping[pasi_contr_rule]['debit'] = '501208'
        rules_mapping[pasi_contr_rule]['credit'] = '200603'

        # SPF (non-Omani) → Expense + Payable
        spf_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_spf')
        rules_mapping[spf_rule]['debit'] = '501208'
        rules_mapping[spf_rule]['credit'] = '200603'

        # ================================================ #
        #          Absence & Overtime                      #
        # ================================================ #

        # Absence → reduces Basic Salary expense
        absence_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_absence')
        rules_mapping[absence_rule]['debit'] = '501201'

        # Overtime → Staff Other Allowances
        overtime_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_overtime_hours')
        rules_mapping[overtime_rule]['debit'] = '501204'

        # ================================================ #
        #          Sick Time Off Deductions (D001-D003)    #
        # ================================================ #

        sick_leave_refs = [
            'l10n_om_hr_payroll.salary_rule_d001_sto75',
            'l10n_om_hr_payroll.salary_rule_d002_sto50',
            'l10n_om_hr_payroll.salary_rule_d003_sto25',
        ]
        for ref in sick_leave_refs:
            rule = self.env.ref(ref)
            rules_mapping[rule]['debit'] = '501204'

        # ================================================ #
        #          Input-based Rules                       #
        # ================================================ #

        # Attachment of Salary → Salary Deductions
        attach_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_attach_salary')
        rules_mapping[attach_rule]['debit'] = '501209'

        # Assignment of Salary → Salary Deductions
        assig_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_assig_salary')
        rules_mapping[assig_rule]['debit'] = '501209'

        # Child Support → Salary Deductions
        child_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_child_support')
        rules_mapping[child_rule]['debit'] = '501209'

        # Deduction → Salary Deductions
        deduction_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_deduction')
        rules_mapping[deduction_rule]['debit'] = '501209'

        # Loan Deduction → Salary Deductions
        loan_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_loan_deduction')
        rules_mapping[loan_rule]['debit'] = '501209'

        # Reimbursement → Employees Payables
        reimbursement_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_reimbursement')
        rules_mapping[reimbursement_rule]['debit'] = '200601'

        # ================================================ #
        #          End of Service Benefit Rules            #
        # ================================================ #

        # EOS Provision → EOS Expense + EOS Provision (liability)
        eosp_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_eosp')
        rules_mapping[eosp_rule]['debit'] = '501207'
        rules_mapping[eosp_rule]['credit'] = '200602'

        # EOS Benefit payout → uses EOS Provision (already accrued)
        eosb_rule = self.env.ref('l10n_om_hr_payroll.salary_rule_om_eosb')
        rules_mapping[eosb_rule]['debit'] = '200602'

        # ================================================ #
        #          Apply Configuration                     #
        # ================================================ #

        self._configure_payroll_account(
            companies,
            "OM",
            account_codes=account_codes,
            rules_mapping=rules_mapping,
            default_account=default_account,
        )
