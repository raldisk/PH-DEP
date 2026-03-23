# 🇵🇭 PH-DEP — Philippine Data Engineering Projects

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,50:16213e,100:0f3460&height=180&section=header&text=PH-DEP&fontSize=52&fontColor=e94560&fontAlignY=38&desc=Philippine%20Data%20Engineering%20Projects&descAlignY=60&descColor=ffffff&animation=fadeIn" width="100%"/>

</div>

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

Each project lives in its own subfolder and retains its independent commit history, imported via `git subtree add --squash`. `PH-DEP` is the single source of truth for all projects.

| Project | Description | Status |
|---|---|---|
| PH-FX-Dashboard | Exchange rate tracking | active |
| PH-Regional-Inequality | Socioeconomic disparity analysis | active |
| PH-Economic-Tracker | Macro indicator monitoring | active |
| PH-Labor-Analysis | Labor market data | active |
| PH-Price-Tracker | Consumer price monitoring | active |

---

## Pulling Updates

```powershell
git subtree pull --prefix=PH-FX-Dashboard `
  https://github.com/raldisk/PH-FX-Dashboard.git master --squash

git subtree pull --prefix=PH-Regional-Inequality `
  https://github.com/raldisk/PH-Regional-Inequality.git master --squash

git subtree pull --prefix=PH-Economic-Tracker `
  https://github.com/raldisk/PH-Economic-Tracker.git master --squash

git subtree pull --prefix=PH-Labor-Analysis `
  https://github.com/raldisk/PH-Labor-Analysis.git master --squash

git subtree pull --prefix=PH-Price-Tracker `
  https://github.com/raldisk/PH-Price-Tracker.git master --squash
```

---

*Built with Python · pandas · matplotlib · Philippine statistical sources (PSA, BSP, NEDA)*
