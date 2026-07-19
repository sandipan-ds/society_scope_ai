"""Generate the synthetic sample document corpus in data/sample_docs/.

These are the public society documents that get ingested into the vector
store. They contain NO resident-private data — only public rules, notices,
policies, and minutes.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "sample_docs"

DOCS: dict[str, str] = {
    "society_handbook_2026.md": """# Society Handbook 2026

## Welcome

Welcome to Society Scope Demo Society. This handbook summarizes the key rules
and facilities for all residents. It applies to all flats in Wings A and B.

## Society Office

The society office is located on the ground floor near the main entrance.
Office hours are Monday to Saturday, 10:00 AM to 6:00 PM. The office is closed
on Sundays and public holidays. For urgent matters outside office hours,
contact the security desk at the main gate.

## Monthly Maintenance Charges

Monthly maintenance charges are due by the 5th of each month. The current
charge is between Rs 2,200 and Rs 2,800 per flat depending on the approved
budget for the year. Payments can be made by UPI, bank transfer, or cheque at
the society office. A late fee of Rs 200 applies when payment is received
after the 15th of the month.

## Common Facilities

The society provides a community hall, a children's play area, a gym, and a
terrace garden. The community hall can be booked at the society office for
private functions. The gym is open from 6:00 AM to 10:00 PM daily.

## Water Supply

Municipal water supply runs from 6:00 AM to 9:00 AM and 5:00 PM to 8:00 PM.
Borewell backup is available round the clock for non-potable use. Overhead
tanks are cleaned every quarter; notices are issued in advance.

## Waste Collection

Door-to-door waste collection happens every morning between 7:00 AM and
9:00 AM. Residents must hand over segregated waste (wet and dry) to the
collection staff. See the Waste Segregation Policy for details.

## Security

The main gate is staffed 24 hours. All visitors must register at the gate.
Residents are responsible for the conduct of their guests and domestic help.
""",
    "visitor_policy.md": """# Visitor Policy

Effective: 10 January 2026

## Visitor Timings

Visitors are allowed between 8:00 AM and 10:00 PM on all days. Visitors
arriving after 10:00 PM may be allowed entry only with prior intimation to
the security desk by the host resident.

## Gate Registration

All visitors must register at the main gate with their name, purpose of
visit, and the flat number they are visiting. Security will call the host
flat to confirm before allowing entry.

## Overnight Guests

Overnight guests are permitted. Residents should inform the society office
in advance if guests will stay for more than three consecutive nights.

## Delivery Personnel

Delivery personnel (food, parcels, couriers) are allowed up to the lobby of
each wing. They are not permitted on residential floors unless the resident
has asked security to allow entry.

## Domestic Help and Drivers

Domestic help, cooks, and drivers must be registered at the society office
with a photo and police verification copy. Entry passes are issued for
registered staff and must be carried at all times.
""",
    "parking_policy.md": """# Parking Policy

Effective: 12 January 2026

## Allotted Slots

Each flat is allotted one covered parking slot in the basement. Residents
must park only in their allotted slot. Parking stickers are issued by the
society office and must be displayed on the vehicle windshield.

## Visitor Parking

Visitor parking is available in the open parking area near the main gate,
marked with yellow lines. Visitor parking is free for the first two hours.
Visitor vehicles must not be parked overnight without office permission.

## No-Parking Zones

Parking is strictly prohibited in the following areas:
- Driveway and turning circles
- Fire tender access paths
- In front of wing entrances
- Another resident's allotted slot

## Wrong Parking Penalty

A fine of Rs 500 will be imposed for parking in a no-parking zone or in
another resident's allotted slot. Repeat violations (three or more in a
quarter) may lead to the vehicle being wheel-clamped.

## Second Vehicles

Second vehicles may be parked subject to availability, after registering at
the society office and paying a monthly fee of Rs 500.
""",
    "pet_policy.md": """# Pet Policy

Effective: 1 February 2026

## Permitted Pets

Residents may keep dogs, cats, birds, and small caged animals. Exotic or
dangerous animals are not permitted.

## Registration

All dogs and cats must be registered at the society office with vaccination
records. Registration is free and must be renewed annually.

## Common Areas

Pets must be on a leash in all common areas including lifts, lobbies,
corridors, gardens, and the basement. Pet owners must clean up after their
pets immediately.

## Pet Timings in Gardens

Pets may use the central garden only before 8:00 AM and after 8:00 PM, so
that children and senior citizens can use the space comfortably during the
day.

## Noise

Pet owners must ensure their pets do not cause continuous noise disturbance,
especially between 10:00 PM and 7:00 AM.

## Complaints

Complaints about pets can be registered at the society office. Repeated
verified complaints may result in restrictions on the pet's use of common
areas.
""",
    "waste_segregation_policy.md": """# Waste Segregation Policy

Effective: 15 March 2026

## Segregation Requirement

As per municipal rules, all households must segregate waste into two
categories before handing it to collection staff:
- Wet waste: kitchen waste, vegetable peels, cooked food leftovers
- Dry waste: paper, plastic, metal, glass, packaging

## Collection Timings

Door-to-door collection runs daily from 7:00 AM to 9:00 AM. Waste handed
over after 9:00 AM must be dropped in the ground-floor bins of each wing.

## What Not to Hand Over

Do not hand over construction debris, batteries, electronics, or medical
waste to the collection staff. Contact the society office for disposal
guidance on these items.

## Non-Compliance

Households that repeatedly hand over unsegregated waste will receive a
written reminder. Continued non-compliance may attract a fine of Rs 300 per
occurrence after two written reminders.

## Composting

