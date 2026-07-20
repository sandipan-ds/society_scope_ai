# 04_DB_SCHEMA.md

## Purpose

This document defines the primary data structure for the Housing Society AI Assistant project.

The project will use an **Excel workbook as the primary operational data source** for housing society charges and fines. This is intentionally designed for practicality and ease of use, since society admins are far more likely to work comfortably with Excel than with SQL tools.

Excel is the **single source of truth for day-to-day data entry and maintenance tracking**.

A database may be considered later only as a backup or integration layer, but **it is not part of the primary operating model** and should not be required for routine use.

---

## Core decision

The project will use:

- **Excel workbook as the primary data entry and management system**
- **No SQL database for regular operational use**
- **Formula-driven calculations inside Excel**
- **Worksheet-based categorization for maintenance charges and fines**

This design keeps the system accessible to non-technical users and reduces operational friction.

---

## Design goals

The workbook must be designed to meet the following goals:

- Excel is the **single source of truth**
- The workbook is easy for non-technical users to understand and maintain
- Resident data is edited in only one place
- Financial worksheets follow the same structure for consistency
- Maintenance charges are pre-filled automatically
- Fine worksheets default to zero values
- Monthly totals update automatically using formulas
- New fine categories can be added by duplicating an existing fine worksheet
- No manual calculations should be required
- No SQL knowledge should be needed to operate the system

---

## Workbook structure

The workbook should contain the following worksheets:

1. `Residents`
2. `Maintenance Charges`
3. `Parking Violation Fines`
4. `Waste Management Fines`
5. `Pet Policy Fines`
6. `Noise Violation Fines`
7. `Property Damage Fines`
8. `Miscellaneous Fines`

If a new fine category is needed in the future, users should be able to duplicate any existing fine worksheet and rename it without changing the workbook design.

---

## Schema model

The workbook uses **two schema patterns**:

1. A dedicated **master data schema** for the `Residents` worksheet
2. A shared **financial worksheet schema** for `Maintenance Charges` and all fine worksheets

This keeps resident identity management clean while preserving a consistent month-wise financial structure across charges and fines.

---

## Residents (Master Data)

This worksheet is the **master source of truth** for all resident information. Any changes made here must automatically be reflected in every other worksheet.

### Schema

| Flat No. | Owner Name | Resident Name | Occupancy Type | Owner Email | Owner Mobile | Resident Email | Resident Mobile |
| -------- | ---------- | ------------- | -------------- | ----------- | ------------ | -------------- | --------------- |

### Column definitions

- **Flat No.** – Unique flat identifier.
- **Owner Name** – Legal owner of the flat.
- **Resident Name** – Person currently living in the flat.
- **Occupancy Type** – Excel dropdown with only two allowed values:
  - `Owner`
  - `Rental`
- **Owner Email** – Owner's email address.
- **Owner Mobile** – Owner's mobile number.
- **Resident Email** – Resident's email address.
- **Resident Mobile** – Resident's mobile number.

### Auto-fill logic

#### If **Occupancy Type = Owner**

The following fields should automatically populate from the owner's information:

- `Resident Name = Owner Name`
- `Resident Email = Owner Email`
- `Resident Mobile = Owner Mobile`

The user should not need to enter these values manually.

#### If **Occupancy Type = Rental**

The following fields should be entered manually:

- `Resident Name`
- `Resident Email`
- `Resident Mobile`

These values may differ from the owner's details.

### Synchronization

The `Residents` worksheet is the only place where resident information is edited.

Any changes made to:

- `Flat No.`
- `Owner Name`
- `Resident Name`
- `Occupancy Type`
- `Owner Email`
- `Owner Mobile`
- `Resident Email`
- `Resident Mobile`

must automatically update the corresponding information in every other worksheet using Excel formulas or references.

---

## Common financial worksheet schema

The following worksheets must use the same financial column structure:

- `Maintenance Charges`
- `Parking Violation Fines`
- `Waste Management Fines`
- `Pet Policy Fines`
- `Noise Violation Fines`
- `Property Damage Fines`
- `Miscellaneous Fines`

### Schema

| Flat No. | Resident Name | Email | Mobile No. | Jan-26 | Feb-26 | Mar-26 | Apr-26 | May-26 | Jun-26 | Jul-26 | Aug-26 | Sep-26 | Oct-26 | Nov-26 | Dec-26 |
|----------|----------------|-------|------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|

### Requirements

- **Resident Name** should contain both the first name and surname in a single column.
- **Email** should use the resident's email from the `Residents` worksheet.
- **Mobile No.** should use the resident's mobile number from the `Residents` worksheet.
- Every resident should appear in every financial worksheet.

### Synchronization rule

In all financial worksheets, the identity fields should be linked from the `Residents` worksheet using Excel formulas or references so users never need to update resident information manually in multiple places.

At minimum, the following should stay synchronized from `Residents`:

- `Flat No.`
- `Resident Name`
- `Resident Email` mapped into `Email`
- `Resident Mobile` mapped into `Mobile No.`

