# Surgical Plan: Demo Data Enrichment for appness_logspace_mockup2

## Overview
Enrich demo data to support pagination demo (>10 search results), migrate all providers from Saudi to Oman addresses, uncomment and add timeframes, add more addon assignments, and fix price matrix to use valid Oman zones.

---

## File Change Manifest

| # | File | Action |
|---|------|--------|
| 1 | `demo_data/demo_providers.xml` | **REWRITE** - Update 3 existing + 5 contacts + add 9 new providers + 9 contacts + fleet summaries + timeframes + instructions + addons |
| 2 | `demo_data/demo_vehicles.xml` | **REWRITE** - Update 8 existing vehicles + add 12 new vehicles |
| 3 | `demo_data/demo_price_matrix.xml` | **REWRITE** - Replace all old zones with valid Oman zones, add entries for all 12 providers |
| 4 | `__manifest__.py` | **EDIT** - Uncomment `demo_price_matrix.xml` line |

---

## Part A: New Provider Partners (9 new, all approved)

All new providers use Oman addresses, Oman phone (+968), .om emails.

### Provider Naming Convention
XML ID pattern: `partner_<shortname>`

| # | XML ID | Name | City | Street | Phone | Email | Years | Fee% |
|---|--------|------|------|--------|-------|-------|-------|------|
| 1 | `partner_muscat_cargo` | Muscat Cargo LLC | Muscat | Al Noor Street, Ruwi, Building 45 | +968 24 123 456 | info@muscatcargo.om | 5_10 | 0.10 |
| 2 | `partner_seeb_freight` | Seeb Freight Solutions | Seeb | Airport Heights Road, Block 7 | +968 24 567 890 | ops@seebfreight.om | 3_5 | 0.12 |
| 3 | `partner_bousher_haulage` | Bousher Haulage Co | Bousher | Al Ghubra North, Street 33 | +968 24 234 567 | contact@bousherhaulage.om | more_10 | 0.08 |
| 4 | `partner_gulf_express` | Gulf Express Transport | Muttrah | Corniche Road, Al Dahir Building | +968 24 678 901 | booking@gulfexpress.om | 5_10 | 0.11 |
| 5 | `partner_oman_fleet` | Oman Fleet Services | Al Amrat | Al Amrat Main Street, Unit 12 | +968 24 345 678 | service@omanfleet.om | 1_2 | 0.15 |
| 6 | `partner_sohar_logistics` | Sohar Logistics Partners | Sohar | Port Road, Industrial Estate | +968 26 456 789 | admin@soharlogistics.om | more_10 | 0.09 |
| 7 | `partner_nizwa_transport` | Nizwa Desert Transport | Nizwa | Al Aqr Street, Near Fort | +968 25 567 890 | dispatch@nizwatransport.om | 3_5 | 0.10 |
| 8 | `partner_dhofar_freight` | Dhofar Coastal Freight | Salalah | Al Haffa District, Block 3 | +968 23 678 901 | info@dhofarfreight.om | 5_10 | 0.12 |
| 9 | `partner_barka_movers` | Barka Movers LLC | Barka | Al Batinah Expressway, Plot 88 | +968 26 789 012 | hello@barkamovers.om | 1_2 | 0.14 |

### Common Fields for All New Providers
```xml
<field name="is_company">True</field>
<field name="is_provider">True</field>
<field name="state">approved</field>
<field name="is_approved_provider">True</field>
<field name="country_id" ref="base.om"/>
<field name="approval_date" eval="(datetime.now() - timedelta(days=N)).strftime('%Y-%m-%d')"/>
```
Use N = 5, 8, 12, 15, 20, 25, 30, 35, 40 (staggered approval dates).

---

## Part B: Update 3 Existing Providers (Saudi → Oman)

### partner_abc_logistics
| Field | Old | New |
|-------|-----|-----|
| phone | +966 50 123 4567 | +968 24 800 1001 |
| email | contact@abclogistics.sa | contact@abclogistics.om |
| city | Riyadh | Muscat |
| street | King Fahd Road, Building 123 | Al Khoudh, Street 15, Building A1 |
| website | https://abclogistics.sa | https://abclogistics.om |
| tax_id | 310123456700003 | OM-1234567890 |
| cr_number | 1234567890 | 1234567 |

