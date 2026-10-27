"""Deterministic synthetic corpus. No private or third-party incident reports."""
from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SEED = 20261021

# Each line: urgency (U/R), clarification needed (Y/N), report. Dev families are
# kept together when split. The test bank uses separate authored scenarios.
DEV = {
"delay": """
R|N|The delivery truck is stuck in expressway traffic. Ambient cartons will reach the depot two hours after the booked slot.
R|N|A customer was not home for delivery. The sealed parcel is with the driver and a second attempt is booked tomorrow.
R|N|The vessel missed its connection. All cargo is accounted for and the receiver has accepted a revised arrival on Friday.
R|N|A warehouse loading queue has pushed dispatch back three hours. No safety or storage concern is reported.
R|N|The recipient asked us to change the delivery window to next week. The consignment remains safely in storage.
R|N|URGENT in the subject line: a routine stationery order will arrive one day late. No critical use or product risk is stated.
U|N|A replacement part for the site's fire suppression system has missed delivery. The site's protection is offline and the part must arrive within an hour.
R|Y|The customer says the truck never arrived, but the carrier shows a completed delivery. No proof or location is available yet.
R|N|The driver took a wrong turn and will arrive 40 minutes late. The cargo is intact and the customer has been informed.
U|Y|An emergency generator part is held in a traffic queue while the backup power at the destination is failing. Exact remaining runtime is unknown.
""",
"missing": """
R|N|A parcel has no scan after sorting yesterday. The consignee has not received it and the warehouse needs to trace its location.
R|N|The shipment arrived with one carton short. There is no indication of theft or product damage.
R|Y|The system says delivered but the recipient denies receipt. The signature is unreadable and the driver cannot confirm the address.
R|N|A pallet was loaded onto the wrong linehaul. Its present depot is known and recovery transport is being arranged.
R|N|The receiver found an empty sealed envelope where the ordered spare parts should have been. Please investigate the missing contents.
U|N|A missing component is needed to restore a disabled industrial emergency stop. The site cannot safely operate until it is located.
R|N|Two bags are absent from the inbound count. The carrier has requested a dock search and a scan history check.
R|Y|Tracking has been silent for a week. We do not know the contents or whether the shipment is time-sensitive.
R|N|The freight forwarder cannot find the consignment at the transfer hub. No hazardous or controlled contents were declared.
U|Y|The destination needs its missing emergency power module immediately. Backup supply is running out, but the shipment's last confirmed location is unclear.
""",
"damage": """
R|N|A cardboard carton was crushed at unloading. The contents are dented but stable, with no leak or risk to staff.
R|N|The receiver found a cracked glass panel inside its protective crate. The sharp pieces have been contained and the area is safe.
R|N|Water entered an electronics shipment during transit. The units are disconnected and isolated for inspection.
R|N|The outer wrapping is torn and several retail boxes are scuffed. The customer requests photos and a damage claim.
R|N|A forklift dented the corner of a metal cabinet. It is stable on the pallet and no one was injured.
R|Y|The consignee reports something is broken but has not identified the item or provided images. No immediate hazard is described.
R|N|The cargo was scratched in transit. The receiver accepted it under reservation and requests a repair estimate.
R|N|A ceramic fixture arrived shattered. Fragments are secured in the package for claims inspection.
R|Y|The pallet looks damaged and the receiver says one box may also be missing. The count has not been checked.
R|N|The wooden crate was split at the side. The machine inside has visible cosmetic marks and is secured pending assessment.
""",
"temperature": """
U|N|The refrigerated container is at 14 C against a 2 to 8 C requirement. The refrigeration unit has stopped and the goods remain inside.
R|N|A chilled shipment had a brief sensor alarm, but a second calibrated probe confirms 4 C throughout. The logger fault is documented.
U|N|Frozen food is thawing on the dock because the cold room has lost power. The stock has not been moved to a working freezer.
U|N|The reefer is leaking coolant and cannot maintain its set point. The temperature is rising and no replacement unit is on site.
R|N|The temperature monitor battery is low. A working backup logger shows the cargo has stayed within its required range.
R|Y|The customer says the boxes felt warm. The product limits and the transport temperature record have not been provided.
U|N|The driver reports the cold compartment at 19 C with sensitive cargo still inside. Product limits are 2 to 8 C and immediate isolation is needed.
R|N|A previous excursion was investigated and the cargo is now quarantined under the quality team's control. This report asks for the final disposition record.
U|Y|A chilled load may have been left unrefrigerated overnight. The logger is unreadable and nobody has confirmed whether the stock is still exposed.
R|N|The receiver requests the temperature trace for an otherwise compliant delivery. No excursion or active cooling issue occurred.
""",
"safety": """
U|N|Smoke is coming from a battery pallet on the loading bay. Staff are still nearby and the area has not been isolated.
U|N|A chemical drum is leaking onto the warehouse floor. The contents are hazardous and the spill has not been contained.
U|N|A person has been injured by a shifting load. Emergency assistance has been requested and the loading operation is still active.
U|N|The truck has been hijacked and the driver's whereabouts are unknown. The security response is needed immediately.
U|N|A suspicious person is removing sealed cartons from the secured yard. The incident is happening now.
R|N|Yesterday's minor workplace collision is closed. Nobody was injured and the report is for the completed safety log.
R|N|A fire drill caused a temporary stop to loading. There was no real fire and normal operations have resumed.
U|Y|There is an unusual chemical smell by an unmarked package. Staff cannot identify its contents and the area remains occupied.
R|N|The receiver asks for the signed security seal checklist. The seal was intact and no intrusion occurred.
U|N|A pallet is leaning over a busy pedestrian lane and could collapse. Staff have not yet cordoned off the area.
""",
"documentation": """
R|N|Customs has held the consignment because the commercial invoice is missing. Cargo remains in secure ambient storage.
R|N|The packing list and invoice have different carton counts. The broker needs corrected documents before clearance.
R|N|The tariff code is incomplete on the import declaration. Please send the correct classification to the broker.
R|N|The proof of delivery has not been uploaded. The receiver confirms the full shipment arrived without issues.
R|N|The consignee name is misspelled on the bill of lading. The forwarder requests an amendment.
R|Y|The customs declaration lists an item the sender does not recognise. We need to confirm the actual contents before routing the request.
U|N|A permit error is blocking delivery of a part needed to restore an offline factory fire pump. The fire protection outage is ongoing.
R|N|The certificate of origin has expired. The shipment can remain safely at the bonded warehouse pending a replacement.
R|N|The seal number in the transport document differs from the recorded number. The physical seal is intact and the depot verified the contents.
R|N|The customer wants a duplicate invoice for reconciliation. The shipment has already been delivered and accepted.
""",
}

