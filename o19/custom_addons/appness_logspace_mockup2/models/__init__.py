# -*- coding: utf-8 -*-
from . import ir_ui_menu

# Core Master Data
from . import logspace_zone
from . import logspace_vehicle_type
from . import logspace_addon

# Provider Management (via res.partner extension)
from . import res_partner
from . import hr_job
from . import logspace_provider_fleet_summary
from . import logspace_provider_time_frame
from . import logspace_provider_special_instruction

# Note: logspace.provider model removed - using res.partner with is_provider=True instead

# Fleet & Pricing
from . import logspace_vehicle
from . import logspace_provider_vtype_addon
from . import logspace_price_matrix
from . import logspace_zone_distance

# Order Management (via sale.order extension)
from . import sale_order
from . import logspace_order  # Timeline model

# Customer Features
from . import logspace_rating
from . import logspace_refund

# Support (via helpdesk.ticket extension)
from . import helpdesk_ticket

# Legacy ticket model (keeping for compatibility, should use helpdesk now)
from . import logspace_ticket

# Notifications
from . import logspace_notification

# Payment Integration
from . import logspace_payment
