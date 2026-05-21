# hazmate Analytics Dashboard Documentation

## Overview

The Analytics Dashboard has been rolled back to its **previous stable version (v1.0)**. The recent advanced data visualization enhancements were removed to prioritize dashboard performance, simplify the user experience, and prevent cognitive overload for standard administrative workflows.

### Rollback Details

- **What was removed:** `Recharts` SVG sparklines in KPI cards, Dual Y-axis ComposedChart, Top Products Bar Chart, Orders by Wilaya Progress List, Activity Timeline, and heavy client-side sorting logic in the data table.
- **Why rollback was performed:** The advanced visualizations caused visual clutter, layout shifts on lower-end devices, and overcomplicated the core workflow. Restoring the original dashboard ensures maximum stability and readability.
- **Version restored:** Dashboard Layout v1.0.

## Core Visualizations

### 1. KPI Cards

- **What it shows:** Key Performance Indicators (Total Revenue, Total Orders, Refunds).
- **Design:** Minimalist cards displaying the primary value and a simple text-based percentage change indicator (colored red/green).
- **Insight:** Allows the admin to quickly grasp business health at a single glance without heavy UI rendering.

### 2. Revenue Trend (Simple Line Chart)

- **What it shows:** The temporal progression of Revenue over time.
- **Design:** A standard single-axis Line Chart.
- **Insight:** Highlights growth and seasonal spikes cleanly.

### 3. Basic Order Data Table

- **What it shows:** Granular transaction data.
- **Design:** Clean, spaced tabular layout with basic status-specific colored badges (e.g., Delivered is Green, Cancelled is Red).
- **Insight:** Enables deep-dives into individual transactions for customer support and fulfillment tracking.

## Technical Architecture

- **State Management:** Handled locally within the dashboard (`loading`, `error`, `empty`, `success`) preventing UI flashing and ensuring graceful fallbacks.
- **RTL Support:** Uses standard Tailwind logical classes (`ms-`, `pe-`, `rtl:text-right`, `rtl:space-x-reverse`) and the standard `dir="auto"` attribute ensuring right-to-left languages like Arabic render accurately without breaking chart constraints.
- **Visual Design Rules Applied:** Strict adherence to modern spacing, rounded corners (`rounded-xl`), soft borders (`border-gray-100`), and contextual color meaning (Green = Positive, Red = Negative, Blue = Neutral).