### partner_fast_truck
| Field | Old | New |
|-------|-----|-----|
| phone | +966 55 987 6543 | +968 24 800 2002 |
| email | info@fasttruck.sa | info@fasttruck.om |
| city | Jeddah | Seeb |
| street | Al Andalus District, Street 45 | Seeb International Road, Block 22 |
| website | https://fasttruck.sa | https://fasttruck.om |
| tax_id | 310987654300001 | OM-9876543210 |
| cr_number | 0987654321 | 9876543 |

### partner_saudi_express → Rename to "Oman Express Transport"
| Field | Old | New |
|-------|-----|-----|
| name | Saudi Express Transport | Oman Express Transport |
| phone | +966 54 456 7890 | +968 24 800 3003 |
| email | operations@saudiexpress.sa | operations@omanexpress.om |
| city | Dammam | Bousher |
| street | King Saud Street, Industrial Area | Al Ghubra South, Warehouse 7 |
| website | https://saudiexpress.sa | https://omanexpress.om |
| tax_id | 310456789000002 | OM-4567890123 |
| cr_number | 4567890123 | 4567890 |

---

## Part C: Update 5 Existing Contacts to Oman

| XML ID | Old Phone | New Phone | Old Email | New Email |
|--------|-----------|-----------|-----------|-----------|
| contact_abc_sales | +966 50 111 2222 | +968 24 810 1001 | ahmed.rashid@abclogistics.sa | ahmed.rashid@abclogistics.om |
| contact_abc_ops | +966 50 333 4444 | +968 24 810 1002 | khalid.omari@abclogistics.sa | khalid.omari@abclogistics.om |
| contact_ftc_dispatch | +966 55 555 6666 | +968 24 820 2001 | fahad@fasttruck.sa | fahad@fasttruck.om |
| contact_ftc_service | +966 55 777 8888 | +968 24 820 2002 | nora@fasttruck.sa | nora@fasttruck.om |
| contact_se_ops | +966 54 999 0000 | +968 24 830 3001 | mohammed@saudiexpress.sa | mohammed@omanexpress.om |

### New Contacts for New Providers (9 contacts, one per provider)

| XML ID | Name | Parent | Function | Phone | Email |
|--------|------|--------|----------|-------|-------|
| contact_mc_ops | Salim Al-Balushi | partner_muscat_cargo | Operations | +968 24 900 1001 | salim@muscatcargo.om |
| contact_sf_dispatch | Yaqoub Al-Harthi | partner_seeb_freight | Dispatcher | +968 24 900 2001 | yaqoub@seebfreight.om |
| contact_bh_manager | Fatma Al-Rashdi | partner_bousher_haulage | Fleet Manager | +968 24 900 3001 | fatma@bousherhaulage.om |
| contact_ge_booking | Ahmed Al-Kindi | partner_gulf_express | Booking Agent | +968 24 900 4001 | ahmed.k@gulfexpress.om |
| contact_of_service | Khalfan Al-Habsi | partner_oman_fleet | Service Lead | +968 24 900 5001 | khalfan@omanfleet.om |
| contact_sl_admin | Said Al-Shuaili | partner_sohar_logistics | Admin | +968 26 900 6001 | said@soharlogistics.om |
| contact_nt_dispatch | Muna Al-Nabhani | partner_nizwa_transport | Dispatcher | +968 25 900 7001 | muna@nizwatransport.om |
| contact_df_ops | Hussain Al-Mashani | partner_dhofar_freight | Operations | +968 23 900 8001 | hussain@dhofarfreight.om |
| contact_bm_coord | Asma Al-Riyami | partner_barka_movers | Coordinator | +968 26 900 9001 | asma@barkamovers.om |

---

## Part D: Vehicles (Update existing + Add new)

### Update 8 Existing Vehicles (move to om_zone_seeb)
| XML ID | Old zone_id | New zone_id |
|--------|-------------|-------------|
| vehicle_abc_1 | om_zone_seeb | **keep om_zone_seeb** (already correct!) |
| vehicle_abc_2 | om_zone_bousher | om_zone_seeb |
| vehicle_abc_3 | om_zone_muttrah | om_zone_seeb |
| vehicle_ftc_1 | om_zone_al_amrat | om_zone_seeb |
| vehicle_ftc_2 | om_zone_quriyat | om_zone_seeb |
| vehicle_se_1 | om_zone_sohar_city | om_zone_seeb |
| vehicle_se_2 | om_zone_saham | om_zone_seeb |
| vehicle_se_3 | om_zone_shinas | om_zone_seeb |

