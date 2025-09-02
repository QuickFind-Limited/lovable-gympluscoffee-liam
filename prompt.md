# OVERVIEW: What This Prompt Does

This prompt instructs an AI system with Odoo ERP access to completely replace unrealistic linear sales data with authentic-looking synthetic transaction data for Gym+Coffee, an athletic lifestyle brand. The current problem is that the existing data shows perfectly smooth growth lines which never happen in real retail - actual businesses experience daily chaos, seasonal patterns, promotional spikes, random events, and complex customer behaviors. This comprehensive prompt creates 4 months of summer sales data (June-September) plus 6 months of historical context, generating individual SKU-level transactions that mirror real retail operations. The data will include proper channel distribution (60% online, 20% retail stores, 20% wholesale), geographic spread (UK 50%, US 20%, Australia 20%, Ireland 10%), realistic return rates (20-27% for online, 4-9% for retail), and natural volatility with week-to-week variance of 20-30%. The prompt ensures every active product in inventory gets appropriate sales volumes based on real-world patterns where top 20% of products drive 60-75% of revenue, and includes specific events like July 4th US sales spikes and UK August Bank Holiday promotions.

## Key Components Explained:

### **Data Volume & Scope**

- Generates approximately 65,000 individual sales transactions over 4 months
- Additional 6 months of historical data at lower density for context
- Each transaction links to real SKUs (and data relating to it) in Odoo inventory you generated.
- Includes timestamps down to the hour, not just dates
- Covers all active products with realistic frequency

### **Customer Modeling**

- Creates ~35,000 unique customer records
- 28-32% are repeat buyers (realistic for apparel)
- 68-72% buy only once in the period
- Customer segments: VIP (5%), Loyal (15%), Regular (30%), One-time (50%)
- Cross-channel shoppers who buy both online and in-store (10-15%)
- BOPIS (Buy Online Pick-up In Store) represents 5-9% of online orders

### **Revenue & Order Values**

- Online orders average €90-120 per transaction
- Retail store orders average €70-100
- B2B wholesale orders average €500-2,500+
- Individual consumers buy 1-3 items per order
- Wholesale buyers purchase 10-100 units per SKU
  *Making sure that orders can be no lower than the price baselines pulled from SKUs within the current inventory we previously have sotred in Odoo, the transaction examples MUST consist of current SKUs and be calculated in that way as such per transaction*

### **Channel Distribution Requirements**

- **D2C E-commerce (60% of revenue)**: Website orders shipped to customers
- **Retail Stores (20% of revenue)**: In-person purchases at physical locations
- **B2B Wholesale (20% of revenue)**: Bulk orders from business partners
- Each channel has distinct patterns (online peaks at lunch/evening, retail on weekends)

### **Geographic Authenticity**

- **United Kingdom**: 50% of all orders
- **United States**: 20% of orders (with July 4th and Labor Day spikes)
- **Australia**: 20% of orders (opposite seasons considered)
- **Ireland**: 10% of orders
- Time zones respected for order timing
- Local holidays and events included

### **Product Performance Patterns**

- Top 20% of SKUs generate 60-75% of revenue (Pareto principle)
- Summer items (t-shirts, shorts) sell more June-August
- Size distribution: S (18-22%), M (28-35%), L (23-28%), XL (12-18%)
- Black/grey/navy colors dominate (60%+)
- Every SKU with inventory must appear at least once

### **Seasonal & Promotional Events**

- July 4-7: US Independence Day sale (+25% US traffic)
- Mid-July: Global flash sale (2-3 days)
- Late August: UK Bank Holiday weekend spike
- Early September: Labor Day (US) promotion
- Week-to-week variance of ±20-30% (never smooth growth)
- Random spikes and dips to simulate real chaos

### **Returns & Exchanges**

- Online return rate: 20-27% of orders (industry standard for apparel)
- Retail return rate: 4-9% (much lower for in-person)
- B2B return rate: 1-2% (mainly for defects)
- Returns happen 5-15 days after purchase
- Reasons: Size/fit (majority), style/color, quality, changed mind
- Includes partial returns and exchanges

### **Time Patterns**

