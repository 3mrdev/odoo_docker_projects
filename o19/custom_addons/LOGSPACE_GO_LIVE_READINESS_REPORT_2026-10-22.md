# Logspace go-live readiness report

**Review date:** 22 October 2026  
**Module:** `custom_addons/appness_logspace` · source version `19.0.2.6.0`  
**Review baseline:** repository `main`, HEAD `1d1bcdf`, including the current uncommitted module changes.

## Decision: not ready for a public production launch

The intended booking and delivery flows have substantial functionality and regression coverage. However, this review reproduced **four critical security defects** that allow unauthorized delivery changes, expose customer verification secrets, permit financial tampering, and expose another provider’s registration documents. These are launch blockers even for a small paid pilot with external providers or drivers.

There are also **eight high-priority findings or release gates** and **six noncritical improvements**. High-priority business and deployment gates can sometimes be satisfied by an explicit, tested operating procedure; the four critical defects require code and permission fixes. A green result from the earlier portal tests does not resolve these new findings.

This is a report and verification task. Application code, access rules, production records, and the demo-data manifest were not changed during this review. Temporary audit records were rolled back. Only this report, its evidence JSON, and its HTML summary are new deliverables.

## What was reviewed and how

Reviewed the active module imports and manifest, controllers, models, record rules and ACLs, provider and order forms, frontend widgets and templates, payment lifecycle, accounting hooks, upload handling, migration scripts, Arabic catalog, and the existing tests. Legacy files such as `models/logspace_provider.py` are not imported by the active model package; they were not treated as live functionality.

The review used temporary customers, providers, drivers, orders, and documents with real Odoo role assignments. Model operations ran as those users in `o19_db_5` and `o19_db_6`, then rolled back. Outbound template mail and invitation methods were mocked. The admin-completion probe mocked bill creation, so it demonstrates unauthorized completion, not an actual payout. The reservation probe used synthetic successful payment transactions; no bank or gateway calls were made.

