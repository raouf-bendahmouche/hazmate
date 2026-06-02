# Statistics Module Documentation

The statistics module delivers real-time analytical insights into transport licensing, fleet categories, and municipality distributions. It supports default rolling timeline ranges and custom date filtering with dynamic scale adjustments.

---

## 1. Core Analytics Dashboard Features

The dashboard is structured into three distinct layers to optimize information hierarchy:

1. **KPI Cards**: Summarize active/expired licenses, vehicles, drivers, and carrier categories (public/private).
2. **Distribution Charts**:
   - **Municipality Distribution**: Pie chart showing top municipalities with licenses.
   - **Carrier Type Share**: Pie chart of public vs. private carriers.
   - **License Status Ratio**: Pie chart of active vs. expired licenses.
3. **Activity Over Time**: A dynamic line chart depicting license issuance trends and forecasted expiries.

---

## 2. Real-Time Rolling Modes vs. Custom Range Filter

The module operates in two core operational modes:

### A. Real-Time Dynamic Mode (Default)
When no custom range is active, the dashboard runs on automated rolling calculations computed relative to the current local calendar date:
- **Weekly**: Exactly the last 7 calendar days day-by-day (shifting dynamically as dates progress).
- **Monthly**: From the 1st of the current month until today.
- **Yearly**: From January 1 of the current year until today (grouped month-by-month).

### B. Custom Date Range Mode
By specifying a Start Date and End Date at the top of the panel and clicking **Apply**, the operator shifts the system into custom filtering mode:
- **Backend Recalculation**: The system executes targeted, parameterized database queries to recount, regroup, and calculate all KPI stats, carrier shares, and activity metrics. It is fully backend-driven to guarantee compliance data accuracy.
- **Granularity Scaling**: The time interval units on the x-axis of the Activity Over Time chart scale automatically based on the range:
  - **Daily**: If the duration is $\le 30$ days.
  - **Weekly**: If the duration is between $31$ and $180$ days.
  - **Monthly**: If the duration is $> 180$ days.

---

## 3. UI Buttons: Apply & Reset

The custom filter form features two standardized international buttons to handle state transitions:

1. **Apply Button (`btn_apply`)**:
   - Locales: **Apply** (EN) / **Appliquer** (FR) / **تطبيق** (AR)
   - Function: Validates the date fields (ensuring the End Date is not prior to the Start Date), sets `statsFilter` parameter values, and triggers `renderStatistics()` to perform the backend-driven recalculation.
2. **Reset Button (`btn_reset`)**:
   - Locales: **Reset** (EN) / **Réinitialiser** (FR) / **إعادة تعيين** (AR)
   - Function: Clears custom date inputs, resets `statsFilter` to default blank values, and reloads the dashboard to restore the real-time weekly/monthly/yearly rolling tabs.

---

## 4. Verification and Safety Rules

- **Range Chronology**: End Date cannot be earlier than Start Date. If validation fails, the UI throws a localized warning toast and blocks backend queries.
- **Cache Handling**: Standard dynamic dashboard queries use caching for rapid loads. Custom date range queries bypass the cache entirely to guarantee immediate recalculation of ad-hoc statistics.
