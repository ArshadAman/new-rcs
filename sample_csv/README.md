# Sample CSV Files

Use these samples as templates for Manual Mailing and Online Orders.

---

## 1. Manual Mailing (`manual_mailing_sample.csv`)

**Required column:**
- `email` – Recipient's email address (required)

**Optional columns:**
- `name` – Customer name (used in email as [Customer Name])
- `order_number` – Order reference (used in email as [Order Number])
- `country` – Recipient's country (e.g. `Czech`, `Slovak`, `United States`). Used for language: Czech/Slovak recipients get localized emails.

**Example:**
```csv
email,name,order_number,country
customer1@example.com,John Smith,ORD-1001,United States
customer2@example.com,Jane Doe,ORD-1002,Czech
```

- First row must be the header.
- Empty optional fields are allowed; only `email` is required per row.
- Use UTF-8 encoding when saving the file.

---

## 2. Online Orders (`online_orders_sample.csv`)

**Required columns:**
- `Order ID` – Your order reference (e.g. ORD-1001)
- `Customer Name` – Full name
- `Email` – Customer email
- `Phone Number` – Customer phone
- `Shipment Date` – Date in **YYYY-MM-DD** format (e.g. 2025-02-17)

**Example:**
```csv
Order ID,Customer Name,Email,Phone Number,Shipment Date
ORD-1001,John Smith,john.smith@example.com,+1 555-0101,2025-02-15
```

- First row must be the header.
- All five columns are required; empty values will cause row errors.
- Shipment Date must be exactly `YYYY-MM-DD` (e.g. `2025-02-17`).
- Save the file with UTF-8 encoding.