**ALL existing vehicles should be moved to om_zone_seeb** to ensure they show up in search results for that zone.

### Add 12 New Vehicles (one flatbed_3t per new provider + extras)

For search demo: each new provider needs at least one `flatbed_3t` vehicle in `om_zone_seeb`.

| XML ID | Name | provider_id | vehicle_type_id | plate_number | zone_id |
|--------|------|-------------|-----------------|--------------|---------|
| vehicle_mc_1 | Muscat Mover 1 | partner_muscat_cargo | vehicle_type_flatbed_3t | MC-1001 | om_zone_seeb |
| vehicle_sf_1 | Seeb Speedster | partner_seeb_freight | vehicle_type_flatbed_3t | SF-2001 | om_zone_seeb |
| vehicle_bh_1 | Bousher Bull | partner_bousher_haulage | vehicle_type_flatbed_3t | BH-3001 | om_zone_seeb |
| vehicle_ge_1 | Gulf Runner | partner_gulf_express | vehicle_type_flatbed_3t | GE-4001 | om_zone_seeb |
| vehicle_of_1 | Fleet Cruiser | partner_oman_fleet | vehicle_type_flatbed_3t | OF-5001 | om_zone_seeb |
| vehicle_sl_1 | Sohar Carrier | partner_sohar_logistics | vehicle_type_flatbed_3t | SL-6001 | om_zone_seeb |
| vehicle_nt_1 | Nizwa Navigator | partner_nizwa_transport | vehicle_type_flatbed_3t | NT-7001 | om_zone_seeb |
| vehicle_df_1 | Dhofar Hauler | partner_dhofar_freight | vehicle_type_flatbed_3t | DF-8001 | om_zone_seeb |
| vehicle_bm_1 | Barka Box Truck | partner_barka_movers | vehicle_type_flatbed_3t | BM-9001 | om_zone_seeb |
| vehicle_mc_2 | Muscat Mover 2 | partner_muscat_cargo | vehicle_type_covered_3t | MC-1002 | om_zone_bousher |
| vehicle_ge_2 | Gulf Van | partner_gulf_express | vehicle_type_van | GE-4002 | om_zone_muttrah |
| vehicle_sl_2 | Sohar Heavy | partner_sohar_logistics | vehicle_type_flatbed_5t | SL-6002 | om_zone_sohar_city |

All vehicles: `<field name="is_active">True</field>`

---

## Part E: Price Matrix (COMPLETE REWRITE)

### Critical: Fix Non-Existent Zone References
All old entries reference `zone_downtown`, `zone_airport`, `zone_industrial`, `zone_business`, `zone_residential`, `zone_metro`, `zone_suburb`, `zone_port`, `zone_coastal`, `zone_northern`, `zone_tech_park` — NONE of these exist!

### Primary Demo Route: om_zone_seeb → om_zone_bousher (vehicle_type_flatbed_3t)
This is THE key route for pagination demo. Need 12 providers (3 existing + 9 new) all with a price matrix for this exact route+type.

| XML ID | provider_id | vehicle_type_id | zone_from_id | zone_to_id | distance_km | provider_price |
|--------|-------------|-----------------|--------------|------------|-------------|----------------|
| price_abc_seeb_bousher | partner_abc_logistics | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 75.0 |
| price_ftc_seeb_bousher | partner_fast_truck | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 80.0 |
| price_se_seeb_bousher | partner_saudi_express | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 70.0 |
| price_mc_seeb_bousher | partner_muscat_cargo | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 72.0 |
| price_sf_seeb_bousher | partner_seeb_freight | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 78.0 |
| price_bh_seeb_bousher | partner_bousher_haulage | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 68.0 |
| price_ge_seeb_bousher | partner_gulf_express | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 85.0 |
| price_of_seeb_bousher | partner_oman_fleet | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 90.0 |
| price_sl_seeb_bousher | partner_sohar_logistics | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 65.0 |
| price_nt_seeb_bousher | partner_nizwa_transport | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 77.0 |
| price_df_seeb_bousher | partner_dhofar_freight | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 82.0 |
| price_bm_seeb_bousher | partner_barka_movers | vehicle_type_flatbed_3t | om_zone_seeb | om_zone_bousher | 18.0 | 88.0 |

**Result: 12 providers × 1 route × 1 vehicle type = 12 search results → triggers pagination (per_page=10)**