---

## Master data synchronization model

All non-resident worksheets must link resident identity fields from the `Residents` worksheet.

This ensures:

- resident details are maintained in only one place
- data remains consistent across worksheets
- updates propagate automatically
- user error is reduced

### Recommended linking approach

For each non-resident worksheet:

- `Flat No.` should be linked from the `Residents` sheet
- `Resident Name` should be linked from the `Residents` sheet
- `Email` should be linked from `Resident Email` in the `Residents` sheet
- `Mobile No.` should be linked from `Resident Mobile` in the `Residents` sheet
- row order should remain aligned across worksheets for simplicity

### Operational assumption

The workbook should maintain the same resident row order across all worksheets.

This keeps formulas simple and makes the workbook easier for non-technical users to understand.

If row order changes later, a more advanced lookup-based approach may be used, but the default design should favor clarity and maintainability.

---

## Default values

### Residents worksheet

The `Residents` worksheet stores only master resident information and occupancy details.

It should not require monthly financial columns.

### Maintenance Charges worksheet

Every resident should have a default maintenance charge of **INR 3,500** for every month from `Jan-26` through `Dec-26`.

These values should be pre-filled when the workbook is created.

### Fine worksheets

Every monthly cell in every fine worksheet should default to **INR 0**.

Users should only replace `0` with the applicable fine amount when a fine is issued.

---

## Maintenance Charges worksheet behavior

The `Maintenance Charges` worksheet is the primary sheet for viewing the resident’s monthly amount due.

Each resident must appear in this worksheet.

Each month should calculate the total payable amount automatically.

### Calculation rule

For every resident and every month:

**Total Amount Due = INR 3,500 + Sum of all applicable fines for that month**

This means the value shown in each month column of `Maintenance Charges` should be formula-driven.

It should automatically update whenever any fine value is added, changed, or removed in any fine worksheet.

---

## Fine worksheet behavior

Each fine worksheet represents a single fine category.

These worksheets must include all residents and use the same financial column structure.

Examples of fine categories include:

- Parking Violation Fines
- Waste Management Fines
- Pet Policy Fines
- Noise Violation Fines
- Property Damage Fines
- Miscellaneous Fines

### Fine entry rule

Users should enter the fine amount in the relevant month column for the relevant resident.

Default monthly values must be **INR 0**.

No manual summation or cross-sheet calculation should be required from the user.

The `Maintenance Charges` worksheet must automatically include all fines from all fine worksheets.

---

## Property Damage Fines scope

The `Property Damage Fines` worksheet should be used for fines related to damage caused to society property.

This may include damage to:

- lifts
- walls
- gates
- gardens
- clubhouse assets
- CCTV systems
- lighting
- any other shared society property

This worksheet follows the same schema and rules as all other fine worksheets.

---

## Formula design expectations

The workbook should rely on Excel formulas for automation.

### Formula goals

Formulas should ensure that:

- resident identity fields remain synced from `Residents`
- owner-to-resident auto-fill works correctly when `Occupancy Type = Owner`
- rental resident fields remain editable when `Occupancy Type = Rental`
- maintenance charges are pre-filled consistently
- fine sheets default to zero values
- monthly totals in `Maintenance Charges` update automatically

### Formula design preference

The formula strategy should prioritize:

- simplicity
- readability
- low maintenance burden
- compatibility with common Excel usage patterns
- ease of extension when duplicating fine sheets

Where possible, the workbook should avoid overly complex formulas if a simpler row-aligned approach can achieve the same result.

---

## Extensibility rule

If a new fine category is introduced later, users should be able to:

1. duplicate an existing fine worksheet
2. rename the duplicated sheet
3. keep the same schema
4. continue using the workbook without structural redesign

This is a key usability requirement.

The workbook should therefore be designed with repeatable worksheet patterns rather than category-specific schemas.

---

## Operational model summary

The workbook follows this model:

- `Residents` = master owner/resident data
- `Maintenance Charges` = calculated payable amounts per month
- fine worksheets = category-specific monthly fine entries
- formulas = automatic syncing and aggregation logic

This creates a simple workflow:

1. update owner and resident details only in `Residents`
2. enter fines only in the appropriate fine worksheet
3. review monthly totals in `Maintenance Charges`

This keeps the workbook practical for common users and avoids any dependency on database administration.

---

## Out of scope

The following are out of scope for this document unless later introduced in a separate design document:

- SQL schema design for primary operations
- database normalization strategy
- stored procedures
- ORM models
- API persistence layer details
- audit logging implementation
- payment gateway reconciliation
- receipt generation logic

These may be added later if the system evolves beyond workbook-first operations, but they are not part of the current primary data model.

---

## Implementation note

If the project later needs system integration, reporting automation, or backup synchronization, the Excel workbook can be exported or mirrored into another storage layer.

However, the business-facing workflow should continue to treat Excel as the primary user-managed data source.

---

## Status

Suggested status: Updated for workbook-first data model
Suggested owner: Data design / operations workflow