The main checks below are **ORM/model-level reproductions**, not a claim that a full external penetration test was performed. The affected non-private model methods are callable by authenticated users through Odoo’s dataset API. Odoo explicitly requires public model methods to validate their own caller and inputs; CRUD permissions alone do not secure such methods. See [Odoo 19 security reference](https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html#unsafe-public-methods).

### Environment and test evidence

- The source manifest says `19.0.2.6.0`; `o19_db_5` reports that version with 229 installed modules. The running database, `o19_db_6`, reports `19.0.2.5.0` with 174 modules. The prior surgical menu and translation updates were applied there without a full module upgrade, so the version difference is a release-control gap, not evidence that every recent change is absent.
- The active local database has **no enabled/test payment provider, no approved providers, no active vehicles, and no active price routes**. It is not populated or configured to accept live bookings. `o19_db_5` has OMPay in test mode and a custom provider enabled; that is not proof of production gateway readiness.
- There are **170 test methods** in the current module. Earlier work ran a 165-test suite, resolved two first-render timeouts through focused reruns, and added language checks. The latest surgical change passed four focused tests. This audit did **not** rerun the entire 170-test inventory; it added targeted adversarial verification using temporary fixtures.
- Seventeen distinct probe types were exercised across the two databases. Source hashes and sanitized results are saved in `LOGSPACE_GO_LIVE_READINESS_EVIDENCE_2026-10-22.json` beside this report. A probe marked `allowed` means Odoo permitted the operation; for several probes that is the defect, not a passing security result.
- Production DNS/TLS, real gateway callbacks, real settlement, restore drills, mail delivery, mobile field operations, and the eventual Odoo.sh configuration were not validated by these local checks.

## Critical — fix before external access or live money

### C1 · Customers and drivers can bypass the delivery action authorization

**Severity:** Critical · **Evidence status:** Confirmed on both databases

**Evidence:** A normal customer called `action_start_pickup()` on their order and moved it to `pickup_started`. An assigned portal driver called `action_pickup_completed()` directly, without supplying a code, and reached `pickup_completed`. A customer also reached `order_completed` through the method named `action_admin_complete_order()`; the probe suppressed its bill side effect.

**Cause and impact:** The dedicated driver controller checks ownership and codes, but the other public order actions do not enforce equivalent role checks. `_require_logspace_transition()` checks state, not the caller’s authority. `_get_verification_wizard_action()` treats anyone who is not an internal provider as eligible to bypass the wizard, including customers and portal drivers. Several actions then use `sudo()` to write. Hiding buttons and protecting the driver-specific route do not protect these alternative entry points.

**Required:** Enforce role, assignment, allowed transition, and verification at every public mutation boundary. Restrict admin completion to the actual Logspace Admin role. Keep the privileged implementation private and allow it only after validated authorization. Add denial tests for every public order action as customer, assigned/unassigned driver, provider, and admin.

**Source:** [models/sale_order.py:942](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:942), [models/sale_order.py:965](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:965), [models/sale_order.py:997](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:997), [models/sale_order.py:1022](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:1022), [models/sale_order.py:1118](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:1118)

### C2 · Assigned drivers can read the customer’s verification codes and bearer token

**Severity:** Critical · **Evidence status:** Confirmed on both databases

**Evidence:** `sale.order.read()` as the assigned driver returned both verification-code fields and the customer order’s `access_token`. The driver page can omit the codes while these model reads still succeed.

**Impact:** The driver can obtain the code without the customer. The token also provides a second path: the driver can use an anonymous session to open the token-protected customer tracking page. Fixing only the two code fields would leave that token path open.

**Required:** Reassess whether drivers need raw `sale.order` read access at all; the custom delivery controller already fetches orders under an explicit assignment domain. Expose a limited delivery payload or enforce field-level/customer-specific access that also protects bearer tokens. A field being `readonly=True` is not a read restriction. Test direct `read`/`search_read` and customer-token access, not just rendered driver HTML.

**Source:** [models/sale_order.py:147](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:147), [models/sale_order.py:153](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:153), [security/logspace_security.xml:201](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/security/logspace_security.xml:201), [controllers/portal.py:169](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:169), [tests/test_driver_portal.py:819](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/tests/test_driver_portal.py:819)

### C3 · Providers can alter paid-order financial data through the model API

**Severity:** Critical · **Evidence status:** Confirmed on both databases

**Evidence:** An ordinary provider changed their order’s `payment_status` to `paid`, altered the stored payout quote, and changed a confirmed order line’s unit price. The fixture’s total changed from 100 to 500 through a direct line write.

**Cause and impact:** The order write guard protects `logspace_state` only. The provider ACL grants order write and order-line create/write/unlink. UI read-only fields and hidden totals do not prevent RPC writes to payment summaries, quote snapshots, amounts, taxes, discounts, or line items. The vendor-bill calculation consumes those records.

**Required:** Define a narrow provider edit allowlist; protect payment summaries, quote snapshots, commercial terms, and confirmation metadata server-side. Guard `sale.order.line` create/write/unlink as well as parent-order writes, and restrict edits after a payment attempt starts. Verify payment truth from canonical transactions rather than a client-writable summary. Test forbidden changes on draft, pending-payment, paid, and completed orders.

**Source:** [models/sale_order.py:1298](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:1298), [models/sale_order.py:1138](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:1138), [security/ir.model.access.csv:79](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/security/ir.model.access.csv:79)

### C4 · A provider can read another provider’s bank-document content

**Severity:** Critical · **Evidence status:** Confirmed on the active database; metadata access also reproduced on the test database

**Evidence:** Provider A could read Provider B’s registration document through `documents.document`, including its `datas` field. A direct read of the underlying `ir.attachment` was correctly denied; the Documents route around that restriction still returned content.

**Cause and impact:** Registration uploads are created with `access_internal='view'`. Logspace providers are internal users, so this grants access more widely than the intended provider/admin audience. The Documents `datas` field reads its attachment with elevated access. Explicit access for the owning provider does not cancel the broader internal-sharing permission.

**Required:** Store uploads in a restricted folder or with internal access disabled, and grant explicit access only to the owning provider and authorized reviewers. Repair permissions on existing registration documents, not just newly uploaded files. Test cross-provider reads through Documents fields, previews, and download URLs as well as direct attachments.

**Source:** [controllers/provider.py:304](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/provider.py:304), [models/documents_document.py:6](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/documents_document.py:6)


## High priority — close before accepting public bookings

### H1 · Two existing quotations can become paid bookings for the same vehicle

**Severity:** High · **Evidence status:** Model-level reproduction; no gateway or load test

**Evidence:** Two quotations for one vehicle were each given a synthetic canonical successful transaction and synchronized. Both became confirmed and paid. This was reproduced on both databases; it does not rely on a simultaneous-request race.

Availability is checked during selection/checkout, but the payment route locks the order, not the shared vehicle. Payment confirmation does not revalidate exclusive capacity. An older payment link can therefore remain payable after another booking consumes that vehicle.

**Before launch:** Implement a reservation/capacity policy with atomic vehicle-level enforcement, expiry, and a defined response when payment arrives after expiry or a competing booking. Do not solve this by simply rejecting an already captured payment. Test two independent sessions, stale links, pending authorizations, cancellations, and delayed callbacks.

**Source:** [models/logspace_vehicle.py:54](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_vehicle.py:54), [models/logspace_price_matrix.py:126](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_price_matrix.py:126), [controllers/payment.py:140](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/payment.py:140), [models/sale_order.py:263](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:263), [models/sale_order.py:696](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:696)

### H2 · Refund processing is an administrative status, not a completed money flow

**Severity:** High · **Evidence status:** Confirmed in code; business acceptance required

`action_process()` changes the refund record to `processed` without calling a gateway refund, creating a credit note, reconciling payment, or recording bank settlement. The order payment synchronizer does not derive its `refunded` selection value. Portal requests initially ask for the full order total; the advertised cancellation percentages are not enforced by the refund model. There is no model validation limiting the total of multiple refunds to the amount received.

**Before launch:** Either implement and test the full refund/accounting lifecycle, or explicitly approve a manual refund process with external payment proof, accounting entries, amount limits, duplicate protection, responsible operators, and reconciliation. A status change must not be presented as proof that money was returned. Include guest customers in the refund/support procedure; their guest tracking page does not provide the same authenticated request actions.

**Source:** [models/logspace_refund.py:67](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_refund.py:67), [models/logspace_refund.py:110](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_refund.py:110), [controllers/portal.py:466](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:466), [models/sale_order.py:263](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:263), [models/res_config_settings.py:10](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_config_settings.py:10)

### H3 · Several customer mutation routes disable CSRF verification

**Severity:** High · **Evidence status:** Confirmed route configuration; external exploit not exercised

Profile updates, cancellations, ratings, refund requests, tickets, and notification updates use `csrf=False` on authenticated HTTP routes. Supplying a CSRF token in an HTML template does not protect an endpoint that skips validation. Cookie/SameSite behavior was not used as evidence of a successful attack, and should not be the sole defense.

**Before launch:** Enable Odoo’s CSRF validation and use explicit POST methods for mutations. Keep GET requests read-only. Add tests rejecting absent/invalid tokens while preserving legitimate form submissions.

**Source:** [controllers/portal.py:42](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:42), [controllers/portal.py:319](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:319), [controllers/portal.py:356](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:356), [controllers/portal.py:407](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:407), [controllers/portal.py:465](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:465), [controllers/portal.py:587](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:587)

### H4 · Provider lifecycle authorization is inconsistent with the Logspace Admin role

**Severity:** High · **Evidence status:** Confirmed on both databases

A user holding Logspace Admin, without general system settings rights, was blocked from editing a provider’s platform fee. The write guard recognizes system administrators but omits Logspace Admin; that role also inherits Provider and hits the provider restriction. Conversely, a provider could create an approved provider child record because the protected-field logic runs on write, not on create.

Public lifecycle and account-provisioning helpers also need an explicit role/ownership audit before their `sudo()` work. Cross-provider email modification and login provisioning were tested and correctly denied by record access; this report does not claim that particular takeover works.

**Before launch:** Use a consistent, explicit permission policy for create/write, approval, rejection, suspension, and account creation. Recognize Logspace Admin as intended without granting general Settings rights as a workaround. Add positive admin tests and negative provider/portal tests.

**Source:** [models/res_partner.py:293](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_partner.py:293), [models/res_partner.py:300](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_partner.py:300), [models/res_partner.py:307](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_partner.py:307), [models/res_partner.py:348](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_partner.py:348), [models/res_partner.py:478](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_partner.py:478)

### H5 · Booking requirements and upload limits are not consistently enforced server-side

**Severity:** High · **Evidence status:** Confirmed code gaps; exact required business fields need owner agreement

The authoritative selection validator checks record relationships and prices, but does not require a future pickup date or validate that the selected timeframe is offered. Vehicle availability accepts a missing date. Checkout does not enforce the vehicle type’s required-document list before creating a payable order.

Booking document uploads call `storage.read()` and create sudo attachments without the registration flow’s 20 MB/type checks. Public registration has per-file checks but no module-level quota/rate policy or abandoned-data cleanup. The final registration submission can also move a session draft to pending without revalidating all earlier steps. Infrastructure limits may reduce abuse; they were not verified here.

**Before launch:** Centralize validation for date, slot, contacts/addresses, required documents, and allowed file size/type before payment and final provider submission. Add request/count quotas and a retention/cleanup rule for abandoned temporary uploads and drafts. Cover bypassed browser validation and back-navigation with existing attachments.

**Source:** [controllers/common.py:369](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/common.py:369), [models/logspace_price_matrix.py:126](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_price_matrix.py:126), [models/logspace_vehicle.py:54](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_vehicle.py:54), [controllers/booking.py:133](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/booking.py:133), [controllers/booking.py:359](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/booking.py:359), [controllers/provider.py:449](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/provider.py:449)

### H6 · Settlement, tax treatment, and bill-failure recovery need accounting approval

**Severity:** High · **Evidence status:** Confirmed implementation behavior; financial correctness depends on the agreed settlement contract

Payout is calculated from the customer’s gross total minus commission, then used as the vendor bill’s untaxed line price. Supplier taxes may be applied on that bill. Existing tests deliberately assert this behavior; for example, their taxed quote/add-on case pays 125.85 against a 136.85 customer total, before any vendor-bill purchase tax. This is not automatically a bug, but it needs an approved explanation of who receives/remits each tax and what the provider’s quote includes.

The checkout helper computes tax from product-template taxes, while the eventual sale order uses Odoo’s order tax logic. Tax-inclusive prices, fiscal positions, company taxes, and rounding need reconciliation tests. Completion marks the order complete before bill creation/posting; selected bill failures are logged and swallowed, leaving an order complete with no posted bill or a draft bill and no module-specific recovery queue.

**Before launch:** Approve service/add-on commission and tax examples with the accounting owner; test actual localization, fiscal positions, company currency, and purchase taxes. Define an exception dashboard/retry procedure and demonstrate journal/account configuration and failed-posting recovery.

**Source:** [models/sale_order.py:1138](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:1138), [controllers/common.py:404](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/common.py:404), [controllers/common.py:444](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/common.py:444), [tests/test_provider_bill.py:83](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/tests/test_provider_bill.py:83), [tests/test_provider_bill.py:185](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/tests/test_provider_bill.py:185)

### H7 · There is no verified, configured production release candidate yet

**Severity:** High · **Evidence status:** Observed local release/configuration gate; production hosting not inspected

The running local database has no enabled payment provider, approved providers, active vehicles, or active price routes. Source and installed versions differ, the test and active databases have different installed-module sets, and substantial module work remains uncommitted. Local OMPay test configuration is not evidence of real production callback or settlement success.

The local configuration also has a weak/default database-manager password and does not explicitly set the inspected proxy/database-list/filter/worker options. These observations describe this local environment, not the eventual Odoo.sh deployment. No password values are included in this report.

**Before launch:** Produce one tracked/versioned release; rehearse its upgrade on a staging copy with the intended dependency set. Configure real operating records and payment methods, validate gateway success/failure/timeout/duplicate/delayed callbacks and reconciliation, and demonstrate email delivery. Verify production TLS, privileged-account protection, database exposure, backups including filestore, restore/rollback, monitoring, and capacity. For self-hosting, see the official [deployment guidance](https://www.odoo.com/documentation/18.0/administration/on_premise/deploy.html); on Odoo.sh, verify which controls the platform provides and which remain your responsibility.

**Source:** [__manifest__.py:1](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/__manifest__.py:1), [controllers/payment.py:140](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/payment.py:140), [tests/common.py:8](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/tests/common.py:8)

### H8 · Some portal endpoints bypass their own ownership and visibility rules

**Severity:** High · **Evidence status:** Confirmed by code inspection; HTTP reproduction not performed

Notification updates accept submitted notification IDs, sudo-browse them, and mark them read without filtering by the current user. A user can therefore target another user’s IDs. Ticket list/detail endpoints verify the customer’s order, then sudo-read its tickets without applying `show_to_customer=True` or the intended ticket-recipient rule. A ticket flagged hidden can still be returned through these pages.

The role probes also allowed a portal customer to read an approved provider’s fee percentage. Anonymous-role ORM reads allowed inactive vehicle details and internal matrix prices, but an external anonymous exploit through the generic dataset route was not established (that route requires login). Review public-facing field/ACL exposure separately from controller output.

**Before launch:** Scope notifications to the current recipient before mutation. Apply a shared customer-visible ticket domain in both listing and detail endpoints, and test hidden and cross-recipient records. Keep admin-only access rules in the model as well as the menu.

**Source:** [controllers/portal.py:357](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:357), [controllers/portal.py:657](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:657), [controllers/portal.py:717](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:717), [models/helpdesk_ticket.py:72](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/helpdesk_ticket.py:72)


## Noncritical improvements — plan and control for the first release

### M1 · Arabic coverage still has dynamic English gaps

**Severity:** Medium · **Evidence status:** Noncritical functionality/polish

The catalog and provider form labels are populated, and the brand correction is in place. However, raw selection labels, `.replace('_', ' ').title()` statuses, relative-time strings, phone feedback, and some JavaScript messages still produce English. Settings policy text is stored as a plain configuration parameter, so filling `ar.po` does not translate customized values. Use language-aware selection descriptions, literal extractable translation calls, localized date/time formatting, and translatable policy storage.

**Source:** [controllers/driver.py:82](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/driver.py:82), [controllers/portal.py:357](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:357), [models/sale_order.py:610](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:610), [models/res_config_settings.py:10](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/res_config_settings.py:10), [static/src/js/logspace.js:578](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/static/src/js/logspace.js:578)

### M2 · Money formatting and a tax caption assume fixed precision/rate

**Severity:** Medium · **Evidence status:** Noncritical display/calculation consistency; raise priority if OMR fractional pricing is offered

Frontend summary amounts use `toFixed(2)` and the zone wizard rounds generated prices to two decimals. The inspected OMR configuration uses three decimal places (`rounding=0.001`); these should follow the configured currency instead of a hardcoded precision. A booking-template caption says `Tax (10%)` regardless of the actual tax configuration. Keep the authoritative amount, display precision, and label consistent.

**Source:** [static/src/js/logspace.js:120](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/static/src/js/logspace.js:120), [static/src/js/logspace.js:137](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/static/src/js/logspace.js:137), [wizard/logspace_zone_setup_wizard.py:239](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/wizard/logspace_zone_setup_wizard.py:239), [views/logspace_booking_templates.xml:464](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/views/logspace_booking_templates.xml:464)

### M3 · Search/listing and email delivery will need scale testing

**Severity:** Medium · **Evidence status:** Noncritical for a small controlled workload; no capacity benchmark performed

Search constructs all matches and paginates the resulting Python list; customer and driver order lists can load all orders. Search performs repeated provider/vehicle/availability lookups, while state changes send multiple emails synchronously with `force_send=True`. Introduce bounded server-side queries, batching, and queued delivery where practical; load-test the expected route, vehicle, and order volumes before deciding worker capacity.

**Source:** [controllers/search.py:181](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/search.py:181), [controllers/search.py:281](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/search.py:281), [controllers/common.py:76](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/common.py:76), [controllers/driver.py:123](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/driver.py:123), [models/sale_order.py:620](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:620)

### M4 · Multi-company support is not a verified contract

**Severity:** Medium · **Evidence status:** Noncritical if deployment is explicitly single-company

Vehicles, matrices, and several provider/master records do not carry company isolation fields/rules; selection validation ties currency to the request’s current company. Do not advertise or rely on multi-company isolation without a separate design and test pass. Record a single-company limitation for the first release if that is the intended deployment.

**Source:** [models/logspace_vehicle.py:7](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_vehicle.py:7), [models/logspace_price_matrix.py:7](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_price_matrix.py:7), [models/logspace_price_matrix.py:178](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_price_matrix.py:178)

### M5 · Several master-data options lack matching server constraints or calculations

**Severity:** Medium · **Evidence status:** Noncritical with a controlled, fixed-price catalog

Add-ons expose per-kilometer, per-hour, and per-item pricing types, but checkout consumes their stored price as a flat amount. Either implement those calculations or limit offered add-ons to fixed pricing. Add validation for sensible fee/distance/count/duration ranges and acyclic zone hierarchies. Provider/driver/vehicle selector domains also need model constraints where cross-provider assignment would be invalid; a domain alone is not enforcement.

**Source:** [models/logspace_addon.py:20](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_addon.py:20), [models/logspace_price_matrix.py:197](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_price_matrix.py:197), [models/logspace_zone.py:21](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/logspace_zone.py:21), [models/sale_order.py:28](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/models/sale_order.py:28)


## Lower-priority polish

### M6 · Finish customer-facing operational copy and optional features

**Severity:** Low · **Evidence status:** Noncritical cleanup

Replace placeholder support details, agree the cancellation/estimated-time terms, and remove or finish the Excel export route that currently returns “not implemented yet.” Required terms, file-upload behavior, support-team routing, and driver phone flows need real-user acceptance testing. Confirm how advertised catalog add-ons such as GPS tracking are operationally delivered. Remove unimported legacy model files in a separate cleanup, not as part of urgent security fixes.

**Source:** [controllers/provider.py:506](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/provider.py:506), [controllers/portal.py:622](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/controllers/portal.py:622), [data/data_products.xml:88](/Users/amrabdalkrim/odoo/docker/o19/custom_addons/appness_logspace/data/data_products.xml:88)

## What is already working and worth preserving

- Booking selections and add-ons are resolved against server-side records and prices, with provider/vehicle/route consistency checks. The browser-supplied total is not trusted as payment truth.
- Payment pages use standard Odoo transaction links, token-protected access, compatible provider/method selection, saved-token ownership checks, and an order-level duplicate-attempt lock. Result pages do not themselves mark an order paid.
- Canonical payment synchronization handles pending, failed, partial, and successful payment states, and the confirmation finalizer is intended to be idempotent.
- The dedicated driver controller checks assignment, presents ordered actions, validates codes, rejects blanks, and returns generic errors without echoing expected codes. Driver pages have no-store/no-referrer headers. C1 and C2 are alternative API paths around these controls.
- Cross-provider contact modification and account provisioning were rejected in the audit probes. Existing provider-bill tests also cover another provider’s bill access.
- Registration uploads already have per-file size/type checks, slot-based identity, replacement logic, and concurrency protection. The remaining storage permissions and final validation need work.
- The latest menu changes hide Configuration/Customer Support from nonadmins and archive Contact Roles. Provider smart buttons and tabs have Arabic entries; the previously observed English labels were reproduced as a stale backend-view cache and corrected by refreshing the backend. The brand remains “Logspace.”
- Migration scripts exist for canonical payment links, vehicle categories, provider-bill flags, document slots, and confirming historically paid quotations. They still need rehearsal against the actual release candidate and production-shaped data.

## Recommended completion order

### 1. Close the critical security boundaries

Fix C1–C4 first, with focused negative-role tests and a review of all existing document permissions. Keep financial and customer secrets inaccessible to external provider/driver accounts. Check every public model action and every `sudo()` boundary, not just the paths used by the current UI. Do not open a paid external pilot while these remain.

### 2. Close the paid-booking and operating gates

Resolve H1–H8. Implement capacity reservations and enforce server-side booking requirements. Agree and test the refund and settlement procedures, including tax examples and failure recovery. Complete the admin-role behavior and portal ownership checks. Owners should be named for operational procedures and reconciliation; an undocumented assumption is not an accepted mitigation.

### 3. Validate one production-shaped release

Use a staging database with the intended module set, localization, company/currency, provider, vehicle, pricing, calendar, and gateway configuration. Run the complete regression suite on the final commit and a clean install/upgrade rehearsal. Recheck Arabic/English desktop and mobile flows after translations load. Validate real mail and gateway sandbox behavior, followed by a controlled production smoke test under the payment provider’s procedure. Demonstrate database-plus-filestore restore and a rollback plan before opening traffic.

### 4. Make an explicit launch decision

Go live only when:

- C1–C4 are fixed and their adversarial regression tests deny the unauthorized operations.
- H1–H8 have implementation/test evidence or a documented, approved operating mitigation where manual handling is appropriate.
- The release is tracked, versioned, deployed consistently, and tested with production-shaped dependencies and configuration.
- An authorized customer can book/pay, an approved provider can operate, an assigned driver can finish a delivery using customer-provided codes, accounting can reconcile the payout, and support can complete a refund without bypassing permissions.
- Actual service zones/prices/calendars, support contacts, terms, email, payment methods, monitoring, and recovery procedures are ready.
- Remaining medium/low items have owners and agreed scope limits (for example, single-company and fixed-price add-ons).

## Test additions to prioritize

1. RPC/model denial matrix for every order action, especially completion, cancellation/reset, and administrator shortcuts.
2. Driver secret/token reads and anonymous customer-page access using a driver-obtained token.
3. Provider changes to payment status, quote snapshots, order lines/taxes/discounts, driver assignment, and confirmation metadata.
4. Cross-provider document access through Documents data fields, preview/content routes, and attachments; include historical uploads.
5. Competing booking sessions, stale payment links, delayed callbacks, authorization/capture policy, reservation expiry, and callback retries.
6. Hidden tickets, cross-recipient notification mutations, and missing/invalid CSRF tokens.
7. Required booking data/documents, oversized or unsupported files, malformed IDs, and incomplete provider registration.
8. Genuine Logspace Admin (without general Settings rights), provider creation, approval, suspension/reactivation, and account provisioning.
9. Refund limits/duplicates/partial refunds, credit notes, real payment refund or manual settlement proof, and payout/tax reconciliation.
10. A production-shaped upgrade/rollback rehearsal, complete regression run, mobile UAT, translation checks, and a modest load test.

## Limits of this decision

This report establishes specific application defects and local configuration gaps. It does not certify production infrastructure, legal policy, or accounting treatment. It does not infer that a vulnerability has been exploited. Deployment checks that were not performed are listed as gates, not invented incidents. The recommendation can change after the blocking findings are resolved and the release evidence is reviewed.
