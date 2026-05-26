from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
import logging

_logger = logging.getLogger(__name__)

class CustodyConfirmationWizard(models.TransientModel):
    _name = 'custody.confirmation.wizard'
    _description = 'Custody Confirmation Wizard'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    custody_decision = fields.Selection(
        [('remain', 'Remain with Custody'), ('return', 'Return Custody')],
        string='Decision'
    )
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    obligations = fields.Text(string='Obligations', readonly=True)

    def confirm(self):
                # Check the decision made
        if self.custody_decision == 'remain':
            # Set the employee's department_id to the selected department
            self.employee_id.department_id = self.department_id
            return True  # Optionally return a success message or action

        elif self.custody_decision == 'return':
            # Raise an error if the decision is to return custody
            raise UserError("Please assign the custodies to another employee first.")
        else:
            self.employee_id.department_id = self.department_id
            return True  # Optionally return a success message or action
        # Logic to handle the confirmation
        # For example, you can update the custody records based on the decision
        #pass

class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        for record in self:
            custody = self.env['hr.custody'].search([('employee', '=', record.employee_id.id)])    
            vehicles = self.env['fleet.vehicle'].search([('driver_id.employee_ids', '=', record.employee_id.id)])
            equipment = self.env['maintenance.equipment'].search([('employee_id', '=', record.employee_id.id)])

            # Prepare messages for each category
            custody_message = '\n'.join(custody.mapped('custody_name')) if custody else ''
            vehicle_message = '\n'.join(vehicles.mapped('name')) if vehicles else ''
            equipment_message = '\n'.join(equipment.mapped('name')) if equipment else ''

            # Construct the error message
            error_message = "This employee has the following obligations:\n"
            if custody_message:
                error_message += f"Custody: {custody_message}\n \n"
            if vehicle_message:
                error_message += f"Vehicles: {vehicle_message}\n \n"
            if equipment_message:
                error_message += f"Equipment: {equipment_message}\n \n"
            
            error_message += "Please assign the custodies to another employee first."      

            # Find the project manager user
            project_manager_group = self.env.ref('fb_wajiz_hr.group_project_manager')
            project_managers = project_manager_group.users
 
            # Raise an error if there are any obligations
            if custody or vehicles or equipment:
                # Notify all project managers related to the employee's department
                for manager_user in project_managers:
                    if manager_user.partner_id:
                        message = f"{record.employee_id.name} has one or more obligations and is marked to be archived. Please assign the custodies to another employee first."
                        # Prepare to send notification
                        notification_ids = [(0, 0, {
                            'res_partner_id': manager_user.partner_id.id,
                            'notification_type': 'inbox'
                        })]
                        
                        # Post the message
                        record.employee_id.parent_id.message_post(
                            message_type="notification",
                            body=message,
                            notification_ids=notification_ids,
                            author_id=2
                        )
                        
                raise ValidationError(error_message)

            # Create a notification for the manager
            if record.employee_id.parent_id:  # Ensure the manager exists and has a user
                # Notify all project managers related to the employee's department
                for manager_user in project_managers:
                    if manager_user.partner_id:
                        message = f"{record.employee_id.name} has been archived. Please prepare for new employee onboarding."

                        # Prepare to send notification
                        notification_ids = [(0, 0, {
                            'res_partner_id': manager_user.partner_id.id,
                            'notification_type': 'inbox'
                        })]
                        
                        # Post the message
                        record.employee_id.parent_id.message_post(
                            message_type="notification",
                            body=message,
                            notification_ids=notification_ids,
                            author_id=2
                        )
        # If no obligations are found, proceed with the departure registration logic
        return super(HrDepartureWizard, self).action_register_departure()
