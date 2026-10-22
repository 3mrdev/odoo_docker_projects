# -*- coding: utf-8 -*-

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLogspaceProviderRegistrationHttp(HttpCase):

    def test_documents_step_renders_a_single_guarded_submit(self):
        """Item 3: the step-4 Next button must be hivable by the JS guard.

        LogspaceProviderDocuments binds `.logspace-provider-documents-form` and
        rewrites `.logspace-provider-documents-label` - so the form needs the
        hook class and the button must be the form's ONLY submit target
        (a second one would also be disabled on submit, or the guard would
        restore the wrong label).
        """
        self.authenticate(None, None)
        response = self.url_open('/logspace/provider/register/4')
        self.assertEqual(response.status_code, 200, response.text[:500])

        html = response.text
        self.assertIn('logspace-provider-documents-form', html)

        form_html = html.split('logspace-provider-documents-form', 1)[1].split('</form>', 1)[0]
        self.assertEqual(form_html.count('type="submit"'), 1, form_html[-500:])
        self.assertIn('logspace-provider-documents-label', form_html)
        self.assertIn('Next: Review', form_html)