- **Daily**: Lunch peak (1-2 PM) and evening peak (7-10 PM) for online
- **Weekly**: Saturdays strongest for retail, mid-week dips
- **Monthly**: Payday effects on 1st-5th and 15th-19th
- **Hourly**: Detailed distribution throughout each day
- No overnight orders (realistic maintenance windows)

### **Data Quality Controls**

- Channel mix must be within ±2-3% of targets
- Geographic distribution verified against requirements
- Return rates checked against industry benchmarks
- Volatility validated (no more than 3 days of linear growth)
- Every active SKU must have sales
- All returns link to original orders
- Inventory never goes negative

### **Technical Odoo Integration**

- Uses actual sale.order and sale.order.line objects
- Creates proper stock.picking records for fulfillment
- Generates account.move entries for invoices
- Implements stock.return.picking for returns
- Links to real customer (res.partner) records
- Updates inventory levels appropriately
  *PLEASE HEAVILY NOTE HERE THAT ITS UP TO YOU AS THE ADAVANCED AGENT ORCHESTRATION AI, TOO MAKE SURE THAT YOU INPUT THIS DATA INTO ODOO VIA THE MCP AND KEEP TRYING UNTIL IT IS PUT IN THE CORRECT PLACE VIA YOUR AGENTS YOU DEPLOY TO COMPLETE THESE TASKS, MEANING THAT YOU SHOULDNT INEHERENTLY ASSUME THESE STORTS OF COMMANDS OR locations for data will be correct BY DEFAULT via deployed agents you should actively seek if this is true and make sure it goes to the right place, trying different ways and validating along the way,*

### **Multi-Agent Processing**

- Deploys multiple AI agents working in parallel
- Each agent handles specific aspects (customers, products, channels, placement into Odoo, matching, etc, et)
- Deploy agents to make sure you cover the number of customer records requested.
- Coordinator agent ensures consistency
- Prevents system overload and ensures complete SKU coverage
- Validates all constraints before final output
- If the number of records is unrealistic, make sure the user knows, we are optimizng for quality, if we had to reduce the number of records by half so we could increase quality this could be possible but would require user permission. 

---

# Replace Linear Synthetic Sales With Realistic in Odoo, SKU-Level Retail Data (Gym+Coffee)

**Why you are being reprompted:** The sales data currently in Odoo (see dashboard) is **implausibly linear** over time. Real retail/D2C/B2B sales show volatility by week/day/hour, seasonal spikes, returns, and uneven SKU performance. Replace that dataset with **credible, per-SKU transactions** that reflect how an athleisure brand like Gym+Coffee actually sells.

## 0) System context you already have

- You have **full read/write access** to Odoo's live **inventory SKUs, variants (size/color), categories, list prices, tax profiles, warehouses, stores, and partners**.
    
- Generate **individual orders** linked to **real SKUs**; do **not fabricate** product IDs.
    
- Base currency can be EUR; enable multi-currency if configured in Odoo.

- Also make sure the CORRECT applications are installed In Odoo so this data can be accessed by the user is needed at any given time, 
    

---

## 1) Scope & period

- **Primary generation window:** **June 1 – September 30 (4 months, summer).**
    
- **Historical backfill for realism:** also **seed the six months _prior_ to June** (Dec–May) at **lower daily density (30–40% of summer volume)** to create purchase history for repeat buyers, natural trend baselines, and realistic stock movements.
    
- Produce **daily transactions (including weekends)** with **time stamps**, not just dates.
    

---

## 2) Channel, geography, customer mix (hard constraints)

- **Channel split (by revenue & order count):**
    
    - **D2C e-commerce:** **60%**
        
    - **Retail (own stores):** **20%**
        
    - **B2B/Wholesale:** **20%**
        
- **Geography (by orders and revenue):** **UK 50%**, **US 20%**, **AU 20%**, **IE 10%**.
    
    - Assign **store-channel orders to real store locations** you find in Odoo. Heavier weight to flagship/high-traffic stores.
