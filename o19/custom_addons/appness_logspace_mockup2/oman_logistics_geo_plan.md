# Offline Geo-Zone Pricing Plan for Odoo 19 Marketplace Logistics

## Goal
Build an offline distance estimation layer for a marketplace logistics module in Odoo 19, where delivery pricing is based on an estimated kilometer distance between origin and destination zones inside Oman.

The solution must:
- avoid any external distance/geocoding API,
- reuse standard Odoo contact/address data as much as possible,
- allow one-time administrative data loading for Oman,
- support a pricing matrix later,
- be easy to extend when the business expands to more cities or countries.

---

## Core idea
Do **not** calculate real road distance.
Instead, introduce a controlled geographic abstraction:

**Country -> State/Governorate -> City -> Zone**

Each address in the system is assigned to a zone. The distance between two zones is an estimated km value stored in a matrix. Pricing is then computed from that zone-to-zone distance.

This is the best fit for an offline system because it is:
- predictable,
- fast,
- fully manageable from Odoo,
- independent of map services,
- good enough for marketplace pricing rules.

---

## Recommended data model strategy

### 1) Reuse standard Odoo address fields
Use the existing contact fields on `res.partner` as the base:
- `country_id`
- `state_id`
- `city` or `city_id` depending on what is already available in your database
- `street`
- `street2`
- `zip`

For logistics pricing, do not rely on street-level precision.
Use these fields only to help assign a partner to a zone.

### 2) Add a custom zone model
Create a new model such as `logistics.zone`.
Suggested fields:
- `name`
- `code`
- `country_id`
- `state_id`
- `city_id` or `city_name`
- `parent_id` if you want hierarchical zones
- `active`
- `sequence`
- `notes`

Purpose:
- represents a delivery area / service zone,
- is the main unit for distance calculation,
- can be linked to one or many partner addresses.

### 3) Add a zone mapping on contacts
Add a field on `res.partner` such as:
- `logistics_zone_id`

This field should be:
- computed or manually assigned,
- optionally editable by users with logistics/admin rights,
- used as the source of truth for pricing.

Recommended behavior:
- default zone is derived from country/state/city,
- manual override is allowed when an address is on a boundary.

### 4) Add a zone distance matrix
Create another model such as `logistics.zone.distance`.
Suggested fields:
- `zone_from_id`
- `zone_to_id`
- `estimated_km`
- `estimated_minutes` if needed later
- `service_type` if you want separate pricing for express/standard
- `active`

This matrix stores the estimated distance between every allowed zone pair.

Important design choice:
- store only one direction if the distance is symmetric,
- or store both directions if the pricing logic may differ.

For simplicity, start with symmetric distance.

### 5) Add pricing rules later on top of the matrix
Create a pricing model such as `logistics.price.rule`.
Possible inputs:
- zone pair or distance band,
- service type,
- vehicle type,
- weight range,
- package size,
- base fee,
- per-km fee,
- minimum fee,
- surcharges.

This keeps distance logic separate from commercial pricing.

---

## Suggested computation flow

### Step 1: Address selection
When a user enters pickup and drop-off addresses:
- each address is linked to a `res.partner` record or a delivery address child contact,
- each address resolves to a `logistics_zone_id`.

### Step 2: Distance lookup
Search the `logistics.zone.distance` table for the matching zone pair.
- If a match exists, use `estimated_km`.
- If no exact pair exists, use fallback rules.

### Step 3: Fallback rules
Use a hierarchy-based fallback when an exact pair is missing:
1. same zone → default short distance,
2. same city but different zone → city-level estimate,
3. same state but different city → state-level estimate,
4. different state → governorate-level estimate,
5. different region with no mapping → manual review or default estimate.

### Step 4: Pricing calculation
Use the distance value in the pricing engine.
Example formula:
- `price = base_fee + (estimated_km * per_km_rate)`
- then apply any weight, service, or express surcharges.

---

## Best implementation approach for Oman

### A) Build an Oman zone hierarchy first
Since the country is fixed to Oman, prepare a one-time administrative dataset for:
- governorates / states,
- major cities,
- service zones inside major cities.

This does not need to be exact road geography.
It only needs to be consistent enough for pricing.

### B) Use coarse-to-fine zoning
Start with a small number of zones:
- Muscat Central
- Muscat Suburbs
- Al Seeb / Bousher / Muttrah style service areas if needed
- Sohar
- Salalah
- Nizwa
- Sur
- Interior/remote zones

Then expand later if the business needs more precision.

### C) Keep manual override available
Some addresses will not fit neatly into automated mapping.
Allow operations staff to manually assign a zone.
This is essential for real logistics operations.

### D) Seed data through import
Prepare a CSV/XML data load for the initial Oman zones and the zone distance matrix.
This is better than hardcoding values in Python.

---

## Technical implementation notes

### Model architecture
Recommended models:
- `logistics.zone`
- `logistics.zone.distance`
- `logistics.price.rule`
- optional helper model for zone assignment history

### Partner integration
On `res.partner`:
- add `logistics_zone_id`
- optionally add `zone_source` (`manual`, `auto`, `imported`)
- optionally add `zone_locked` for validated addresses

### Assignment logic
Implement a helper method like:
- `_compute_logistics_zone()`

The method should attempt zone assignment using:
1. country,
2. state,
3. city,
4. zip,
5. fallback manual selection.

### Performance
Because this is offline and matrix-based:
- use indexed many2one fields,
- cache repeated lookups if needed,
- avoid recomputing zone distance repeatedly inside pricing loops.

### Auditability
Log:
- how a zone was assigned,
- whether it was manual or automatic,
- who changed it,
- when a distance matrix row was edited.

This is useful when pricing questions come from customers.

---

## Data preparation plan

### One-time setup tasks
1. Define Oman countries/states/cities in a clean structure.
2. Create service zones for the operational areas.
3. Map existing customer and vendor delivery addresses to zones.
4. Build the initial zone distance matrix.
5. Validate the matrix with operations staff.
6. Lock the first approved version of the matrix.

### Maintenance tasks
- add new zones when the business expands,
- update estimated distances when routes change operationally,
- keep historical versions if pricing must not change retroactively.

---

## Recommended rules for the first version

Start simple:
- one pickup zone and one drop-off zone produce one estimated km,
- no live map integration,
- no street-level geocoding,
- no external APIs,
- manual maintenance by operations/admin users.

This gives a stable foundation and avoids overengineering.

---

## Deliverables for the developer
The implementation should include:
- Python models,
- security access rules,
- views/forms for zone management,
- importable seed data,
- helper methods for zone assignment,
- helper methods for estimated distance lookup,
- a pricing hook that uses the lookup result.

---

## Acceptance criteria
The feature is complete when:
- every logistics address can be assigned a zone,
- a pickup and drop-off zone produce an estimated km offline,
- the pricing engine can consume that km value,
- admin users can maintain zones and distances without code changes,
- the solution works for Oman without any internet dependency.

---