"""Generates a monitoring dataset for a (fictional) youth employability programme and a
single-file interactive dashboard (index.html) with the data embedded. Open in any browser or GitHub Pages."""
import json, numpy as np, pandas as pd
rng = np.random.default_rng(9)
regions = ["Ankara", "İstanbul", "İzmir", "Gaziantep", "Diyarbakır", "Trabzon"]
quarters = [f"{y}-Q{q}" for y in (2025, 2026) for q in (1, 2, 3, 4)][:7]
rows = []
for r in regions:
    scale = rng.uniform(.7, 1.4)
    for i, q in enumerate(quarters):
        enrolled = int(rng.normal(120, 15) * scale * (1 + .06 * i))
        female = rng.uniform(.42, .62)
        completed = int(enrolled * rng.uniform(.68, .88))
        employed = int(completed * rng.uniform(.28, .52) * (1 + .03 * i))
        rows.append(dict(region=r, quarter=q, enrolled=enrolled, female=int(enrolled * female), completed=completed,
                         employed_6m=employed, satisfaction=round(rng.uniform(3.6, 4.6), 2), cost_try=int(enrolled * rng.uniform(5200, 7400))))
df = pd.DataFrame(rows); df.to_csv("monitoring_data.csv", index=False)
targets = {"completion_rate": .78, "employment_rate": .40, "female_share": .50, "satisfaction": 4.2}
html = open("template.html", encoding="utf-8").read().replace("__DATA__", json.dumps(rows, ensure_ascii=False)).replace("__TARGETS__", json.dumps(targets))
open("index.html", "w", encoding="utf-8").write(html); print(len(rows), "rows → index.html")
