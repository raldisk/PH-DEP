# 🇵🇭 PH-DEP — Philippine Data Engineering Projects

<div align="center">

```
PH-DEP/
├── PH-FX-Dashboard/        ← Exchange rate tracking
├── PH-Regional-Inequality/ ← Socioeconomic disparity analysis
├── PH-Economic-Tracker/    ← GDP, inflation, macro indicators
├── PH-Labor-Analysis/      ← Employment & labor market data
└── PH-Price-Tracker/       ← Consumer price monitoring
```

</div>

---

<div align="center">

```svg
<!--
  Banner: paste this block into https://vecta.io/nano or any SVG renderer
  to preview — or let GitHub render it directly via the <img> tag below.
-->
```

<!-- SVG Banner (GitHub renders inline SVGs in README via img tag) -->
<img src="banner.svg" alt="PH-DEP project structure" width="100%"/>

</div>

> A monorepo consolidating Philippine macroeconomic and social data engineering projects.
> Each subfolder is a self-contained project with its own `README.md`, data pipeline,
> and analysis artifacts — imported via `git subtree` with full commit history preserved.

---

## Projects

### 📈 [PH-FX-Dashboard](./PH-FX-Dashboard)
Real-time and historical Philippine Peso exchange rate tracking across major currency pairs.

### 📊 [PH-Regional-Inequality](./PH-Regional-Inequality)
Socioeconomic disparity analysis across Philippine regions — income, HDI, poverty incidence.

### 🏦 [PH-Economic-Tracker](./PH-Economic-Tracker)
Macroeconomic indicator monitoring: GDP growth, inflation, BSP policy rates, trade balance.

### 👷 [PH-Labor-Analysis](./PH-Labor-Analysis)
Labor force participation, unemployment, underemployment, and sectoral employment trends.

### 🛒 [PH-Price-Tracker](./PH-Price-Tracker)
Consumer price index monitoring across commodity groups and regional markets.

---

## Repository Structure

Each project lives in its own subfolder and retains its independent commit history (imported via `git subtree add --squash`). The original source repositories remain active on GitHub.

| Project | Source Repo | Status |
|---|---|---|
| PH-FX-Dashboard | [raldisk/PH-FX-Dashboard](https://github.com/raldisk/PH-FX-Dashboard) | active |
| PH-Regional-Inequality | [raldisk/PH-Regional-Inequality](https://github.com/raldisk/PH-Regional-Inequality) | active |
| PH-Economic-Tracker | [raldisk/PH-Economic-Tracker](https://github.com/raldisk/PH-Economic-Tracker) | active |
| PH-Labor-Analysis | [raldisk/PH-Labor-Analysis](https://github.com/raldisk/PH-Labor-Analysis) | active |
| PH-Price-Tracker | [raldisk/PH-Price-Tracker](https://github.com/raldisk/PH-Price-Tracker) | active |

---

## Pulling Updates from Source Repos

```bash
git subtree pull --prefix=PH-FX-Dashboard \
  https://github.com/raldisk/PH-FX-Dashboard.git master --squash

git subtree pull --prefix=PH-Regional-Inequality \
  https://github.com/raldisk/PH-Regional-Inequality.git master --squash

git subtree pull --prefix=PH-Economic-Tracker \
  https://github.com/raldisk/PH-Economic-Tracker.git master --squash

git subtree pull --prefix=PH-Labor-Analysis \
  https://github.com/raldisk/PH-Labor-Analysis.git master --squash

git subtree pull --prefix=PH-Price-Tracker \
  https://github.com/raldisk/PH-Price-Tracker.git master --squash
```

---

*Built with Python · pandas · matplotlib · Philippine statistical sources (PSA, BSP, NEDA)*
