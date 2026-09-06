# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

from . import controllers
from . import models

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    """Create the standard OMPay provider record when the module is installed."""
    setup_provider(env, 'ompay')


def uninstall_hook(env):
    """Restore the provider selection when the module is uninstalled."""
    reset_payment_provider(env, 'ompay')