TEST = {
"delay": """
R|N|The van is waiting for a ferry after the last sailing was cancelled. The dry-goods customer agreed to delivery tomorrow.
R|N|Our books are on the correct truck, but the school receiving desk closes before it arrives. Please rebook the handover.
U|N|The vehicle carrying the replacement emergency ventilation motor is delayed at a road closure. The destination's ventilation has failed and personnel cannot remain there safely.
R|Y|The recipient has sent only 'late again, fix it'. There is no tracking reference or description of what was ordered.
R|N|The driver is taking a mandatory rest break. All ambient cargo is secure and arrival will be 90 minutes after the estimate.
R|N|A furniture delivery missed the customer's preferred morning slot. There is no damage, missing cargo or immediate risk.
U|Y|A replacement pump needed for emergency flood protection is stuck en route during rising water. We have not confirmed how long the barrier can hold.
R|N|The destination rescheduled unloading because its loading crew is unavailable. The freight is still on our vehicle.
R|N|The shipment is intact and located at the origin depot. A scheduling error means it missed tonight's departure.
R|N|The customer marked a towel order 'ASAP'. It is expected two hours late and no service-critical impact was described.
""",
"missing": """
R|N|The inbound manifest lists twelve units but the destination has eleven. All received units are intact. Trace the absent unit.
R|Y|A consignee says the container never appeared while the terminal record says collected. The collecting vehicle is not identified.
R|N|The bag was sent to a depot in the wrong city. We have its scan and need a recovery plan.
U|N|A consignment containing the only replacement pressure-relief valve cannot be located. The site's safety system remains disabled awaiting the part.
R|N|A regular apparel order disappeared between two sorting hubs. There is no current evidence of a security incident.
R|Y|The delivery photo shows a doorway nobody recognises. The buyer has no parcel and the exact delivery address needs confirmation.
R|N|The warehouse cannot locate the return shipment after receiving it last week. Please search the return racks.
R|N|One roll of fabric is unaccounted for after a cross-dock transfer. No incident or active hazard was reported.
U|Y|The replacement module for the destination's failed emergency communications is unaccounted for. It is needed now, but we do not know which vehicle last carried it.
R|N|The carton count is correct but the sealed box contains no ordered instrument. The sender has requested a contents investigation.
""",
"damage": """
R|N|The receiver unpacked a bent bicycle frame. It is set aside and the customer needs a damage assessment.
R|N|A printer has a cracked housing after transport. It is unplugged and there are no exposed batteries or fluids.
R|Y|A client wrote 'everything is ruined' without photos or details. We need to establish the item and extent of damage.
R|N|The crate's side is splintered and the sculpture inside is chipped. The packing area has been made safe.
R|N|Rain soaked the paper stock in transit. The load is in dry storage awaiting a claim inspection.
R|Y|The consignee reports torn packaging and thinks some contents are gone. No count or inventory is supplied.
R|N|The chilled carton has a cosmetic tear. The seal is intact, the recorded temperature stayed in range and the claim concerns the packaging only.
R|N|A mirror arrived with a fracture. All pieces remain secured in the protective film and no one is exposed.
R|N|The steel panel is dented along one edge. It is stable in the unloading area and the receiver wants replacement approval.
R|N|A parcel of lamps has crushed shades. There is no smoke, leaking substance or continuing hazard.
""",
"temperature": """
U|N|Ice cream is softening in a trailer whose compressor has failed. The stock remains on board without working cooling.
R|Y|A receiver reports 'not cold enough'. We lack a measured temperature, the required limits and any transport record.
R|N|The receiver needs a logger file for the quality archive. All measurements met the shipment's stated storage conditions.
U|N|A 2 to 8 C product is now at 17 C after the insulated vehicle was left open. The consignment has not been quarantined.
R|N|A faulty display flashed 30 C, but two independent probes verified stable 5 C. The sensor has been replaced.
U|Y|The refrigerated goods were transferred into an unpowered compartment. We cannot read the logger or establish how long they have been there.
R|N|Last week's cold-chain deviation is already isolated and under a quality hold. This request is for the investigation paperwork only.
U|N|The cold storage circuit has tripped and the food cargo is warming rapidly. There is no spare cold room available.
R|N|A temperature warning was generated during an empty return trip. No product was on the vehicle.
U|N|The required minus 18 C freight has reached minus 2 C and continues warming. The refrigeration technician has not arrived.
""",
"safety": """
U|N|A worker is trapped beside a fallen load at the transfer bay. Other vehicles are still moving through the area.
U|N|A box of lithium cells is hissing and giving off heat. People are standing close to the unisolated pallet.
R|N|The security team requests an archive copy of last month's resolved access incident. There is no ongoing intrusion.
U|Y|An unidentified liquid is spreading from a container near the break area. Its contents and hazard class have not been established.
U|N|The driver reports an armed threat beside the vehicle. Cargo and driver remain at the scene.
R|N|A mock evacuation was completed on schedule. The fire alarm was part of the exercise and there is no real emergency.
U|N|An unauthorised truck is taking goods from the locked compound right now. The gate operator has asked for immediate assistance.
R|N|An old near miss has been reviewed and its corrective action closed. Please file the final report.
U|N|A stack of heavy crates is sliding toward the loading crew. The unstable stack has not been secured.
U|N|A damaged acid container is venting fumes into the occupied warehouse. Nobody has isolated the area yet.
""",
"documentation": """
R|N|The forwarder cannot release the cargo until the exporter signs the missing origin declaration. Storage conditions are satisfactory.
R|Y|The transport papers describe machinery while the receiver expects clothing. We need to verify the actual consignment.
R|N|The broker needs the invoice currency corrected before lodging the entry. No urgent use or cargo risk is identified.
R|N|The customer received all items but the electronic receipt has the wrong company registration number.
U|N|A clearance document error is preventing the release of the replacement emergency sprinkler controller. The destination has no working fire protection until it arrives.
R|N|The import permit number has one incorrect digit. The goods are safe in the bonded facility awaiting an amendment.
R|N|A pallet of spare labels is held because the tariff heading is absent. The broker requests a corrected declaration.
R|N|The delivery signature file is blank, although the consignee confirms receipt of the undamaged shipment.
R|N|An audit found that the manifest uses the old customer address. The completed delivery itself was correct.
R|N|The receiver requests a copy of the stamped packing list for its accounts team. There is no operational issue with the cargo.
""",
}