### Additional Routes (using valid Oman zones)

**Route: om_zone_seeb → om_zone_muttrah (flatbed_3t)** - 6 providers
| XML ID | provider_id | provider_price |
|--------|-------------|----------------|
| price_abc_seeb_muttrah | partner_abc_logistics | 95.0 |
| price_mc_seeb_muttrah | partner_muscat_cargo | 92.0 |
| price_bh_seeb_muttrah | partner_bousher_haulage | 88.0 |
| price_ge_seeb_muttrah | partner_gulf_express | 100.0 |
| price_sl_seeb_muttrah | partner_sohar_logistics | 85.0 |
| price_df_seeb_muttrah | partner_dhofar_freight | 97.0 |

**Route: om_zone_seeb → om_zone_al_amrat (flatbed_3t)** - 4 providers
| XML ID | provider_id | provider_price |
|--------|-------------|----------------|
| price_ftc_seeb_amrat | partner_fast_truck | 60.0 |
| price_se_seeb_amrat | partner_saudi_express | 55.0 |
| price_sf_seeb_amrat | partner_seeb_freight | 62.0 |
| price_nt_seeb_amrat | partner_nizwa_transport | 58.0 |

**Route: om_zone_bousher → om_zone_muttrah (covered_3t)** - 4 providers
| XML ID | provider_id | provider_price |
|--------|-------------|----------------|
| price_abc_bousher_muttrah | partner_abc_logistics | 50.0 |
| price_mc_bousher_muttrah | partner_muscat_cargo | 48.0 |
| price_ge_bousher_muttrah | partner_gulf_express | 55.0 |
| price_of_bousher_muttrah | partner_oman_fleet | 52.0 |

**Route: om_zone_seeb → om_zone_quriyat (flatbed_5t)** - 3 providers
| XML ID | provider_id | vehicle_type_id | provider_price |
|--------|-------------|-----------------|----------------|
| price_ftc_seeb_quriyat | partner_fast_truck | vehicle_type_flatbed_5t | 120.0 |
| price_sl_seeb_quriyat | partner_sohar_logistics | vehicle_type_flatbed_5t | 115.0 |
| price_df_seeb_quriyat | partner_dhofar_freight | vehicle_type_flatbed_5t | 125.0 |

**Route: om_zone_seeb → om_zone_bousher (van)** - 3 providers
| XML ID | provider_id | vehicle_type_id | provider_price |
|--------|-------------|-----------------|----------------|
| price_abc_seeb_bousher_van | partner_abc_logistics | vehicle_type_van | 40.0 |
| price_ge_seeb_bousher_van | partner_gulf_express | vehicle_type_van | 45.0 |
| price_of_seeb_bousher_van | partner_oman_fleet | vehicle_type_van | 42.0 |

**Route: om_zone_seeb → om_zone_bousher (refrigerated)** - 2 providers
| XML ID | provider_id | vehicle_type_id | provider_price |
|--------|-------------|-----------------|----------------|
| price_se_seeb_bousher_ref | partner_saudi_express | vehicle_type_refrigerated | 130.0 |
| price_mc_seeb_bousher_ref | partner_muscat_cargo | vehicle_type_refrigerated | 125.0 |

**Total: 12 + 6 + 4 + 4 + 3 + 3 + 2 = 34 price matrix entries**

---

## Part F: Time Frames (Uncomment + Rewrite with Many2many)

The old commented-out timeframes use `time_start`/`time_end`/`is_pickup`/`is_dropoff` fields which NO LONGER EXIST. The new model uses:
- `partner_id` → res.partner
- `vehicle_type_id` → logspace.vehicle.type
- `time_slot_ids` → Many2many to logspace.time.slot (morning, afternoon, evening)
- **UNIQUE constraint**: (partner_id, vehicle_type_id)

### For 3 Existing Providers (uncomment/rewrite)

| XML ID | partner_id | vehicle_type_id | time_slot_ids |
|--------|------------|-----------------|---------------|
| tf_abc_flatbed | partner_abc_logistics | vehicle_type_flatbed_3t | morning, afternoon |
| tf_abc_covered | partner_abc_logistics | vehicle_type_covered_3t | morning, afternoon, evening |
| tf_abc_van | partner_abc_logistics | vehicle_type_van | morning, afternoon, evening |
| tf_ftc_flatbed5 | partner_fast_truck | vehicle_type_flatbed_5t | morning, afternoon |
| tf_ftc_flatbed3 | partner_fast_truck | vehicle_type_flatbed_3t | morning, afternoon, evening |
| tf_se_flatbed5 | partner_saudi_express | vehicle_type_flatbed_5t | morning |
| tf_se_refrigerated | partner_saudi_express | vehicle_type_refrigerated | morning, evening |
| tf_se_covered | partner_saudi_express | vehicle_type_covered_3t | morning, afternoon |

