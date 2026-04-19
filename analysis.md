# RTT Analysis
## Networks Assignment — Measurement & Geography

---

### Q1 — Which city has the highest inefficiency ratio?

**Lagos** consistently shows the highest inefficiency ratio, typically in the range of **4–6×** the theoretical minimum when measured from Boston (great-circle distance ≈ 8,200 km, theoretical minimum ≈ 82 ms, measured median often >350 ms).

Checking [submarinecablemap.com](https://submarinecablemap.com), the cables that serve Lagos and West Africa broadly include:

- **ACE (Africa Coast to Europe)** — runs from France down the West African coast to South Africa, landing at Lagos. It is the primary artery for Nigeria's international traffic.
- **MainOne** — connects Portugal to Nigeria and Ghana; a major cable for Nigerian ISPs.
- **SAT-3/WASC** — an older cable that is increasingly congested and shows higher latency.
- **WACS (West Africa Cable System)** — runs from the UK to South Africa via the West African coast.

What the cable map reveals is that **all major cables serving Lagos route traffic northward to Europe first** (London or Lisbon) before packets can reach North America. A packet from Boston to Lagos thus travels: Boston → transatlantic cable → UK/Europe landing point → ACE or MainOne southward back down to Lagos. This is a classic "hairpin" — the packet travels thousands of extra kilometers out of its way, inflating the RTT well beyond the theoretical minimum. Additionally, West African cables have historically been underprovisioned relative to traffic demand, causing queuing delays that further inflate RTT.

---

### Q2 — Which city is closest to the theoretical minimum?

**Frankfurt** or **London** typically show the lowest inefficiency ratios from Boston (often **1.5–2.0×**), meaning measured RTTs are only 50–100% above the theoretical floor.

This makes physical sense: Boston and Western Europe are connected by multiple high-capacity transatlantic cables (AEConnect-1, Hibernia Express/Apollo, TAT-14, and others), with landing points optimized for low-latency routes. Furthermore, major cloud providers (AWS, Google, Cloudflare) operate edge infrastructure in both regions, meaning the `google.de` request likely hits a nearby PoP rather than traveling all the way to a German datacenter. The low ratio tells us that North Atlantic routing infrastructure is mature, well-peered, and geographically efficient — routing closely approximates the great-circle path with minimal detours.

---

### Q3 — Why does Africa route through Europe?

**Historical and economic reasons:**

1. **Colonial-era telecommunications**: International telephone infrastructure was built by European colonial powers, who routed traffic through their own capitals. This topology became the template for early internet routing in Africa.

2. **Cable landing geography**: The first high-capacity submarine cables to connect Africa to global internet backbones (SAT-3 in the early 2000s, then ACE, WACS, MainOne) were financed and landed by European telecoms. They naturally terminated in Europe, creating a hub-and-spoke topology centered on London and Lisbon.

3. **IXP (Internet Exchange Point) scarcity**: Africa historically lacked its own major IXPs where traffic could be exchanged locally. Without them, even intra-African traffic (Lagos to Nairobi, say) often routes through Europe because that is where the peering agreements and backbone interconnects exist. The [NSRC](https://nsrc.org) and [AFRINIC](https://afrinic.net) have documented this extensively.

4. **Economics of peering**: Transit providers charge for traffic. African ISPs found it cheaper to buy transit to a European hub than to build direct cross-continental or transatlantic links.

**What would need to change:**

- **More direct cable routes**: Projects like the **2Africa** cable (Meta-backed, ~45,000 km ring around Africa with a spur to the US) and **Equiano** (Google, West Africa to Europe with African landing points) aim to reduce dependence on hairpin routing through Europe. Critically, a **direct West Africa → East Coast US** cable would eliminate the European detour for Boston↔Lagos traffic.
- **More African IXPs and local peering**: Expanding IXPs like IXPN (Lagos), JINX (Johannesburg), and KIXP (Nairobi) allows regional traffic to stay regional, reducing RTT for intra-African flows.
- **Local CDN presence**: If Google and Cloudflare place more edge nodes inside Nigeria (some already exist in Lagos), requests to `google.com.ng` could be answered locally, collapsing RTTs regardless of long-haul cable topology.

In short, the high Lagos inefficiency ratio is not a physics problem — it is an infrastructure and economic problem that is actively being addressed but is not yet solved.
