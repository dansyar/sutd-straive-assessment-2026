"""Reproduce the new fictional reports; contains no reference labels."""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REPORTS = [
    "The ferry operator cancelled tonight's sailing. Our pallet of ceramic tiles is still sealed in the booked staging bay; the next departure is tomorrow afternoon.",
    "The driver reached the furniture store on time, but its booking system gave us a slot after closing. The complete load is back at our depot for a new appointment.",
    "A tyre puncture added four hours to the journey. The replacement truck has all ten rolls of carpet and is now moving; please give the shop a revised ETA.",
    "The replacement actuator for the terminal's fire-water pump is on a truck stuck behind a road closure. The pump cannot be restored until it arrives and there is no backup pump operating.",
    "The consignee says URGENT in every message about the promotional mugs. We know exactly where the full shipment is; its arrival moved from 10 am to 2 pm and no safety service is affected.",
    "A short-notice port inspection moved the vessel's departure to Monday. The sportswear container is identified on the quay, intact and cleared; the request is to arrange a later delivery slot.",
    "The tail-lift stopped working before unloading the packaged chairs. Nothing fell and nobody was hurt. The driver and all chairs are at the customer's loading bay waiting for a suitable unloading vehicle.",
    "The customer accepted tomorrow's revised arrival for the office plants, but the tracking page still shows today. Please correct the delivery forecast; the van and all cartons are accounted for.",
    "The scheduled courier for a repair part that restores a hospital's medical-gas alarm did not collect it. The alarm is still unavailable with no temporary monitoring, and the part remains at the supplier.",
    "Our loaded vehicle arrived after the receiver's staff went home. It is parked in our secure yard with the full load of pet bedding; we need to arrange redelivery.",
    "The manifest lists 24 sacks of coffee. At unloading we counted 23, with no torn sacks or spill. Searches of the vehicle and loading bay have not located the last sack.",
    "Tracking says the laptop parcel was handed to reception, but the building has no reception desk and none of its occupants acknowledge receiving it. We have no confirmed delivery location.",
    "A cage of stationery was accidentally cross-docked onto another route. That driver confirms it is sealed on his vehicle at the east depot; arrange recovery and a later handover.",
    "The consignee received a sealed carton of printed leaflets with the space for its removable metal tooling insert empty. The insert is on the packing list; neither end can locate it.",
    "A courier left the battery cabinet at an unstaffed side entrance according to a photo. The customer cannot find it there and no one can confirm who moved it; there is no evidence yet of theft or an electrical hazard.",
    "Three numbered sample kits have not appeared since the conveyor transfer. The rest reached sorting normally. Their owner needs a trace; nothing in the report identifies a current safety consequence.",
    "The main pipe-burst isolation valve for the occupied laboratory is missing from the express shipment. Water is still entering an electrical service area and the site cannot isolate it without that valve.",
    "Our inventory says the return tote is back in aisle D, but two physical counts cannot find it. The customer is waiting for the returned hand tools; please locate the tote.",
    "The carrier recorded collection of two exhibition cases, while the venue signed for one. Neither party can account for the second case and there is no photo showing it at delivery.",
    "A signed delivery scan belongs to the neighbouring unit, whose staff say they have no parcel for us. The shipment of tablecloths remains unlocated; the carrier's route record needs checking.",
    "The stone countertop arrived with one corner snapped off. The pieces are wrapped and secured on a pallet; no sharp fragments remain loose. Please arrange a damage assessment.",
    "The upholstery on two armchairs has oil marks from transit. They are in the customer's storeroom and no liquid is leaking now. We need photographs and a repair or replacement claim.",
    "The delivery crate took a fork strike. Its oak door panels are split, but the load is stable on the ground and the area is clear of people. Record the cargo damage.",
    "The receiving team found six dented tins in a carton of biscuits. None is punctured, swollen or leaking, and the remaining cargo is intact. They want a credit for those tins.",
    "A framed print has a cracked glass cover. The receiver has taped and boxed all fragments and reports no injury or ongoing hazard. Please start the repair claim.",
    "Rain entered the trailer and stained the packaged cotton fabric. The trailer is now dry, the rolls are isolated in a dry rack, and the claim concerns the stained fabric rather than a late arrival.",
    "Several sealed outer cartons are scuffed, but the refrigerated contents remained at 4 C throughout transport within their permitted 2-6 C range. The receiver requests compensation for the packaging damage only.",
    "A shock indicator activated on the microscope crate. There is no visible breakage, and a functional inspection has not yet happened; the receiver asks whether it should open a damage claim.",
    "The ice-cream trailer's evaporator is off and the product core is minus 9 C, against a required minus 22 to minus 18 C. The doors are closed but the loaded trailer is continuing to warm.",
    "The cargo requires 36-46 F. Two calibrated probes now show 50 F in the same loaded compartment and the refrigeration unit is still trying to recover.",
    "The fish consignment specifies 0 to 2 C. The logger is holding at 1.2 C; a scheduled quality audit asks for its temperature trace and there has been no reported excursion.",
    "An unopened insulated pack of biological samples arrived with an illegible temperature display. Nobody has read the backup logger and the allowed range is not supplied. Please decide what information quality needs before release.",
    "During transit the frozen dough briefly reached -12 C, outside its -20 to -16 C specification. The batch is now isolated in a verified -18 C store and quality asks for a disposition review of the recorded excursion.",
    "The container is empty awaiting cleaning. Its refrigeration fault light is on, but no goods are inside and the next loading has been cancelled until maintenance signs it off.",
    "A sensor on the cheese pallet reads 3 C and another reads 11 C. The permitted range is 2-5 C; both claim to measure the same product and neither has been checked with a reference probe.",
    "The flowers have a stated maximum of 8 C. The reefer screen now shows 14 C with the loaded doors closed; no product probe is available and the compressor has stopped.",
    "Our warm-hold meals must remain between 60 and 65 C. A verified probe reads 54 C and heat has not been restored. Staff are asking whether to continue dispatching from this load.",
    "Last month's freezer alarm involved no exposed product: the bay was empty. The incident is closed and the quality desk needs the archived temperature log attached to the record.",
    "A charged power-bank carton is hissing and expanding at the packing bench. People are still working beside it and no one has isolated the area.",
    "A person without a visitor pass has forced the warehouse gate and is walking between occupied loading bays. The guard cannot account for them and asks for immediate assistance.",
    "The forklift operator struck a pedestrian in the dispatch aisle. The person is on the floor and traffic has not yet been stopped.",
    "One drum of cleaning solvent is dripping into the pedestrian walkway. The label is readable, the leak is still active, and staff are stepping around it to collect orders.",
    "A customer alleges a carton was stolen, but the only evidence supplied is a late tracking update. The depot confirms the intact carton is still in its locked dispatch cage; no theft or intrusion occurred. Please arrange its delayed departure.",
    "A shipment's GPS tracker is moving away from the scheduled route while the driver reports being threatened by someone in the cab. Contact with the driver has just been lost.",
    "A guard found last week's damaged lock during a scheduled audit. The lock was replaced that day, the site is secure and there was no loss; the request is for a completed security incident record.",
    "Two staff have itchy eyes next to an open unmarked tote that gives off a strong odour. Nobody knows what it contains and the area remains occupied.",
    "Customs rejected the declaration because the invoice currency says USD while the declared value was entered as SGD. The container is safely held for a corrected entry and no critical service is affected.",
    "The delivery happened yesterday and the recipient confirms all goods arrived intact. Accounts cannot close the job because the signed proof-of-delivery attachment will not open.",
    "The export permit is valid, but the carrier entered the previous vehicle's registration on it. The load is held at the checkpoint waiting for the trade desk to amend the record.",
    "A routine ceramics shipment has a tariff code for clothing on its import declaration. The cargo is located and sound; the broker needs a corrected classification before clearance.",
    "The consignment contains non-hazardous plastic parts, but a copied form incorrectly declares lithium batteries. There are no batteries or physical hazards in the load. Correct the shipping declaration.",
    "A licence number is missing from the clearance packet for the replacement fire-alarm controller. The building's alarm remains out of service with no temporary alarm, and customs will not release the controller until the licence is supplied.",
    "The receiver accepts all eight cartons but their invoice lists seven. Nothing is missing or damaged; the commercial invoice needs to match the completed delivery.",
    "The broker says the clearance form was accepted; the port system says rejected and does not show a reason. The cargo's location and condition are confirmed. We need to establish which clearance status is valid.",
    "The message only says 'Please help with shipment 471, something is wrong.' It gives no location, contents, symptoms, condition or current consequence.",
    "The customer says the entire consignment is missing; the driver says it is on the truck but delayed. Neither has supplied a recent location or count, so we cannot establish what actually happened.",
    "A temperature monitor shows ALERT without any units or reading. The subject also mentions a customs hold. There is no information about the goods, permitted range, current location or whether either issue is still active.",
    "One of the chilled pallets has ruptured packaging and a sweet-smelling puddle is spreading toward a live charging point. Its temperature history is also incomplete; people remain beside the pallet.",
    "The box arrived crushed and one of its two instruments is absent. The receiver has not provided a count at opening or pictures, and the carrier says the sealed box was intact at handover.",
    "There is a red light on the cabinet beside the loading door. The note does not identify the cabinet, what the light means, whether goods are inside or whether anyone is at risk.",
]


def main():
    if len(REPORTS) != 60 or len(set(REPORTS)) != 60:
        raise ValueError("Expected 60 distinct reports.")
    rows = [{"id": f"RLY-{910001+i}", "text": text,
             "channel": ["Email", "Depot note", "Control desk", "Customer portal"][i % 4]}
            for i, text in enumerate(REPORTS)]
    random.Random(20261022).shuffle(rows)
    destination = ROOT / "data/fresh_reports_20261022.jsonl"
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    if destination.exists():
        if destination.read_text() != content:
            raise ValueError("Preserve the frozen fresh report file.")
    else:
        destination.write_text(content)
    print(f"Verified {len(rows)} fresh fictional reports: {destination.name}")


if __name__ == "__main__":
    main()
