# System Localization Guide

This document describes the design, implementation, and maintenance of the multi-language localization framework in the Hazardous Material Transport License Management System.

---

## 1. Terminology Standardization: "Apply" & "Reset"

To align the analytics dashboard and search interfaces with modern international UI/UX design paradigms, we have standardized the filtering controls to **Apply** and **Reset**.

- **Why "Apply" and "Reset" were chosen**:
  - Legacy labels like "Filter" (French: *Filtrer*, Arabic: *تصفية*) focus on the category of the action, whereas **Apply** (French: *Appliquer*, Arabic: *تطبيق*) specifies the execution of the selected parameter set (the custom date range) and dynamically updates downstream visualization.
  - **Reset** (French: *Réinitialiser*, Arabic: *إعادة تعيين*) represents returning the system state to its default rolling operational metrics (e.g., weekly statistics representing the last 7 calendar days), rather than merely clearing the date fields visually.
  - These terms align cleanly with standard dashboard UI vocabularies, ensuring that the system is intuitive for bilingual and trilingual operators.

---

## 2. Localization Infrastructure (`i18n.js`)

The localization system uses a lightweight, client-side dictionary-based routing structure without heavy external libraries.

### Dictionary Architecture
Translations are defined in `frontend/js/i18n.js` inside a global `TRANSLATIONS` object supporting:
- **English (`en`)**: LTR directionality.
- **French (`fr`)**: LTR directionality.
- **Arabic (`ar`)**: RTL directionality.

Each language block specifies:
1. `dir`: Sets the text directionality (`ltr` or `rtl`).
2. Label translations: Map unique semantic keys (e.g., `btn_apply`, `lbl_start_date`, `err_invalid_date_range`) to localized values.

### Directionality (RTL/LTR Support)
When a language is selected, the application automatically handles structural layouts by altering the DOM metadata:
```javascript
document.documentElement.lang = currentLang;
document.body.dir = tr.dir;
```
This updates layout styling instantly. Flexbox grids, icon alignments, margins, padding offsets, and cards dynamically flip mirroring standard RTL styles.

---

## 3. System-wide UI Synchronization

System-wide UI translation consistency is maintained through a dynamic notification-refresh loop.

### Lifecycle of a Language Change
1. **Selection**: The user clicks a language preference button in the Settings page.
2. **State Updates**: The controller calls `setLanguage(lang)`, which persists the setting to `localStorage` under `"lang"`.
3. **DOM Scanning**: `applyLanguage()` scans the DOM for elements containing the attributes `data-i18n` or `data-i18n-ph` and replaces their text contents/placeholders inline using `t(key)`.
4. **App Title Synchronization**: The browser/electron tab title is updated on language change:
   ```javascript
   document.title = t('app_title');
   ```
5. **Event Propagation**: `applyLanguage()` dispatches a global `"langchange"` event:
   ```javascript
   document.dispatchEvent(new Event("langchange"));
   ```
6. **Re-rendering**: The main controller listens for `"langchange"` and calls `renderCurrentPage()`. This refreshes dynamic sections (such as charts, lists, and pages loaded dynamically like `welcome.html`) instantly using the new language dictionary.

---

## 4. Detection and Correction of Translation Mismatches

To ensure that the application remains free of mixed-language UI fragments:
- **Fallback Rule**: The translation translation helper `t(key)` uses a defensive fallback chain:
  ```javascript
  function t(key) {
    return (TRANSLATIONS[currentLang] || TRANSLATIONS.en)[key] || key;
  }
  ```
- **Auditing Rule**:
  - UI developers should avoid inline strings inside templates and templates literals. Every label should wrap in a `t('key')` helper.
  - Custom dynamic page templates, such as `welcome.html`, must use the `data-i18n` attributes. Upon content insertion via `innerHTML`, the DOM must parse those elements:
    ```javascript
    el.content.querySelectorAll("[data-i18n]").forEach(subEl => {
        subEl.textContent = t(subEl.getAttribute("data-i18n"));
    });
    ```