- **Customer behavior:**
    
    - **Repeat buyers:** **~28–32%** of customers place ≥2 orders in summer; schedule some to buy monthly, others every 60–90 days.
        
    - **One-time buyers:** **~68–72%**.
        
    - Model **cross-channel shoppers** (~10–15%) and **BOPIS/click-and-collect** for online orders **~5–9%** of D2C (mark as fulfillment method), with prevalence during peak events. ([Fit Small Business](https://fitsmallbusiness.com/bopis-statistics/ "30 Buy Online, Pick Up In-store (BOPIS) Statistics"))
        

---

## 3) Value & basket realism (calibrated to apparel norms & your price book)

1. **Use Odoo list_price per SKU**; apply taxes/discounts based on promos. Respect min price points in your catalog (e.g., **low-price items ≈ €60**), and allow occasional high-value baskets (e.g., **€300–€400** for premium/bundled fits).
    
2. **Target AOV bands (pre-tax, post-discount; tune to list prices):**
    
    - **D2C online:** typical apparel **€90–€120** (allow 70–150 interquartile).
        
    - **Retail stores:** **€70–€100**.
        
    - **B2B orders:** **€500–€2,500+** (via bulk quantities/lines).  
        _(These bands reflect apparel benchmarks where ecommerce AOV ≈ $120 and B2B is materially higher.)_ ([eCommerce DB](https://ecommercedb.com/benchmarks/ww/apparel?utm_source=chatgpt.com "Global Apparel eCommerce Benchmarks - AOV, Conversion rate, ... - ECDB"), [eFulfillment Service, Inc.](https://www.efulfillmentservice.com/2024/04/b2b-vs-b2c-fulfillment-key-differences-explained/?utm_source=chatgpt.com "B2B vs. B2C Fulfillment: Key Differences Explained"))
        
3. **Line-item quantities:**
    
    - D2C/Retail: mostly **qty 1** per SKU; sometimes 2–3.
        
    - B2B: **qty 10–100** per SKU; multi-SKU lines favored.
        

---

## 4) Seasonality, volatility & calendared events (no linear curves)

- **Monthly shape (example target share of summer revenue):** June ~20–23%, July ~24–27%, August ~27–31% (peak), September ~22–26%.
    
- **Week-to-week variance:** **±20–30%** vs prior week.
    
- **Day-of-week:** weekend bias for Retail (Sat strongest), and softer mid-week dips.
    
- **Time-of-day (for D2C):** lunch **13:00–14:00** and evening **19:00–22:00** are peaks; spread remaining demand across other hours to look natural. ([Oberlo](https://www.oberlo.com/statistics/what-time-do-people-shop-online?utm_source=chatgpt.com "What Time Do People Shop Online? [Updated Apr 2023] | Oberlo"), [ECDB](https://ecdb.com/blog/online-shopping-habits-the-golden-hours-of-ecommerce/4462?utm_source=chatgpt.com "The Golden Hours of eCommerce: Online Shopping Days Worldwide"))
    
- **Summer promo/holiday spikes** (apply channel- and geo-specific weighting, price cuts, and inventory depletion):
    
    - **Early July (US):** 4–7 July **Independence Day** offers: +US D2C traffic; modest AOV dip from discounts.
        
    - **Mid-July:** 2–3-day flash sale (global) with +orders / −AOV.
        
    - **Late Aug (UK/IE):** **Summer Bank Holiday** (last Monday of Aug) long-weekend uplift for UK/IE Retail & D2C. ([Britishheadline](https://britishheadline.co.uk/august-bank-holiday-2025/?utm_source=chatgpt.com "August Bank Holiday 2025: UK's End-of-Summer Tradition"), [Retail Times](https://retailtimes.co.uk/sunshine-and-sales-august-bank-holiday-set-to-brighten-retail-and-hospitality-with-600m-boost/?utm_source=chatgpt.com "Sunshine and sales: August bank holiday set to brighten retail and ..."))
        
    - **Early Sept (US):** Labor Day weekend bump.
        
- **Pay-cycle effects:** gentle lift around 1–5 and 15–19 each month.
    
- **Non-promo noise:** random weather/event dips and micro-spikes so charts are jagged, not smooth.
    

---

## 5) SKU mix, sizes, colors (sell-through realism)

- **Map all SKUs** to categories and variants (size/color).
    
- **Pareto shape:** the **top ~20% SKUs drive ~60–75%** of revenue; remaining SKUs sell occasionally (long tail).
    
- Summer-weight bias: tees, tanks, shorts, lightweight hoodies outperform; heavy fleece lags until September.
    
- **Size curve** (tune to your customer base/inventory): approximately **S 18–22%**, **M 28–35%**, **L 23–28%**, **XL 12–18%**, **XS/XXL remainder**.
    
- **Color demand:** neutrals (black/grey/navy) dominate; brights seasonal.
    
- **Coverage requirement:** **every active SKU** appears at least once **if stocked**, with frequency proportional to price point, seasonality, and available quantity.
    

---

## 6) Returns, exchanges, cancellations (Odoo-native flows)

- **Channel return rates (summer apparel reality):**
    
    - **D2C online:** **~20–27% of orders** develop a return (bracketing/fit). ([Coresight Research](https://coresight.com/research/the-true-cost-of-apparel-returns-alarming-return-rates-require-loss-minimization-solutions/?utm_source=chatgpt.com "The True Cost of Apparel Returns: Alarming Return Rates Require Loss ..."), [eCommerce DB](https://ecommercedb.com/benchmarks/ww/apparel?utm_source=chatgpt.com "Global Apparel eCommerce Benchmarks - AOV, Conversion rate, ... - ECDB"))
        
    - **Retail:** **~4–9%**. ([Capital One Shopping](https://capitaloneshopping.com/research/average-retail-return-rate/?utm_source=chatgpt.com "Average Retail Return Rate (2025 Data): eCommerce vs In-Store"))
        
    - **B2B:** **~1–2%**, often partial (damaged/late).
        
- **Return timing:** usually **5–15 days** post-purchase; 60% within first week after delivery.
    
- **Return types:** full, **partial**, or **exchange** (size/color). Exchanges re-book revenue on the new SKU; returns generate credit notes.
    
- **Reasons mix:** size/fit dominant; then style/color, defect/quality, changed mind.
    
- **Cancellation rate:** **0.5–1.5%** of orders (payment failure, duplicate, OOS).
    
- **Odoo mapping:**
    
    - **sale.order / sale.order.line** → original order.
        
    - **stock.picking (outgoing)** → fulfillment; **tracking_number**, carrier.
        
    - **account.move (invoice)** → customer invoice; payments applied.
        
    - **Return** via **RMA**: create **stock.return.picking** (incoming) + **account.move reversal** (credit note).
        
    - Mark **return_reason**, **refund_method**, **restock flag** (return to stock vs. damaged).
        

---

## 7) Data fields to output (CSV import-ready)

Create **two tables** (orders & customers) plus an optional **daily KPI rollup**. Use consistent IDs and linkages.

**A) Orders / order lines**

```
order_id, order_date, order_time, channel, store_location, 
customer_id, customer_name, customer_email, customer_type[Consumer|B2B], 
segment[VIP|Loyal|Regular|One-Time], fulfillment_method[Ship|BOPIS|Curbside], 
country, city, 
sku, product_name, category, size, color, quantity, 
unit_price, discount_percent, discount_amount, subtotal, tax_rate, tax_amount, 
shipping_fee, total_amount, currency, 
payment_method, payment_status, payment_terms, 
invoice_id, picking_id, tracking_number, 
order_status[Completed|Cancelled|Returned|Exchanged], 
return_flag, return_id, original_order_id, return_date, return_reason, refund_amount, 
promotion_code, promotion_name, acquisition_source, device_type
```

**B) Customers (for repeat logic & segmentation)**

```
customer_id, first_name, last_name, email, phone, 
type[Consumer|B2B], segment[VIP|Loyal|Regular|One-Time], 
registration_date, first_purchase_date, last_purchase_date, 
total_orders, total_spent, average_order_value, 
favorite_category, preferred_size, preferred_channel, 
city, country, lifetime_value
```

**C) (Optional) Daily performance**

```
date, total_orders, total_revenue, unique_customers, new_customers, returning_customers, 
online_orders, retail_orders, b2b_orders, aov, return_rate, promo_flag, top_selling_sku
```

---

## 8) Generation steps (multi-pass)

1. **Inventory pass:** pull all SKUs/variants, categories, list prices, stock-on-hand; mark discontinued/OOS.
    
2. **Tiering:** classify SKUs into **Hero (≈20%) / Core (≈30%) / Long Tail (≈50%)**; assign sales weights accordingly.
    
3. **Customer graph:** synthesize **unique customers** (enough to support volumes) with **~28–32% repeat**, segmented as: VIP (~5%), Loyal (~15%), Regular (~30%), One-time (~50%). VIP/Loyal get higher AOV & promo engagement.
    
4. **B2B accounts:** create a realistic set of wholesale partners (tiers with monthly quotas); **month-end clustering** and **Net 30** terms.
    
5. **Calendar modeling:** generate daily targets using Section 4 rules (week/weekday/hour curves + events).
    
6. **Basket assembly:** select SKUs per channel using Section 5 weights; D2C/Retail mostly 1–3 lines; B2B multi-line bulk. Respect sizes/colors and store inventory.
    
7. **Pricing & promos:** apply event-specific discounts (10–30%); track promo codes & promo names.
    
8. **Fulfillment:** generate pickings/shipments (and BOPIS handoffs), tracking numbers, carriers; delay delivery relative to order date by realistic transit times per country.
    
9. **Returns & exchanges:** create linked RMAs/credit notes with reasons and exchange lines; restock if appropriate.
    
10. **QA/validation** (see below); then write CSVs and (optionally) bulk-import via Odoo importers.
    

---

## 9) Guardrails & acceptance tests (auto-validate before finalizing)

- **Channel mix** within **±2–3 pp** of **60/20/20** by revenue.
    
- **Geo mix** meets **UK 50 / US 20 / AU 20 / IE 10** ±2 pp each.
    
- **AOVs** fall in Section 3 ranges; **distribution is right-skewed** (not narrow).
    
- **Repeat rate** within **28–32%**; **BOPIS 5–9%** of D2C. ([Fit Small Business](https://fitsmallbusiness.com/bopis-statistics/ "30 Buy Online, Pick Up In-store (BOPIS) Statistics"))
    
- **Returns**: overall rates per channel in Section 6 (D2C ~20–27%, Retail ~4–9%, B2B ~1–2%). ([Coresight Research](https://coresight.com/research/the-true-cost-of-apparel-returns-alarming-return-rates-require-loss-minimization-solutions/?utm_source=chatgpt.com "The True Cost of Apparel Returns: Alarming Return Rates Require Loss ..."), [Capital One Shopping](https://capitaloneshopping.com/research/average-retail-return-rate/?utm_source=chatgpt.com "Average Retail Return Rate (2025 Data): eCommerce vs In-Store"))
    
- **Volatility:** week-to-week variance **≥20%** at least half the time; at least **5–7 spike days** (>+50% vs 7-day average) and **3–5 slow days** (<−40%).
    
- **SKU coverage:** **every active SKU** with stock appears at least once; top 20% SKUs contribute **≥60%** of summer revenue.
    
- **No stock negatives** (unless you are simulating backorders).
    
- **Data integrity:** all returns link to an original order; sums of lines = totals; taxes consistent; currencies valid.
    

---

## 10) Notes for realism (use these when shaping patterns)

- Online apparel AOV hovers around **$120 (global)**; online return rates near **~24%**; in-store much lower (~9%). Peak shopping hours are **afternoon & evening**, with **late-August UK Bank Holiday** driving a UK/IE uplift. Use these as realism guardrails while still matching your price book and events. ([eCommerce DB](https://ecommercedb.com/benchmarks/ww/apparel?utm_source=chatgpt.com "Global Apparel eCommerce Benchmarks - AOV, Conversion rate, ... - ECDB"), [Coresight Research](https://coresight.com/research/the-true-cost-of-apparel-returns-alarming-return-rates-require-loss-minimization-solutions/?utm_source=chatgpt.com "The True Cost of Apparel Returns: Alarming Return Rates Require Loss ..."), [Capital One Shopping](https://capitaloneshopping.com/research/average-retail-return-rate/?utm_source=chatgpt.com "Average Retail Return Rate (2025 Data): eCommerce vs In-Store"), [ECDB](https://ecdb.com/blog/online-shopping-habits-the-golden-hours-of-ecommerce/4462?utm_source=chatgpt.com "The Golden Hours of eCommerce: Online Shopping Days Worldwide"), [Britishheadline](https://britishheadline.co.uk/august-bank-holiday-2025/?utm_source=chatgpt.com "August Bank Holiday 2025: UK's End-of-Summer Tradition"))

---

## 11) Output & delivery - Must be outputted into immediately Odoo using advanced multi step reasoning thinking through where each piece of data should be put in and then make this repeatable over and over again to speed up your efficency over each of the fields.

### **Required Odoo Apps Check (MUST VERIFY FIRST)**

Before proceeding, verify these Odoo apps are installed and configured:

- **Sales Management** (sale_management) - for sale.order creation
- **Inventory** (stock) - for product variants and stock movements
- **Accounting** (account) - for invoices and credit notes
- **Point of Sale** (point_of_sale) - for retail transactions - this data should be inputted easily but honeslty we want to make things as simple and straightforward as possible. 
- **Contacts** (contacts) - for customer records b2c and b2b/ 
- Vendors - for supplier records. 
- **Purchase** (purchase) - for B2B wholesale management
- And ANY OTHER RELEVANT APPS WHERE THIS DATA SHOULD BE PLACED. 
  e.g. Channel should just be attributed via the contacts - the simple way to avoid complexity, use the above as a general guide to where data shpuld be put. 

### **Precise Odoo Object Mapping (MANDATORY)**

**CRITICAL**: You must place data in the correct Odoo objects and fields. Retry up to 5 times if initial placement fails. Here's the precise mapping: - YOU DO NOT ALWAYS HAVE TO BE PRECISE, REASON THROUGH EACH STEP AND VALIDATE, and IF YOU FIND A BETTER WAY DONT BE AFRAID TO APPROACH IT THAT WAY. 

Simple is better, but get the correct fields dont and inputted easily. 

---

## 12) Final instruction — MULTI-AGENT PARALLEL EXECUTION MODEL

### **Agent Architecture & Coordination**

**MANDATORY**: Deploy specialized agents working in parallel to handle the massive data volume. Each agent has specific responsibilities and must coordinate through a central orchestrator.

### **Final Validation Checklist**

Before considering complete, verify IN ODOO:

- **Primary Goal**: Linear pattern is gone - sales show realistic chaos
- **SKU Coverage**: Every product gets appropriate sales volume
- **Historical Data**: 6 months of context exists - 4 months with detail.
- **Customer profiling**: Customers have different profiling. 
- **Customer Realism**: Proper repeat buyer percentage
- **Channel Requirements**: 60/20/20 split achieved
- **Geographic Targets**: UK/US/AU/IE distribution correct
- **Volatility**: Real week-to-week variance, not smooth lines
- **Seasonal Events**: Specific spikes for holidays/promotions visible
- **Return Rates**: Industry-standard returns by channel - okay if not done.
- **BOPIS**: Modern fulfillment option included
- **B2B Characteristics**: Bulk ordering patterns present - separate customer representation.
- **Time Patterns**: Realistic hourly/daily patterns
- **Product Mix**: Natural size/color distribution
- **Data Integrity**: Everything properly connected
-
**OUTPUT TO USER**:

```
SYNTHETIC DATA GENERATION COMPLETE
==================================
Records Created:
- Customers: 35,000
- Orders: 65,000
- Order Lines: 125,000
- Deliveries: 64,500
- Invoices: 65,000
- Returns: 11,665
- Credit Notes: 11,665

Validation Results:
- Channel Split: ✓ D2C 60.2% | Retail 19.8% | B2B 20.0%
- Geography: ✓ UK 49.8% | US 20.1% | AU 19.9% | IE 10.2%
- Return Rates: ✓ Online 24.1% | Retail 6.2% | B2B 1.8%
- AOV: ✓ Online €105 | Retail €87 | B2B €1,850
- Volatility: ✓ 26.3% average week-to-week variance

Issues Requiring Attention:
- [Any warnings or manual fixes needed]

Data Location in Odoo:
- Sales > Orders: View all transactions
- Inventory > Deliveries: Check fulfillment
- Accounting > Invoices: Review financials
- Sales > Customers: Browse database
```