def parse(bank):
    return {cat: [(u == "U", c == "Y", text) for u, c, text in
                  (line.split("|", 2) for line in body.strip().splitlines())]
            for cat, body in bank.items()}

def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    identifiers = rng.sample(range(10000, 99999), 360)
    channels = ["Email", "Depot note", "Driver message", "Customer portal", "Control desk"]
    wrappers = ["{text}", "Dispatch update: {text}", "Please check this report. {text}",
                "Message from the receiving team: {text}", "Operations note — {text} Please advise the next team."]
    development, review, draft = [], [], []
    for cat, scenarios in parse(DEV).items():
        # Two fixed families per category are held out of training completely.
        validation_families = {8, 9}
        for family, (urgent, clarify, text) in enumerate(scenarios):
            for variant, wrapper in enumerate(wrappers):
                ident = f"RLY-{identifiers.pop()}"
                development.append({"id": ident, "text": wrapper.format(text=text),
                    "category": cat, "urgent": urgent, "clarification": clarify,
                    "family": f"dev-{cat}-{family}",
                    "split": "validation" if family in validation_families else "train",
                    "channel": channels[variant], "label_source": "synthetic author draft"})
    for cat, scenarios in parse(TEST).items():
        for family, (urgent, clarify, text) in enumerate(scenarios):
            ident = f"RLY-{identifiers.pop()}"
            review.append({"id": ident, "text": text, "channel": rng.choice(channels)})
            draft.append({"id": ident, "category": cat, "urgent": urgent,
                          "clarification": clarify, "label_source": "unreviewed synthetic draft"})
    rng.shuffle(development)
    rng.shuffle(review)
    assert len(development) == 300 and len(review) == 60
    assert len({r["text"] for r in development + review}) == 360
    write_jsonl(DATA / "development.jsonl", development)
    write_jsonl(DATA / "review_reports.jsonl", review)
    # Never exposed to reviewers, training, validation, static files or web API.
    write_jsonl(DATA / "private_draft_labels.jsonl", draft)
    with (DATA / "review_template.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["report_id", "report", "category", "urgency", "needs_clarification", "reason"])
        writer.writerows([r["id"], r["text"], "", "", "", ""] for r in review)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [DATA / "development.jsonl", DATA / "review_reports.jsonl"]}
    (DATA / "manifest.json").write_text(json.dumps({"seed": SEED,
        "development": 300, "train": 240, "validation": 60, "independent_review": 60,
        "source": "Original synthetic reports authored with OpenAI Codex. No real operator data.",
        "sha256": hashes}, indent=2) + "\n")
    print(json.dumps({"created": 360, "train": 240, "validation": 60, "review": 60}))

if __name__ == "__main__":
    main()
