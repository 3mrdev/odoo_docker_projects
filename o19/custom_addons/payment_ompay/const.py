# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

"""Constants for the fixed, server-to-server OMPay integration surface."""

API_URLS = {
    'test': 'https://api.sandbox.truepay.ompay.om',
    'enabled': 'https://api.truepay.ompay.om',
}

BANK_HOSTED_ENDPOINT = '/api/v1/transactions/bank-hosted'
INQUIRY_ENDPOINT = '/api/v1/transactions/inquiry'
ALLOWED_ENDPOINTS = frozenset((BANK_HOSTED_ENDPOINT, INQUIRY_ENDPOINT))

DEFAULT_PAYMENT_METHOD_CODES = {'card'}
SUPPORTED_CURRENCIES = {'OMR'}
OMR_DECIMAL_PLACES = 3

RETURN_INQUIRY_COOLDOWN_SECONDS = 30
RECONCILIATION_MIN_AGE_MINUTES = 2
RECONCILIATION_COOLDOWN_MINUTES = 5
RECONCILIATION_BATCH_SIZE = 50

# The payment logger masks values for these keys should a future diagnostic log use them.
SENSITIVE_KEYS = {
    'ompay_api_key',
    'ompay_api_secret',
    'OMPAY-API-Key',
    'OMPAY-API-Secret',
}

PENDING_STATUSES = {'PENDING', 'PROCESSING'}
SUCCESSFUL_STATUS = 'SUCCESSFUL'
FAILED_STATUS = 'FAILED'
