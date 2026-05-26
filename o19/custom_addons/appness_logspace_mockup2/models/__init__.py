# -*- coding: utf-8 -*-

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

# Legacy provider model (keeping for compatibility during transition)
# Can be removed after migration to res.partner
from . import logspace_provider

# Fleet & Pricing
from . import logspace_vehicle
from . import logspace_provider_vtype_addon
from . import logspace_price_matrix

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