### For 9 New Providers (all with flatbed_3t + some with secondary types)

| XML ID | partner_id | vehicle_type_id | time_slot_ids |
|--------|------------|-----------------|---------------|
| tf_mc_flatbed | partner_muscat_cargo | vehicle_type_flatbed_3t | morning, afternoon, evening |
| tf_mc_covered | partner_muscat_cargo | vehicle_type_covered_3t | morning, afternoon |
| tf_sf_flatbed | partner_seeb_freight | vehicle_type_flatbed_3t | morning, afternoon |
| tf_bh_flatbed | partner_bousher_haulage | vehicle_type_flatbed_3t | morning, afternoon, evening |
| tf_ge_flatbed | partner_gulf_express | vehicle_type_flatbed_3t | morning, afternoon |
| tf_ge_van | partner_gulf_express | vehicle_type_van | morning, afternoon, evening |
| tf_of_flatbed | partner_oman_fleet | vehicle_type_flatbed_3t | morning, afternoon, evening |
| tf_sl_flatbed | partner_sohar_logistics | vehicle_type_flatbed_3t | morning, afternoon |
| tf_sl_flatbed5 | partner_sohar_logistics | vehicle_type_flatbed_5t | morning |
| tf_nt_flatbed | partner_nizwa_transport | vehicle_type_flatbed_3t | morning, afternoon |
| tf_df_flatbed | partner_dhofar_freight | vehicle_type_flatbed_3t | morning, afternoon, evening |
| tf_bm_flatbed | partner_barka_movers | vehicle_type_flatbed_3t | morning, afternoon |

### XML Pattern for time_slot_ids (Many2many)
```xml
<record id="tf_mc_flatbed" model="logspace.provider.time.frame">
    <field name="partner_id" ref="partner_muscat_cargo"/>
    <field name="vehicle_type_id" ref="vehicle_type_flatbed_3t"/>
    <field name="time_slot_ids" eval="[(6, 0, [ref('time_slot_morning'), ref('time_slot_afternoon'), ref('time_slot_evening')])]"/>
</record>
```

**Total: 8 + 12 = 20 time frame records**

---

## Part G: Addon Assignments

### Existing 5 (keep as-is, they use valid references)

### New Addon Assignments for New Providers

Each new provider gets 2-3 addon assignments for their vehicle types:

| XML ID | provider_id | vehicle_type_id | addon_id | provider_price |
|--------|-------------|-----------------|----------|----------------|
| addon_mc_gps | partner_muscat_cargo | vehicle_type_flatbed_3t | addon_gps | 10.0 |
| addon_mc_loading | partner_muscat_cargo | vehicle_type_flatbed_3t | addon_loading | 22.0 |
| addon_mc_insurance | partner_muscat_cargo | vehicle_type_flatbed_3t | addon_insurance | 32.0 |
| addon_sf_express | partner_seeb_freight | vehicle_type_flatbed_3t | addon_express | 48.0 |
| addon_sf_helper | partner_seeb_freight | vehicle_type_flatbed_3t | addon_helper | 38.0 |
| addon_bh_loading | partner_bousher_haulage | vehicle_type_flatbed_3t | addon_loading | 20.0 |
| addon_bh_unloading | partner_bousher_haulage | vehicle_type_flatbed_3t | addon_unloading | 20.0 |
| addon_bh_protection | partner_bousher_haulage | vehicle_type_flatbed_3t | addon_protection | 12.0 |
| addon_ge_gps | partner_gulf_express | vehicle_type_flatbed_3t | addon_gps | 8.0 |
| addon_ge_insurance | partner_gulf_express | vehicle_type_flatbed_3t | addon_insurance | 35.0 |
| addon_ge_express | partner_gulf_express | vehicle_type_van | addon_express | 45.0 |
| addon_of_loading | partner_oman_fleet | vehicle_type_flatbed_3t | addon_loading | 25.0 |
| addon_of_helper | partner_oman_fleet | vehicle_type_flatbed_3t | addon_helper | 40.0 |
| addon_sl_gps | partner_sohar_logistics | vehicle_type_flatbed_3t | addon_gps | 10.0 |
| addon_sl_protection | partner_sohar_logistics | vehicle_type_flatbed_3t | addon_protection | 15.0 |
| addon_sl_insurance | partner_sohar_logistics | vehicle_type_flatbed_5t | addon_insurance | 30.0 |
| addon_nt_loading | partner_nizwa_transport | vehicle_type_flatbed_3t | addon_loading | 18.0 |
| addon_nt_unloading | partner_nizwa_transport | vehicle_type_flatbed_3t | addon_unloading | 18.0 |
| addon_df_express | partner_dhofar_freight | vehicle_type_flatbed_3t | addon_express | 50.0 |
| addon_df_gps | partner_dhofar_freight | vehicle_type_flatbed_3t | addon_gps | 12.0 |
| addon_df_helper | partner_dhofar_freight | vehicle_type_flatbed_3t | addon_helper | 35.0 |
| addon_bm_loading | partner_barka_movers | vehicle_type_flatbed_3t | addon_loading | 22.0 |
| addon_bm_protection | partner_barka_movers | vehicle_type_flatbed_3t | addon_protection | 14.0 |

