from odoo import Command
from lxml import etree

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLogspaceTranslations(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        arabic = cls.env['res.lang']._activate_lang('ar_001')
        cls.env['ir.module.module'].search([
            ('name', '=', 'appness_logspace'),
        ])._update_translations(filter_lang='ar_001', overwrite=True)
        cls.env.ref('website.default_website').write({
            'language_ids': [Command.link(arabic.id)],
        })

    def test_website_serves_arabic_javascript_translations(self):
        self.authenticate(None, None)

        # No explicit module parameter: the website must include Logspace itself.
        response = self.url_open('/website/translations?lang=ar_001', timeout=60)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['lang_parameters']['direction'], 'rtl')
        messages = {
            message['id']: message['string']
            for message in data['modules']['appness_logspace']['messages']
        }
        self.assertEqual(messages['All Vehicle Types'], 'جميع أنواع المركبات')
        self.assertEqual(messages['Verifying...'], 'جارٍ التحقق...')

    def test_search_page_renders_in_arabic_and_english(self):
        self.authenticate(None, None)
        response = self.url_open('/ar/logspace', timeout=60)
        self.assertEqual(response.status_code, 200)
        self.assertIn('dir="rtl"', response.text)
        self.assertIn('اعثر على المركبة المناسبة لنقل أغراضك', response.text)

        response = self.url_open('/en/logspace', timeout=60)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Find the Perfect Vehicle for Your Move', response.text)

    def test_provider_form_buttons_and_tabs_are_translated(self):
        view = self.env.ref('appness_logspace.view_res_partner_provider_form')
        result = self.env['res.partner'].with_context(lang='ar_001').get_view(
            view_id=view.id, view_type='form',
        )
        arch = etree.fromstring(result['arch'].encode())
        self.assertEqual(arch.xpath('//div[@name="button_box"]//field/@string'), [
            'المركبات', 'الأسطول', 'التسعير', 'الفترات الزمنية',
            'التعليمات', 'الإضافات', 'المستندات',
        ])
        self.assertEqual(arch.xpath('//notebook/page/@string'), [
            'جهات الاتصال', 'السائقون', 'بيانات عامة', 'المركبات',
            'مصفوفة الأسعار', 'إضافات نوع المركبة', 'ملاحظات',
        ])
        self.assertEqual(
            self.env.ref('appness_logspace.module_category_logspace')
            .with_context(lang='ar_001').name,
            'Logspace',
        )


@tagged('post_install', '-at_install')
class TestLogspaceMenuVisibility(TransactionCase):
    def test_configuration_and_support_are_admin_only(self):
        Menu = self.env['ir.ui.menu']
        roots = (
            self.env.ref('appness_logspace.menu_logspace_configuration')
            | self.env.ref('appness_logspace.menu_logspace_support')
        )
        protected_ids = set(Menu.search([('id', 'child_of', roots.ids)]).ids)
        for role, group in (
            ('internal', 'base.group_user'),
            ('provider', 'appness_logspace.group_logspace_provider'),
            ('admin', 'appness_logspace.group_logspace_admin'),
        ):
            with self.subTest(role=role):
                user = self.env['res.users'].with_context(no_reset_password=True).create({
                    'name': 'Menu Visibility ' + role,
                    'login': 'logspace.menu.' + role + '@example.com',
                    'group_ids': [Command.set([self.env.ref(group).id])],
                })
                visible = Menu.with_user(user)._visible_menu_ids()
                if role == 'admin':
                    self.assertTrue(set(roots.ids) <= visible)
                else:
                    self.assertFalse(protected_ids & visible)

    def test_contact_roles_menu_is_archived(self):
        self.assertFalse(
            self.env.ref('appness_logspace.menu_logspace_contact_roles').active,
        )
