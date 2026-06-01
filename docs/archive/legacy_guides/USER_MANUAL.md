# Hazardous Material Transport License Management System - User Manual

## Table of Contents

1. [Getting Started](#getting-started)
2. [Main Dashboard](#main-dashboard)
3. [Data Entry](#data-entry)
4. [Searching Records](#searching-records)
5. [Statistics & Reports](#statistics--reports)
6. [Settings](#settings)
7. [FAQ](#faq)

---

## Getting Started

### Launching the Application

1. Navigate to the project folder
2. Run `python main.py` from the terminal
3. The application will launch with the main dashboard

### Language Selection

The application supports three languages:

- **English (EN)** - English interface
- **French (FR)** - French interface
- **Arabic (AR)** - Arabic interface with right-to-left layout (default)

To change language:

1. Click the language dropdown in the top menu
2. Select your preferred language
3. The interface will update immediately

---

## Main Dashboard

### Overview

The main dashboard displays:

- **Total Vehicles** - Count of all registered vehicles
- **Total Drivers** - Count of unique driver names in the system
- **Active Licenses** - Count of licenses not yet expired
- **Expired Licenses** - Count of licenses past their expiration date

### Main Menu Buttons

- **Add New Record** - Opens the data entry form
- **Search Records** - Search and view all transport records
- **Statistics** - View detailed charts and reports
- **Settings** - Configure system preferences
- **Refresh** - Update dashboard statistics

---

## Statistics & Reports

### Overview: The Redesigned Statistics Dashboard

The Statistics Page has been transformed into a professional, three-tier analytical dashboard. It provides deep insights into your operations at a glance, helping you make informed decisions quickly. The dashboard is designed to be fast, responsive, and easy to read.

---

### TIER 1: KPI CARDS (TOP SECTION)

This section gives you an instant snapshot of your entire operation with five key performance indicators (KPIs). Each card is color-coded for quick identification.

| Icon | Metric                | Description                                                              | Use Case                                                   |
| :--- | :-------------------- | :----------------------------------------------------------------------- | :--------------------------------------------------------- |
| 📊   | **Total Carriers**    | The total number of unique transport companies registered in the system. | Understand the overall size of your carrier network.       |
| ✅   | **Active Carriers**   | The number of carriers with at least one active, unexpired license.      | Gauge the health and operational capacity of your network. |
| ❌   | **Inactive Carriers** | The number of carriers with only expired or no licenses.                 | Identify carriers that may need follow-up or have churned. |
| 🏛️   | **Public Carriers**   | The count of carriers registered as "Public".                            | Analyze the composition of your public sector partners.    |
| 🏢   | **Private Carriers**  | The count of carriers registered as "Private".                           | Analyze the composition of your private sector partners.   |

---

### TIER 2: DISTRIBUTION CHARTS (MIDDLE SECTION)

This tier helps you understand the geographic and structural distribution of your carriers.

#### 📍 Bar Chart: Carrier Distribution by Municipality

- **What it shows:** A bar chart displaying the **top 10 municipalities** with the highest number of registered carriers.
- **How to use it:**
  - **Identify Key Hubs:** Quickly see which geographic areas have the highest concentration of transport activity.
  - **Resource Allocation:** Use this data to plan for regional inspections, support, or expansion.
  - **Market Analysis:** Understand where your operational footprint is strongest.

#### 🥧 Pie Chart: Carrier Type Distribution

- **What it shows:** A doughnut chart that visually breaks down the percentage of **Public vs. Private** carriers in your system.
- **How to use it:**
  - **Sector Balance:** Instantly grasp the balance between public and private sector involvement.
  - **Strategic Planning:** Inform decisions related to public-private partnerships or sector-specific outreach.
  - **Reporting:** Easily generate percentages for reports and presentations.

---

### TIER 3: ACTIVITY & COMPLIANCE (BOTTOM SECTION)

This tier is focused on analyzing trends over time and identifying potential compliance issues.

#### 📈 Line Chart: Activity Over Time

- **What it shows:** A line chart illustrating trends in new activity (e.g., new contracts or registrations) over a selected period.
- **Interactive Tabs:** You can switch the time view instantly by clicking the tabs:
  - **Daily:** Shows activity for the last 30 days.
  - **Weekly:** Shows activity for the last 12 weeks.
  - **Monthly:** Shows activity for the last 12 months.
- **How to use it:**
  - **Spot Trends:** Identify seasonal patterns, growth periods, or slowdowns.
  - **Measure Impact:** See the effect of new regulations or business initiatives on activity.
  - **Forecasting:** Use historical data to anticipate future workload.

#### 🏙️ Grouped Bar Chart: Compliance by Municipality

- **What it shows:** A grouped bar chart comparing the number of **Active (Green)** vs. **Inactive (Red)** carriers for each of the top 10 municipalities.
- **How to use it:**
  - **Pinpoint Problem Areas:** Immediately identify municipalities with a high ratio of inactive to active carriers.
  - **Targeted Enforcement:** Direct compliance and enforcement resources to areas that need it most.
  - **Data Quality:** A high number of inactive carriers may also indicate a need for data cleanup or follow-up.

---

### Key Features of the New Dashboard

- **Performance:** The dashboard loads almost instantly thanks to a 5-minute caching system on the backend. You always get fast data without waiting.
- **Responsiveness:** The layout automatically adjusts to fit your screen size, ensuring a great experience on any device.
- **Professional Design:** The clean, modern design makes data easy to interpret and visually appealing for presentations.

---

## Settings

### Configuring Email Notifications

The system can send email alerts for expiring licenses. To set this up:

1.  Go to **Settings** from the main menu.
2.  Fill in your SMTP server details:
    - **SMTP Server** (e.g., `smtp.gmail.com`)
    - **Port** (e.g., 587)
    - **Email Address** and **Password** for the sending account.
    - **Recipient Email** where notifications should be sent.
3.  Click **"Send Test Email"** to verify your settings.
4.  Click **"Save Settings"**.

### Backup

- **Backup Folder:** Choose a folder where the system will automatically save database backups.
- It is highly recommended to set up regular backups to prevent data loss.

---

## FAQ

**Q: How often is the statistics data updated?**  
A: The data is cached for 5 minutes. After 5 minutes, it will automatically refresh on your next visit to the statistics page. You can also force a refresh by restarting the application.

**Q: Can I export the charts to a PDF or image?**  
A: Currently, the application does not have a built-in export feature. You can use your computer's screenshot tool to capture images of the charts.

**Q: Why are some carriers showing as "Inactive"?**  
A: A carrier is marked as inactive if all of its associated licenses have expired. This is a key indicator for compliance checks.

### Saving Records

1. Fill all required fields (marked with \*)
2. Click "Save Record" button
3. Confirmation message will appear
4. New record is added to the database

### Editing Records

1. Use Search Records to find the record
2. Click the "Edit" button on the record
3. Modify desired fields
4. Click "Save Changes"

---

## Searching Records

### Basic Search

1. Click "Search Records" from the main dashboard
2. Use the search bar to find records by:
   - Record Number
   - Vehicle Registration
   - Company Name
   - Driver Name

3. Results appear automatically as you type
4. Click "Search" button to perform full search

### Filters

Apply filters to narrow results:

- **Status Filter** - Active or Expired licenses
- **Carrier Type Filter** - Filter by company type

### Record Actions

For each record in search results:

- **Edit** - Modify record details
- **Delete** - Remove record from system (with confirmation)
- **View Details** - See full record information

### Exporting Results

Records can be exported for external use:

1. Perform a search
2. Right-click on results table
3. Select "Export to CSV" option
4. Choose save location

---

## Statistics & Reports

### Overview: The Redesigned Statistics Dashboard

The Statistics page has been fully redesigned as a **professional three-tier analytical dashboard** to provide clear, actionable insights at a glance. All data is cached for performance, ensuring fast loading even with large datasets.

---

### Dashboard Structure

#### **TIER 1: KPI CARDS (Top Section)**

Five key performance indicator cards provide an instant snapshot of your carrier network:

| Card                     | Description                                     | Use Case               |
| ------------------------ | ----------------------------------------------- | ---------------------- |
| **📊 Total Carriers**    | Complete count of registered carriers in system | Network size indicator |
| **✅ Active Carriers**   | Carriers with at least one active license       | Operational capacity   |
| **❌ Inactive Carriers** | Carriers with no active licenses                | Dormant accounts       |
| **🏛️ Public Carriers**   | Government-owned or public transport operators  | Sector analysis        |
| **🏢 Private Carriers**  | Privately-owned operators                       | Sector analysis        |

**What to do:** Use these metrics to quickly assess system health and identify trends at a glance.

---

#### **TIER 2: DISTRIBUTION CHARTS (Middle Section)**

Two professional charts show resource allocation patterns:

**Chart 1: Carriers per Municipality (Bar Chart)**

- **X-axis:** Municipality names (top 10 by volume)
- **Y-axis:** Number of carriers in each municipality
- **Why:** Identifies geographic concentration and distribution patterns
- **Action:** Target under-served regions for recruitment or compliance checks

**Chart 2: Public vs Private Distribution (Pie Chart)**

- **Shows:** Percentage split between public and private carriers
- **Labels:** Exact carrier count and percentage for each type
- **Why:** Understand market composition and dependency on private logistics
- **Action:** Plan policy initiatives based on sector dominance

**How to interact:**

- Hover over any bar or pie slice for detailed information
- Charts update automatically based on current data
- No manual refresh needed

---

#### **TIER 3: ACTIVITY & COMPLIANCE (Bottom Section)**

Two comprehensive charts track operational patterns and regulatory compliance:

**Chart 1: Transport Activity Trend (Line Chart)**

- **Features:** Dynamic time period selector (Daily | Weekly | Monthly)
  - **Daily:** Last 30 days (granular view)
  - **Weekly:** Last 12 weeks (trend analysis)
  - **Monthly:** Last 12 months (seasonal patterns)
- **Shows:** Carrier activity over time
- **Why:** Identify peak operational periods, seasonal trends, and anomalies
- **Action:** Plan maintenance, staffing, and enforcement activities accordingly

**How to use:**

1. Click one of the period buttons above the chart
2. Chart reloads with the selected time granularity
3. Hover over data points to see exact values and dates

**Chart 2: Active vs Inactive per Municipality (Grouped Bar Chart)**

- **Green bars:** Active carriers per municipality
- **Red bars:** Inactive carriers per municipality
- **Correlates:** Geography with compliance status
- **Why:** Identify municipalities with high compliance issues
- **Action:** Target specific regions for regulatory enforcement or support

---

### Key Features

#### **Performance (Caching)**

- Statistics data is cached for 5 minutes
- Subsequent loads within the cache window are instant
- Cache automatically refreshes when expired

#### **Responsiveness**

- Charts adapt to window size
- Works seamlessly on different screen resolutions
- Touch-friendly on touchscreen devices

#### **Professional Design**

- Clean, modern aesthetic
- High-contrast color scheme for readability
- Consistent with system design language

---

### How to Use Statistics for Different Purposes

| Purpose               | Which Chart                         | What to Look For                               |
| --------------------- | ----------------------------------- | ---------------------------------------------- |
| **Compliance Audit**  | Active vs Inactive per Municipality | Red bars (inactive carriers needing follow-up) |
| **Regional Planning** | Carriers per Municipality           | Geographic distribution; under-served areas    |
| **Seasonal Planning** | Activity Trend (Monthly view)       | Peaks and troughs in operations                |
| **Market Analysis**   | Public vs Private Pie               | Sector dominance and dependency                |
| **Daily Operations**  | Activity Trend (Daily view)         | Current activity levels                        |
| **Annual Report**     | All charts                          | Comprehensive system overview                  |

---

### Tips for Best Results

✅ **Do:**

- Use daily view for immediate operational decisions
- Switch to monthly view for strategic planning
- Check statistics weekly to track trends
- Use active/inactive chart to identify compliance issues

❌ **Don't:**

- Make long-term decisions based on daily fluctuations
- Ignore red (inactive) indicators
- Rely on cached data older than 5 minutes for urgent decisions

---

## Settings

### User Settings

Access application preferences:

1. Click "Settings" from the main dashboard
2. Configure the following options:

#### Language

- Select default interface language
- Changes apply immediately

#### Email Notifications

- **SMTP Server** - Enter mail server address
- **Email Port** - Port number (typically 587)
- **Email Address** - Sender email for notifications
- **Password** - Authentication password

#### Database

- **Backup Location** - Where backups are saved
- **Auto-backup** - Enable/disable automatic daily backups

### Saving Settings

1. Make desired changes
2. Click "Save Settings" button
3. Confirmation message appears
4. Settings take effect immediately

---

## FAQ

### General Questions

**Q: What is the default language?**  
A: Arabic (AR) is the default language, but can be changed anytime.

**Q: How do I backup my data?**  
A: Go to Settings and configure backup location. Automatic daily backups can be enabled.

**Q: How many records can the system handle?**  
A: The system efficiently handles thousands of records with sub-second search and retrieval times.

### License Management

**Q: What does "Active" status mean?**  
A: An active license has not yet passed its expiration date.

**Q: What does "Expired" status mean?**  
A: An expired license has passed its expiration date and is no longer valid.

**Q: How often is status automatically updated?**  
A: License status is updated automatically when you view statistics or perform a search.

**Q: What if I need to reactivate an expired license?**  
A: Edit the record and change the expiration date to a future date.

### Search & Records

**Q: Can I search by partial information?**  
A: Yes, the search accepts partial matches for all fields.

**Q: What happens when I delete a record?**  
A: The record is permanently removed along with all associated data (company, vehicle, routes).

**Q: Is there a way to undo a deletion?**  
A: Deletions are permanent. Always ensure you have recent backups.

### Statistics

**Q: How far back do statistics go?**  
A: Daily: 30 days, Weekly: 12 weeks, Monthly: 12 months.

**Q: Can I export statistics?**  
A: Statistics charts can be saved by taking screenshots. Data can be exported via the search functionality.

**Q: Why are transport numbers different from license counts?**  
A: Transport statistics count records by signature date, while license statistics count unique licenses.

### Technical

**Q: Is my data stored locally or in the cloud?**  
A: All data is stored locally on your computer in a SQLite database for maximum security.

**Q: Do I need internet connection to use the system?**  
A: No, the system works completely offline, though email notifications require internet access.

**Q: What if the application crashes?**  
A: Your data is safe. Restart the application and your data will remain intact. Use backups if needed.

---

## Best Practices

### Data Entry

- Always verify driver and vehicle information before saving
- Use consistent company naming conventions
- Ensure dates are entered correctly (DD/MM/YYYY format)

### Search & Organization

- Use record numbers consistently for easy searches
- Regularly search for expired licenses
- Keep vehicle registrations up to date

### Maintenance

- Perform monthly backups in addition to automatic backups
- Review statistics quarterly for compliance
- Archive old records periodically

### Security

- Keep your computer password protected
- Restrict access to the application
- Store backups securely
- Don't share database files

---

## Contact & Support

For technical assistance or questions:

- Contact your system administrator
- Refer to the Technical Documentation
- Check this manual's FAQ section

---

**Version 1.0 - License Management System**  
**Last Updated: April 2026**

---

## April 2026 Operational Updates (Mandatory)

### 1) Deleted Contracts Page

- **What changed:** A dedicated **Deleted Contracts** page was added.
- **Why changed:** Deleted contracts must be managed separately from active contracts.
- **How it works:** The page only lists contracts where deletion flag is enabled.
- **How to use:**
  1.  Open **Deleted Contracts** from the left menu.
  2.  Search by contract ID, company, driver, or vehicle.
  3.  Filter by municipality, contract type, and status before deletion.
  4.  Click **Restore Contract** to return the contract to active records.

### 2) Quantity Removal from Hazardous Material Entry

- **What changed:** The **Quantity** field was removed from forms and screens.
- **Why changed:** Regulatory authority only requires material type, not quantity.
- **How it works:** System stores hazardous material type without quantity data.
- **How to use:** Enter only hazardous material type when applicable.

### 3) Navigation Label Update

- **What changed:** Data entry menu label is now standardized as **Add Contract**.
- **Why changed:** Improve naming consistency and reduce operator confusion.
- **How it works:** Label is translated dynamically based on selected language.
- **How to use:** Use **Add Contract** to open contract creation form.

### 4) Statistics Enhancements

- **What changed:** Statistics now include carrier-focused analytics.
- **Why changed:** Support planning and municipality-level decision making.
- **How it works:** The page shows:
  - Total carriers / Public carriers / Private carriers
  - Active vs inactive carriers
  - Carriers by municipality with percentages
  - Bar and pie style visual indicators
- **How to use:** Open **Statistics** and review global and municipality sections.

### 5) Strict Real-Time Validation

- **What changed:** Input validation now runs while typing.
- **Why changed:** Prevent invalid records from being saved.
- **How it works:**
  - Numeric-only fields reject letters.
  - Name fields reject numbers.
  - Errors are displayed in red below each field.
  - Save is blocked until all validation errors are fixed.
- **How to use:** Correct each highlighted field until no red error remains.

### 6) Default Dashboard Routing

- **What changed:** The initial "Welcome" page was bypassed.
- **Why changed:** To provide immediate access to actionable data and speed up the workflow.
- **How it works:** When launching the application, the system automatically routes to the **Dashboard** page by default.
- **How to use:** Simply open the application. No further action is required.

## Simplified System Modules Explanation
* **Dashboard Module:** Shows key metrics and numbers at a glance.
* **Data Entry Module (Add Contract):** Where you input new carrier and license details.
* **Search Module:** Allows you to find, edit, or delete existing records.
* **Statistics Module:** Provides deep analytical charts and graphs for management.
* **Settings Module:** Configure emails, backups, and app language.

**How user interacts with system:**
You interact with a modern graphical interface (Electron). When you save or search, the interface secretly asks the local Python engine for data, which pulls it securely from your local SQLite database file. Everything stays on your computer!
