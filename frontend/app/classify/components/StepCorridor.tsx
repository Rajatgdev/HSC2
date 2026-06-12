"use client";
import { useState } from "react";

const COUNTRIES = [
  ["AF","Afghanistan"],["AL","Albania"],["DZ","Algeria"],["AO","Angola"],["AR","Argentina"],
  ["AM","Armenia"],["AU","Australia"],["AT","Austria"],["AZ","Azerbaijan"],["BH","Bahrain"],
  ["BD","Bangladesh"],["BY","Belarus"],["BE","Belgium"],["BZ","Belize"],["BO","Bolivia"],
  ["BA","Bosnia and Herzegovina"],["BR","Brazil"],["BN","Brunei"],["BG","Bulgaria"],
  ["KH","Cambodia"],["CM","Cameroon"],["CA","Canada"],["CL","Chile"],["CN","China"],
  ["CO","Colombia"],["CR","Costa Rica"],["HR","Croatia"],["CU","Cuba"],["CY","Cyprus"],
  ["CZ","Czechia"],["DK","Denmark"],["DO","Dominican Republic"],["EC","Ecuador"],["EG","Egypt"],
  ["SV","El Salvador"],["EE","Estonia"],["ET","Ethiopia"],["FI","Finland"],["FR","France"],
  ["GE","Georgia"],["DE","Germany"],["GH","Ghana"],["GR","Greece"],["GT","Guatemala"],
  ["HN","Honduras"],["HU","Hungary"],["IN","India"],["ID","Indonesia"],["IR","Iran"],
  ["IQ","Iraq"],["IE","Ireland"],["IL","Israel"],["IT","Italy"],["JM","Jamaica"],
  ["JP","Japan"],["JO","Jordan"],["KZ","Kazakhstan"],["KE","Kenya"],["KW","Kuwait"],
  ["KG","Kyrgyzstan"],["LA","Laos"],["LV","Latvia"],["LB","Lebanon"],["LY","Libya"],
  ["LT","Lithuania"],["LU","Luxembourg"],["MY","Malaysia"],["MT","Malta"],["MX","Mexico"],
  ["MD","Moldova"],["MN","Mongolia"],["MA","Morocco"],["MZ","Mozambique"],["MM","Myanmar"],
  ["NP","Nepal"],["NL","Netherlands"],["NZ","New Zealand"],["NG","Nigeria"],["NO","Norway"],
  ["OM","Oman"],["PK","Pakistan"],["PA","Panama"],["PY","Paraguay"],["PE","Peru"],
  ["PH","Philippines"],["PL","Poland"],["PT","Portugal"],["QA","Qatar"],["RO","Romania"],
  ["RU","Russia"],["SA","Saudi Arabia"],["SN","Senegal"],["RS","Serbia"],["SG","Singapore"],
  ["SK","Slovakia"],["SI","Slovenia"],["ZA","South Africa"],["KR","South Korea"],["ES","Spain"],
  ["LK","Sri Lanka"],["SE","Sweden"],["CH","Switzerland"],["TW","Taiwan"],["TZ","Tanzania"],
  ["TH","Thailand"],["TN","Tunisia"],["TR","Türkiye"],["UG","Uganda"],["UA","Ukraine"],
  ["AE","United Arab Emirates"],["GB","United Kingdom"],["US","United States"],["UY","Uruguay"],
  ["UZ","Uzbekistan"],["VE","Venezuela"],["VN","Vietnam"],["YE","Yemen"],["ZM","Zambia"],
  ["ZW","Zimbabwe"],
].sort((a, b) => a[1].localeCompare(b[1]));
const INCO = [
  "",
  "EXW – Ex Works",
  "FCA – Free Carrier",
  "FAS – Free Alongside Ship",
  "FOB – Free On Board",
  "CFR – Cost and Freight",
  "CIF – Cost, Insurance and Freight",
  "CPT – Carriage Paid To",
  "CIP – Carriage and Insurance Paid To",
  "DAP – Delivered at Place",
  "DPU – Delivered at Place Unloaded",
  "DDP – Delivered Duty Paid",
];

export default function StepCorridor({ onNext }: { onNext: (o: string, d: string, i?: string) => void }) {
  const [origin, setOrigin] = useState("CN");
  const [dest, setDest] = useState("IE");
  const [inco, setInco] = useState("");
  const sel = "w-full p-3 border border-[var(--line)] rounded-md bg-white focus:outline-[var(--ink)]";
  return (
    <section>
      <div className="font-code text-[11px] tracking-[0.16em] uppercase text-[var(--stamp)] mb-2">Entry 01 · Trade corridor</div>
      <h1 className="font-serif-d text-3xl font-semibold mb-2">Where is this shipment moving?</h1>
      <p className="text-[var(--muted)] mb-7 max-w-[54ch]">Origin and destination decide which duties, preferences and restrictions apply to the final code.</p>
      <div className="grid sm:grid-cols-2 gap-4 mb-4">
        <div><label className="block text-sm font-semibold mb-1.5">Origin country</label>
          <select className={sel} value={origin} onChange={(e) => setOrigin(e.target.value)}>
            {COUNTRIES.map(([c, n]) => <option key={c} value={c}>{n} ({c})</option>)}
          </select></div>
        <div><label className="block text-sm font-semibold mb-1.5">Destination country</label>
          <select className={sel} value={dest} onChange={(e) => setDest(e.target.value)}>
            {COUNTRIES.map(([c, n]) => <option key={c} value={c}>{n} ({c})</option>)}
          </select></div>
      </div>
      <div className="mb-4"><label className="block text-sm font-semibold mb-1.5">Incoterm <span className="font-normal text-[var(--muted)]">(optional)</span></label>
        <select className={sel} value={inco} onChange={(e) => setInco(e.target.value)}>
          <option value="">Not specified</option>
          {INCO.filter(i => i).map((i) => (
            <option key={i} value={i.split(" ")[0]}>{i}</option>
          ))}
        </select>
        <p className="text-xs text-[var(--muted)] mt-1.5">Used for context only — it doesn't change the classification.</p></div>
      <button onClick={() => onNext(origin, dest, inco || undefined)}
        className="bg-[var(--ink)] text-white rounded-md px-5 py-3 font-semibold hover:bg-[#1d2e54]">
        Describe the product →
      </button>
    </section>
  );
}
