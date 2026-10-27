"""A second new fictional challenge set, authored after routing-v4 was frozen."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = [
    "The receiving photos show the aluminium display stand bent into a curve. Its carton is complete, there are no loose parts, and the customer wants a repair assessment.",
    "The terminal brought forward its holiday closure. Our sealed container of books is identified in bay 12, but the booked collection must move to Tuesday.",
    "The import entry names the consignee's old legal entity. Customs is holding the sewing machines until the broker corrects the declaration; all machines are accounted for.",
    "At the returns centre the scanner accepted four rental projectors, but the shelf holds three. A physical search has not located the fourth and the last handover count is disputed.",
    "The vaccine carton is being held in its transport box. Its required range is 2 to 8 C, while the current calibrated product probe reads 10 C and continues to rise.",
    "A dock leveller dropped while a worker was crossing it. The worker is trapped between the platform and vehicle and nobody has stopped the next truck from approaching.",
    "The signed receipt has yesterday's date, but the consignee confirms today's delivery was complete and intact. Accounts needs a corrected delivery receipt, not a cargo search.",
    "The rail operator removed our wagon from tonight's departure because of a track possession. The sealed wagon and all packaged furniture remain in the marshalling yard for the next service.",
    "The chilled food is stable at 3 C within its 1-5 C specification. The claim concerns the cardboard sleeves, which were torn by a handling strap; no product is exposed.",
    "The engineer cannot restore the warehouse fire suppression system because a replacement control relay is held for a missing export licence. The system remains disabled and no alternative protection is in place.",
    "The airway bill lists an extra crate that the shipper says was never tendered. The airline says it collected the full booking. We need evidence of what physically changed hands before choosing a team.",
    "The driver is waiting at the buyer's locked gate with the complete load of exercise mats. The buyer has confirmed that staff will return at 3 pm to accept it.",
    "The woven rug arrived with a long cut through its centre. The receiver has retained the wrapping and requests a replacement; there is no continuing physical hazard.",
    "A sealed drum marked corrosive has fallen on its side. Liquid is leaking beneath the racking and staff are still picking orders in that aisle.",
    "The packing list gives kilograms where the broker's entry requires pounds. The weights need correction before clearance; the shipment is sound and in the nominated inspection area.",
    "A tote of catering cutlery was handed to a subcontractor without a destination scan. Neither depot can locate it, and the event team says nothing was received.",
    "The floral cargo specifies 4 to 7 C. The display and two verified probes agree on 6 C; the customer asks for the day's temperature chart for a routine quality audit.",
    "URGENT: please prioritise the coffee cups. The customer is annoyed by a one-day delay, but the full load is located in our secure yard and no safety service depends on it.",
    "The container's door bars were deliberately cut and a person is unloading its contents into an unmarked van now. The guard is watching from the occupied gatehouse.",
    "The broker has the correct permit, but the uploaded PDF is blank on every page. Customs needs a readable copy of that document before releasing the routine household-goods load.",
    "The temperature file for a frozen shipment has a six-hour gap. Arrival product readings and the permitted limits are not supplied, so quality cannot establish whether exposure occurred.",
    "The cartons are damp and their books have swollen pages after a roof leak in transit. They are now on a dry rack and the request is for a cargo damage claim.",
    "The replacement fan for the site's emergency ventilation is on a vehicle waiting for a bridge to reopen. Ventilation has failed and staff cannot safely remain in the affected room.",
    "The tracking page says a parcel of curtain fittings was delivered, but the named signer does not work at the address and the occupants deny receipt. Its present location is unconfirmed.",
    "A store employee reports that the counterweight inside the delivered machine is cracked. It has been disconnected, supported and cordoned off; no one is exposed to it now. A repair claim is requested.",
    "Yesterday's freezer excursion is closed. The goods are now quarantined in verified controlled storage, and the cold-chain desk is asked to attach the historical trace to its disposition record.",
    "The carrier transcribed the wrong seal number on the declaration. The actual seal is intact and matches the shipper's photo; the customs record needs amendment.",
    "The message reads only 'Red status on this load - call me'. It contains no shipment reference, location, condition or explanation of the red status.",
    "The depot confirms the entire toy consignment was loaded onto the wrong service. It is sealed on that vehicle at the north hub; recovery is arranged but delivery will be late.",
    "The battery charger beside the dispatch cages is sparking and giving off smoke. Staff are still using the adjacent packing station.",
    "The frozen berries require -24 to -18 C. A calibrated probe is now at -15 C, and the pallet remains inside the loaded trailer without a working compressor.",
    "Seven identical camera cases were sent, but the consignee counted six when the vehicle was emptied. The seals show no damage and the last case cannot be found at either end.",
    "The consignee has approved the invoice amount, but its tax registration number is incorrect. They need a corrected commercial invoice to complete the import file.",
    "A hotel renovation order is intact on the truck, but the road authority has moved the delivery window to after 8 pm. Please update the appointment and arrival estimate.",
    "The steel shelving arrived with chipped coating and several twisted brackets. All components are present and secured on the ground; arrange a claim inspection.",
    "The medical-gas alarm's replacement sensor is absent from the express parcel. The alarm is still unavailable, the occupied facility has no temporary monitoring, and restoration is blocked.",
    "A box labelled reagent is giving off an unusual odour. Nobody knows whether it contains hazardous material, and there is no information about who is nearby or whether it is open.",
    "The cold room logger sent an alarm from an empty bay. No stock was inside, the bay is now isolated for maintenance, and quality needs the false-alarm record reviewed.",
    "The receiver confirms every carton arrived intact, but the electronic proof of delivery shows only a loading image and no signature. The missing signed record is the unresolved issue.",
    "The booking was moved to another flight after a cancelled departure. All three sealed cases are confirmed in the airline's secure store; please arrange their later onward delivery.",
    "The fragile plates arrived in pieces. The receiver has boxed the shards and cleared the unpacking area; they are asking for a claim reference and replacement stock.",
    "The laboratory's temperature-controlled chemicals have a stated range of 15 to 25 C. The loaded compartment reads 31 C on an independent probe and cooling has not recovered.",
    "Two depot clerks disagree about whether the unnumbered cage contains this customer's parcels. No parcel count or recent location record has been supplied.",
    "A forklift damaged a gas cylinder valve and gas is venting beside the occupied sorting line. The area has not been evacuated or isolated.",
    "The broker used the description 'electric heaters' for a shipment of wooden ornaments. No electrical products are present; correct the import declaration before clearance.",
    "The refrigerated cartons reached the receiver at 5 C, which is within the stated 2-8 C range. Their logger records are complete; the only dispute is the late delivery appointment, with all goods intact and located.",
    "The pallet wrap was removed and a clearly empty space was found where the listed calibration tool should have been. Both packing and receiving staff are unable to account for the tool.",
    "A crack was photographed in an outer equipment case. The shipper says it existed before dispatch, while the receiver says it is new; inspection of the contents has not happened.",
    "The shipment of replacement stationery is in our yard, intact. The original collection driver called in sick; the replacement pickup is scheduled for tomorrow morning.",
    "A smoke alarm at the loading dock activated during a drill last week. The drill is complete, the site is secure and operations needs to close the safety incident record.",
    "One sensor on the chilled seafood pallet reads 2 C and another reads 9 C against an allowed 0-4 C range. Nobody has checked either sensor against a reference instrument.",
    "The customer says ten reels are missing, but a current signed count and photographs show all ten sealed reels on the truck. The actual request is to rebook delivery after the factory's closure.",
    "The certificate of origin names the wrong country of manufacture. The stock is intact and securely held by the broker until a corrected certificate is supplied.",
    "A stack of loaded crates is leaning into a pedestrian route and a support has fractured. Workers continue to pass underneath it; the stack could collapse.",
    "The returned handbag collection never reached the consolidation cage. The last scan is from a sorting conveyor, and a search of both ends cannot locate the bags.",
    "The receiver reports a rattling noise inside an unopened appliance crate. There are no visible marks; they have not inspected or tested the appliance and cannot yet describe a fault.",
    "The driver reports a broken mirror but says the vehicle and sealed cargo are parked safely in our yard. A replacement vehicle is booked, and delivery of the paintbrushes will be delayed.",
    "Customs has released the cargo, but the status page still says held. The broker supplied a release confirmation; the customer needs the clearance record corrected before arranging collection.",
    "The message mentions a damaged crate, possible missing contents and a warm package. There are no counts, temperatures, limits, pictures or current location, and no one has confirmed what happened.",
    "A person has fallen from the vehicle roof while removing a delivery cover. They are injured, the driver has not reached assistance, and vehicles are still entering the bay.",
]


def main():
    assert len(REPORTS) == len(set(REPORTS)) == 60
    rows = [{"id": f"RLY-{920001+i}", "text": text,
             "channel": ["Customer portal", "Control desk", "Depot note", "Email"][i % 4]}
            for i, text in enumerate(REPORTS)]
    random.Random(2026102202).shuffle(rows)
    path = ROOT / "data/fresh2_reports_20261022.jsonl"
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    if path.exists():
        if path.read_text() != content:
            raise ValueError("Preserve the frozen fresh-2 source.")
    else:
        with path.open("x") as stream:
            stream.write(content)
    print("Verified 60 new fictional reports:", path.name)


if __name__ == "__main__":
    main()
