from dateutil.relativedelta import relativedelta

from odoo import models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _l10n_om_get_eos_benefit(self):
        """Compute End of Service Benefit for Oman.

        Per Royal Decree 35/2003 (Articles 40-43):
        - First 3 years: 15 days' basic salary per year of service
        - After 3 years: 30 days' (1 month) basic salary per year of service
        - Base: Last drawn basic salary only
        - Full entitlement on resignation, termination, retirement, end of contract
        - Forfeiture on gross misconduct
        """
        self.ensure_one()
        result = 0
        employee = self.employee_id
        if not employee.departure_date:
            return result

        start_date = employee._get_first_version_date()
        end_date = employee.departure_date
        total_years = self._l10n_om_get_years_of_service(start_date, end_date)

        # Basic salary only (per Oman labor law Article 40)
        basic_salary = self._get_contract_wage()

        reason_type = employee.departure_reason_id.l10n_om_reason_type
        if not reason_type:
            return result

        # Gross misconduct: forfeit EOSB
        if reason_type == 'gross_misconduct':
            return 0

        # All other reasons (fired, resigned, retired, end_of_contract): full entitlement
        if total_years <= 3:
            result = total_years * basic_salary / 2  # 15 days/month = half month per year
        else:
            result = (3 * basic_salary / 2) + ((total_years - 3) * basic_salary)

        return self.company_id.currency_id.round(result)

    def _l10n_om_get_eos_provision(self):
        """Compute monthly EOSB provision (accrual).

        This is the monthly amount set aside for future EOSB liability.
        - First 3 years: basic_salary / 24 per month
        - After 3 years: basic_salary / 12 per month
        """
        self.ensure_one()
        result = 0
        employee = self.employee_id

        # Only accrue provision for active employees (no departure)
        if employee.departure_date:
            return result

        start_date = employee._get_first_version_date()
        total_years = self._l10n_om_get_years_of_service(start_date, self.date_to)
        basic_salary = self._get_contract_wage()

        if total_years <= 3:
            result = basic_salary / 24  # 15 days / 30 days / 12 months
        else:
            result = basic_salary / 12  # 30 days / 30 days / 12 months

        return self.company_id.currency_id.round(result)

    def _l10n_om_get_years_of_service(self, start_date, end_date):
        """Calculate years of service as a decimal value."""
        if not start_date or not end_date:
            return 0
        worked_duration = relativedelta(end_date, start_date)
        # Add 1 day as per standard GCC calculation practice
        worked_duration += relativedelta(days=1)
        # Calculate fractional years precisely
        next_month = (end_date + relativedelta(months=1)).replace(day=1)
        last_day_of_month = (next_month - end_date.replace(day=1)).days
        total_years = worked_duration.years + (worked_duration.months / 12) + ((worked_duration.days / last_day_of_month) / 12)
        return total_years