**Total: 5 existing + 23 new = 28 addon assignments**

---

## Part H: Fleet Summaries for New Providers

| XML ID | partner_id | vehicle_type_id | fleet_count | capacity_tons | dimensions |
|--------|------------|-----------------|-------------|---------------|------------|
| fleet_mc_flatbed | partner_muscat_cargo | vehicle_type_flatbed_3t | 6 | 3.0 | 600 x 240 x 220 cm |
| fleet_mc_covered | partner_muscat_cargo | vehicle_type_covered_3t | 4 | 3.0 | 550 x 230 x 210 cm |
| fleet_mc_refrig | partner_muscat_cargo | vehicle_type_refrigerated | 2 | 2.5 | 550 x 220 x 200 cm |
| fleet_sf_flatbed | partner_seeb_freight | vehicle_type_flatbed_3t | 5 | 3.0 | 600 x 240 x 220 cm |
| fleet_bh_flatbed | partner_bousher_haulage | vehicle_type_flatbed_3t | 8 | 3.0 | 600 x 240 x 220 cm |
| fleet_ge_flatbed | partner_gulf_express | vehicle_type_flatbed_3t | 4 | 3.0 | 600 x 240 x 220 cm |
| fleet_ge_van | partner_gulf_express | vehicle_type_van | 6 | 1.0 | 300 x 180 x 150 cm |
| fleet_of_flatbed | partner_oman_fleet | vehicle_type_flatbed_3t | 3 | 3.0 | 600 x 240 x 220 cm |
| fleet_of_van | partner_oman_fleet | vehicle_type_van | 5 | 1.0 | 300 x 180 x 150 cm |
| fleet_sl_flatbed | partner_sohar_logistics | vehicle_type_flatbed_3t | 7 | 3.0 | 600 x 240 x 220 cm |
| fleet_sl_flatbed5 | partner_sohar_logistics | vehicle_type_flatbed_5t | 4 | 5.0 | 750 x 250 x 240 cm |
| fleet_nt_flatbed | partner_nizwa_transport | vehicle_type_flatbed_3t | 4 | 3.0 | 600 x 240 x 220 cm |
| fleet_df_flatbed | partner_dhofar_freight | vehicle_type_flatbed_3t | 5 | 3.0 | 600 x 240 x 220 cm |
| fleet_df_flatbed5 | partner_dhofar_freight | vehicle_type_flatbed_5t | 3 | 5.0 | 750 x 250 x 240 cm |
| fleet_bm_flatbed | partner_barka_movers | vehicle_type_flatbed_3t | 3 | 3.0 | 600 x 240 x 220 cm |
| fleet_bm_van | partner_barka_movers | vehicle_type_van | 4 | 1.0 | 300 x 180 x 150 cm |

**Total: 8 existing + 16 new = 24 fleet summaries**

---

## Part I: Special Instructions for New Providers

