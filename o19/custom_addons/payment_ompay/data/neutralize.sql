-- Clear OMPay credentials when Odoo neutralizes a copied database.
UPDATE payment_provider
   SET ompay_api_key = NULL,
       ompay_api_secret = NULL
 WHERE code = 'ompay';
