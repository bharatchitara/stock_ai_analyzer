# Where to See Stock Events in the UI

## 🎯 Quick Access Points

### 1. **Portfolio Dashboard** (Main Page)
**URL**: `http://localhost:8000/portfolio/`

**What you'll see**:
- An info banner at the top explaining stock events feature
- Each holding row has two icons in the Actions column:
  - 👁️ **Eye icon** - View holding details
  - 📅 **Calendar icon** - **View Stock Events** (NEW!)

**How to use**:
1. Go to your portfolio dashboard
2. Find any stock in your holdings table
3. Click the **📅 calendar icon** in the Actions column
4. You'll be taken to the Stock Events page for that stock

---

### 2. **Holding Detail Page**
**URL**: `http://localhost:8000/portfolio/holding/<id>/`

**What you'll see**:
- A prominent **blue info card** at the bottom with:
  - Title: "Track Stock Events"
  - Description of available event types
  - Large **"View All Events"** button
- Additional **"View Stock Events"** button in the action buttons section

**How to use**:
1. Click the eye icon (👁️) on any holding in your dashboard
2. Scroll down to see the blue "Track Stock Events" card
3. Click **"View All Events"** button
4. Or click the **"View Stock Events"** button at the bottom

---

### 3. **Stock Events Page** (Detailed View)
**URL**: `http://localhost:8000/portfolio/stock/<SYMBOL>/events/`
Example: `http://localhost:8000/portfolio/stock/RELIANCE/events/`

**What you'll see**:
A comprehensive tabbed interface with 5 sections:

#### 📊 **Tab 1: Promoter Holdings** (Default)
- Latest promoter holding percentage
- Quarter-over-quarter changes (green/red badges)
- Table showing last 8 quarters
- FII and DII holdings
- Pledged shares percentage

#### 👔 **Tab 2: Insider Trades**
- Director/promoter transactions
- Buy/Sell/Pledge activities
- Transaction dates and amounts
- Insider names and designations

#### 💼 **Tab 3: Bulk Deals**
- Large transactions (>0.5% equity)
- Client names
- Buy/Sell indicators
- Deal values and dates

#### 📦 **Tab 4: Block Deals**
- Institutional transactions
- Similar to bulk deals
- Typically larger volumes

#### 🏢 **Tab 5: Corporate Actions**
- Dividends with amounts
- Bonus issues with ratios
- Stock splits
- Rights issues
- Buyback announcements
- AGM/EGM dates

**Features**:
- **Refresh Events** button at the top to fetch latest data
- **Back to Portfolio** button
- Color-coded badges for different transaction types
- Sortable tables with dates

---

## 🔄 How to Fetch Events

### Method 1: Command Line (Recommended for bulk fetching)
```bash
# Fetch all events for all your holdings
python manage.py fetch_stock_events --holdings-only

# Fetch for a specific stock
python manage.py fetch_stock_events --symbol RELIANCE

# Fetch only insider trades
python manage.py fetch_stock_events --event-type insider --holdings-only
```

### Method 2: Via UI (On-demand)
1. Go to any stock events page
2. Click **"Refresh Events"** button
3. Wait for fetching to complete
4. Page automatically reloads with new data

---

## 📱 Visual Flow

```
Portfolio Dashboard
    ↓
[Click 📅 calendar icon on any stock]
    ↓
Stock Events Page
    ↓
[View 5 tabs of different event types]

OR

Portfolio Dashboard
    ↓
[Click 👁️ eye icon on any stock]
    ↓
Holding Detail Page
    ↓
[Click "View All Events" in blue card]
    ↓
Stock Events Page
```

---

## 🎨 UI Elements to Look For

### Icons Used:
- 📅 `<i class="fas fa-calendar-alt"></i>` - Stock Events
- 👁️ `<i class="fas fa-eye"></i>` - View Details
- 👔 `<i class="fas fa-user-tie"></i>` - Insider Trades
- 👥 `<i class="fas fa-users"></i>` - Promoter Holdings
- 💱 `<i class="fas fa-exchange-alt"></i>` - Bulk Deals
- 📦 `<i class="fas fa-cubes"></i>` - Block Deals
- 🏢 `<i class="fas fa-building"></i>` - Corporate Actions

### Color Coding:
- 🟢 **Green badges** - Buy transactions, positive changes
- 🔴 **Red badges** - Sell transactions, negative changes
- 🔵 **Blue badges** - Corporate actions
- 🟡 **Yellow badges** - Pledge/warning indicators

---

## 📊 Example Workflow

### Scenario: Check RELIANCE stock events

1. **Go to Dashboard**
   ```
   http://localhost:8000/portfolio/
   ```

2. **Find RELIANCE in your holdings table**
   - Look at the "Actions" column on the right

3. **Click the 📅 calendar icon**
   - Instantly taken to events page

4. **Explore the tabs**:
   - **Promoter Holdings**: See if promoters are increasing/decreasing stake
   - **Insider Trades**: Check if directors are buying or selling
   - **Bulk Deals**: See institutional interest
   - **Corporate Actions**: Check upcoming dividends

5. **Interpret the data**:
   - **Promoter buying** + **Directors buying** = Strong confidence 🟢
   - **High pledging** = Risk factor 🔴
   - **Recent dividend** = Good cash flow 🟢
   - **FII accumulation** = Long-term bullish 🟢

---

## 🔍 What Each Event Tells You

### 📈 **Insider Trades**
- **Directors buying**: Positive signal - they know the company best
- **Promoters selling**: Requires attention - why are they exiting?
- **High volume buying**: Strong conviction

### 💰 **Bulk/Block Deals**
- **FII buying**: Foreign institutions showing interest
- **DII buying**: Domestic institutions accumulating
- **Repeated buying**: Strong institutional confidence

### 🎁 **Corporate Actions**
- **Dividend**: Company sharing profits
- **Bonus**: Stock dividend (e.g., 1:2 = 1 bonus for every 2 held)
- **Split**: Making shares more accessible
- **Buyback**: Company buying back shares (usually positive)

### 👥 **Promoter Holdings**
- **Increasing**: Promoters bullish on company
- **Decreasing**: Could mean fund raising or concerns
- **High pledging (>50%)**: Risk - promoters borrowing against shares
- **Low pledging (<10%)**: Healthy - strong promoter confidence

---

## 💡 Pro Tips

1. **Check events before buying/selling**: Look for recent insider activity
2. **Monitor promoter trends**: Consistent increase is positive
3. **Watch for unusual bulk deals**: Could indicate institutional interest
4. **Set a schedule**: Check events weekly for your holdings
5. **Combine with news**: Correlate events with news articles
6. **Compare with sector**: See if other sector stocks have similar activity

---

## 🚀 Coming Soon

- Email alerts for significant events
- Event-based recommendations
- Historical impact analysis
- Custom event filters
- Mobile app integration

---

**Need Help?**
- Run: `python manage.py fetch_stock_events --help`
- Read: `docs/STOCK_EVENTS_GUIDE.md`
- Check logs: Django development server output