| XML ID | partner_id | vehicle_type_id | Instructions Summary |
|--------|------------|-----------------|---------------------|
| instruction_mc_flatbed | partner_muscat_cargo | vehicle_type_flatbed_3t | All trucks equipped with tie-down straps and tarpaulin covers. Max load height 2.2m. |
| instruction_mc_covered | partner_muscat_cargo | vehicle_type_covered_3t | Weather-sealed cargo area. Suitable for electronics and paper goods. |
| instruction_sf_flatbed | partner_seeb_freight | vehicle_type_flatbed_3t | GPS-tracked fleet. Loading assistance included. Same-day booking available. |
| instruction_bh_flatbed | partner_bousher_haulage | vehicle_type_flatbed_3t | Largest flatbed fleet in Bousher area. Hydraulic tailgate on all vehicles. |
| instruction_ge_flatbed | partner_gulf_express | vehicle_type_flatbed_3t | Express booking available. Driver assistance for loads up to 300kg included. |
| instruction_ge_van | partner_gulf_express | vehicle_type_van | Ideal for small deliveries. Air-conditioned cargo area. |
| instruction_of_flatbed | partner_oman_fleet | vehicle_type_flatbed_3t | Budget-friendly option. Basic loading assistance available. |
| instruction_sl_flatbed | partner_sohar_logistics | vehicle_type_flatbed_3t | Industrial-grade vehicles. Suitable for construction materials. |
| instruction_sl_flatbed5 | partner_sohar_logistics | vehicle_type_flatbed_5t | Heavy haulage specialists. Crane loading available at Sohar port. |
| instruction_nt_flatbed | partner_nizwa_transport | vehicle_type_flatbed_3t | Mountain route specialists. All drivers experienced with Ad Dakhiliyah terrain. |
| instruction_df_flatbed | partner_dhofar_freight | vehicle_type_flatbed_3t | Coastal route experts. Salt-air resistant equipment. |
| instruction_bm_flatbed | partner_barka_movers | vehicle_type_flatbed_3t | Furniture protection pads included. Assembly/disassembly service available. |

All with `<field name="is_active">True</field>`

---

## Part J: __manifest__.py Change

**Line 42 — Uncomment:**
```python
# BEFORE:
# 'demo_data/demo_price_matrix.xml',

# AFTER:
'demo_data/demo_price_matrix.xml',
```

---

## Execution Order

1. **demo_providers.xml** — Rewrite completely:
   - Update 3 existing provider addresses/phones/emails
   - Update 5 existing contacts
   - Add 9 new providers
   - Add 9 new contacts
   - Add 16 new fleet summaries
   - Add 20 timeframes (8 existing rewritten + 12 new)
   - Add 12 new special instructions
   - Add 23 new addon assignments

2. **demo_vehicles.xml** — Rewrite:
   - Update 8 existing vehicles to om_zone_seeb
   - Add 12 new vehicles

3. **demo_price_matrix.xml** — Rewrite:
   - Replace all 14 old entries (with broken zone refs) → 34 new entries with valid Oman zones

4. **__manifest__.py** — Uncomment demo_price_matrix.xml line

---

## Verification Checklist

- [ ] 12 approved providers with price matrices for (flatbed_3t, om_zone_seeb, om_zone_bousher)
- [ ] Each of those 12 has at least 1 active vehicle in om_zone_seeb
- [ ] Search for (flatbed_3t, om_zone_seeb, om_zone_bousher) returns 12 results → page 1 (10) + page 2 (2)
- [ ] All providers have Oman addresses (+968 phones, .om emails, Oman cities)
- [ ] All contacts have Oman phones/emails
- [ ] Time frames use Many2many to time_slot_ids (NOT old time_start/time_end)
- [ ] No references to non-existent zone XML IDs
- [ ] demo_price_matrix.xml is included in __manifest__.py
- [ ] All unique constraints respected (partner+vehicle_type for timeframes/fleet/instructions; partner+vehicle_type+addon for addons; partner+vehicle_type+zone_from+zone_to for price matrix)

---

## Data Volume Summary

| Data Type | Before | After | Change |
|-----------|--------|-------|--------|
| Approved providers | 3 | 12 | +9 |
| Provider contacts | 5 | 14 | +9 |
| Vehicles | 8 | 20 | +12 |
| Price matrix entries | 0 (commented out) | 34 | +34 |
| Time frames | 0 (commented out) | 20 | +20 |
| Fleet summaries | 8 | 24 | +16 |
| Addon assignments | 5 | 28 | +23 |
| Special instructions | 3 | 15 | +12 |