Garden and plant waste is collected separately every Sunday and composted
on site. Compost is available free to residents for home gardening.
""",
    "water_outage_notice.md": """# Notice: Water Supply Interruption

Date: 10 May 2026

## Summary

Municipal water supply will be interrupted on Tuesday, 12 May 2026, from
9:00 AM to 1:00 PM for overhead tank cleaning in both wings.

## What Residents Should Do

- Store sufficient water on Monday night for morning use.
- Borewell water will remain available for non-potable use.
- Report any leakage noticed after supply restoration to the office.

## Contact

For questions, contact the society office during office hours
(10:00 AM to 6:00 PM, Monday to Saturday).

This notice supersedes any earlier communication about tank cleaning dates.
""",
    "lift_maintenance_notice.md": """# Notice: Lift Maintenance

Date: 4 June 2026

## Schedule

Annual maintenance of all lifts will be carried out as follows:
- Wing A lifts: Saturday, 6 June 2026, 10:00 AM to 2:00 PM
- Wing B lifts: Sunday, 7 June 2026, 10:00 AM to 2:00 PM

## During Maintenance

One lift per wing will remain operational at all times. Residents are
requested to expect short delays and to give priority to senior citizens,
children, and anyone carrying heavy items.

## Safety Reminder

Do not force open lift doors. In case of a lift emergency, press the alarm
button inside the cabin or call the security desk; intercoms connect
directly to the gate cabin.
""",
    "festival_event_circular.md": """# Circular: Festival Celebration

Date: 20 July 2026

## Event

The society will celebrate the annual monsoon festival on Sunday,
26 July 2026, in the community hall from 5:00 PM to 9:00 PM.

## Programme

- 5:00 PM: Cultural performances by residents
- 6:30 PM: Games for children
- 7:30 PM: Snacks and dinner
- 8:45 PM: Prize distribution

## Contribution

A voluntary contribution of Rs 200 per family is requested to cover event
costs. Contributions can be paid at the society office or to any committee
member by 24 July 2026.

## Volunteers

Residents interested in volunteering for decoration, food, or games should
register at the society office by 23 July 2026.
""",
    "vendor_contact_notice.md": """# Notice: Approved Vendor Contacts

Date: 28 July 2026

## Purpose

The following vendors are empaneled for common household services. Residents
may contact them directly. The society does not guarantee pricing; rates are
between the resident and the vendor.

## Vendor List

- Plumbing: Reliable Plumbing Services, available 8 AM - 8 PM
- Electrical: City Electricals, available 9 AM - 7 PM
- Carpentry: WoodWorks Carpentry, available 9 AM - 6 PM
- Pest Control: SafeHome Pest Control, monthly service available
- AC Service: CoolAir Services, available 10 AM - 7 PM

## Gate Entry for Vendors

Vendors must register at the main gate and will be allowed entry only after
the security desk confirms with the resident's flat. Vendors are not
permitted after 8:00 PM except for emergencies confirmed by the resident.

## Feedback

Residents are requested to share feedback on vendor services with the
society office so the empaneled list can be reviewed quarterly.
""",
    "maintenance_due_reminder_july.md": """# Reminder: July Maintenance Dues

Date: 30 July 2026

## Reminder

This is a friendly reminder that July 2026 maintenance charges were due by
5 July 2026. Residents who have not yet paid are requested to clear their
dues at the earliest.

## How to Pay

- UPI or bank transfer to the society account (details at the office)
- Cheque deposited at the society office during office hours

## Late Fee

A late fee of Rs 200 applies to payments received after 15 July 2026, as
per the society handbook.

## Receipts

Payment receipts are issued by the society office within two working days
of payment. Residents paying by bank transfer should share the transaction
reference with the office for reconciliation.
""",
    "agm_minutes_jan_2026.md": """# AGM Minutes - January 2026

Meeting date: 25 January 2026
Venue: Community Hall

## Attendance

Quorum was met with members from 74 flats present in person or by proxy.

## Key Resolutions

1. The audited accounts for the previous year were presented and approved.
2. Monthly maintenance charges were retained at the current slab
   (Rs 2,200 to Rs 2,800 per flat) for the year 2026.
3. A late fee of Rs 200 for maintenance payments received after the 15th
   of a month was approved.
4. The proposal to install two additional CCTV cameras in the basement was
   approved; work to be completed by March 2026.
5. Waste segregation enforcement with written reminders and fines was
   approved and a separate policy will be issued.

## Other Business

- Members requested longer gym hours on weekends; the committee will review.
- A suggestion box will be placed at the society office.
""",
    "agm_minutes_apr_2026.md": """# AGM Minutes - April 2026

Meeting date: 26 April 2026
Venue: Community Hall

## Attendance

Quorum was met with members from 68 flats present in person or by proxy.

## Key Resolutions

1. The committee reported that the two new basement CCTV cameras approved in
   January have been installed and are operational.
2. The budget for repainting the exterior of both wings was approved. Work
   will begin after the monsoon, tentatively in October 2026.
3. A quarterly pest control contract for common areas was approved.
4. Visitor parking enforcement was discussed. The existing fine of Rs 500
   for wrong parking was retained, and security was instructed to issue
   warnings before fining first-time visitor violations.
5. The next AGM is scheduled for July 2026.

## Other Business

- Members appreciated the new composting initiative; compost distribution
  will begin in May 2026.
- A request for a children's indoor games room was noted for future
  consideration.
""",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in DOCS.items():
        (OUT_DIR / name).write_text(content, encoding="utf-8")
        print(f"wrote {name} ({len(content)} chars)")
    print(f"\n{len(DOCS)} sample documents written to {OUT_DIR}")


if __name__ == "__main__":
    main()
