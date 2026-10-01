# Database Design

## 1. Purpose

PostgreSQL will store the operational state of the fictional e-commerce
business.

This includes data that changes over time, such as:

- users
- addresses
- products
- inventory
- orders
- payments
- shipments
- tracking events
- returns
- refunds
- support tickets

Static company knowledge such as policies, FAQs, troubleshooting guides,
and documentation does not belong in this operational schema. That data
will later be handled by the knowledge/RAG subsystem.

---

# 2. Core Design Principles

## 2.1 PostgreSQL is the source of truth for operational data

Customer-specific and transaction-specific state will be stored in
PostgreSQL.

Examples:

- current order status
- shipment status
- payment status
- inventory
- return status
- refund status

---

## 2.2 The LLM will not access PostgreSQL directly

The intended architecture is:

AI Agent
→ Tool
→ Service
→ Repository
→ PostgreSQL

This allows authorization, validation, business rules, logging, and error
handling to exist outside the language model.

---

## 2.3 Historical transactional data must remain historically accurate

Changing current customer or product information must not incorrectly alter
historical orders.

For example:

- changing a product's current price must not change the price shown on an
  old order
- changing a user's saved address must not change the shipping address of an
  already placed order

Important transactional values will therefore be snapshotted where
appropriate.

---

## 2.4 Money must not use floating-point storage

Monetary values will use PostgreSQL NUMERIC/DECIMAL types rather than
floating-point types.

---

## 2.5 Important entities use stable identifiers

Primary keys will use UUIDs internally.

Customer-facing identifiers such as order numbers may use separate readable
identifiers.

Example:

Internal ID:
550e8400-e29b-41d4-a716-446655440000

Customer-facing order number:
ORD-100001

---

# 3. Users

Represents authenticated users of the platform.

## Table: users

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| email | VARCHAR(255) | NOT NULL, UNIQUE |
| password_hash | TEXT | NOT NULL |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| phone | VARCHAR(30) | nullable |
| role | VARCHAR(30) | NOT NULL |
| status | VARCHAR(30) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Possible roles:

- customer
- support_agent
- admin

Possible statuses:

- active
- suspended
- disabled

Passwords must never be stored in plaintext.

---

# 4. Addresses

A user may maintain multiple addresses.

## Table: addresses

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| user_id | UUID | NOT NULL, FK → users.id |
| label | VARCHAR(50) | nullable |
| recipient_name | VARCHAR(200) | NOT NULL |
| line1 | VARCHAR(255) | NOT NULL |
| line2 | VARCHAR(255) | nullable |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NOT NULL |
| postal_code | VARCHAR(30) | NOT NULL |
| country_code | CHAR(2) | NOT NULL |
| phone | VARCHAR(30) | nullable |
| is_default | BOOLEAN | NOT NULL DEFAULT FALSE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Relationship:

users 1 → N addresses

Addresses represent the user's currently saved addresses.

Orders will separately snapshot shipping information so historical orders do
not change when a saved address is edited.

---

# 5. Products

Represents products sold by the store.

## Table: products

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| sku | VARCHAR(100) | NOT NULL, UNIQUE |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | nullable |
| category | VARCHAR(100) | NOT NULL |
| price | NUMERIC(12,2) | NOT NULL |
| currency | CHAR(3) | NOT NULL |
| active | BOOLEAN | NOT NULL DEFAULT TRUE |
| warranty_months | INTEGER | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

`price` represents the current selling price.

Historical purchase prices are stored separately in order_items.

---

# 6. Inventory

Inventory is kept separate from product metadata.

## Table: inventory

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| product_id | UUID | NOT NULL, UNIQUE, FK → products.id |
| quantity_on_hand | INTEGER | NOT NULL |
| quantity_reserved | INTEGER | NOT NULL DEFAULT 0 |
| updated_at | TIMESTAMPTZ | NOT NULL |

Initial version assumes one logical inventory pool.

Future versions could introduce warehouses.

Constraints should ensure quantities cannot become negative.

Available inventory can conceptually be calculated as:

quantity_on_hand - quantity_reserved

---

# 7. Orders

Represents customer purchases.

## Table: orders

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| order_number | VARCHAR(50) | NOT NULL, UNIQUE |
| user_id | UUID | NOT NULL, FK → users.id |
| status | VARCHAR(30) | NOT NULL |
| currency | CHAR(3) | NOT NULL |
| subtotal | NUMERIC(12,2) | NOT NULL |
| tax_amount | NUMERIC(12,2) | NOT NULL DEFAULT 0 |
| shipping_amount | NUMERIC(12,2) | NOT NULL DEFAULT 0 |
| discount_amount | NUMERIC(12,2) | NOT NULL DEFAULT 0 |
| total_amount | NUMERIC(12,2) | NOT NULL |
| shipping_recipient_name | VARCHAR(200) | NOT NULL |
| shipping_line1 | VARCHAR(255) | NOT NULL |
| shipping_line2 | VARCHAR(255) | nullable |
| shipping_city | VARCHAR(100) | NOT NULL |
| shipping_state | VARCHAR(100) | NOT NULL |
| shipping_postal_code | VARCHAR(30) | NOT NULL |
| shipping_country_code | CHAR(2) | NOT NULL |
| placed_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| cancelled_at | TIMESTAMPTZ | nullable |

Possible statuses:

- pending
- confirmed
- processing
- shipped
- delivered
- cancelled

The shipping address is intentionally snapshotted onto the order.

An address may originally come from the user's saved addresses, but once the
order is placed it becomes historical transaction data.

---

# 8. Order Items

Represents products purchased within an order.

## Table: order_items

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| order_id | UUID | NOT NULL, FK → orders.id |
| product_id | UUID | NOT NULL, FK → products.id |
| sku_snapshot | VARCHAR(100) | NOT NULL |
| product_name_snapshot | VARCHAR(255) | NOT NULL |
| unit_price | NUMERIC(12,2) | NOT NULL |
| quantity | INTEGER | NOT NULL |
| line_total | NUMERIC(12,2) | NOT NULL |

Relationship:

orders 1 → N order_items

products 1 → N order_items

Snapshots ensure historical order information remains meaningful if product
metadata changes later.

quantity must be greater than zero.

---

# 9. Payments

Represents payment attempts associated with orders.

## Table: payments

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| order_id | UUID | NOT NULL, FK → orders.id |
| provider | VARCHAR(50) | NOT NULL |
| provider_transaction_id | VARCHAR(255) | nullable |
| amount | NUMERIC(12,2) | NOT NULL |
| currency | CHAR(3) | NOT NULL |
| status | VARCHAR(30) | NOT NULL |
| payment_method_type | VARCHAR(50) | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Possible statuses:

- pending
- succeeded
- failed
- cancelled

An order may have multiple payment attempts.

Sensitive card information such as full card numbers and CVVs must never be
stored.

---

# 10. Shipments

Represents physical shipments for orders.

## Table: shipments

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| order_id | UUID | NOT NULL, FK → orders.id |
| carrier | VARCHAR(100) | NOT NULL |
| service | VARCHAR(100) | nullable |
| tracking_number | VARCHAR(255) | nullable |
| status | VARCHAR(30) | NOT NULL |
| estimated_delivery_at | TIMESTAMPTZ | nullable |
| shipped_at | TIMESTAMPTZ | nullable |
| delivered_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Possible statuses:

- pending
- label_created
- in_transit
- out_for_delivery
- delivered
- delayed
- lost
- returned

An order may eventually have multiple shipments.

This supports split shipments.

---

# 11. Tracking Events

Stores shipment tracking history.

## Table: tracking_events

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| shipment_id | UUID | NOT NULL, FK → shipments.id |
| status | VARCHAR(50) | NOT NULL |
| description | TEXT | NOT NULL |
| location | VARCHAR(255) | nullable |
| occurred_at | TIMESTAMPTZ | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

Relationship:

shipments 1 → N tracking_events

---

# 12. Returns

Represents customer return requests.

## Table: returns

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| return_number | VARCHAR(50) | NOT NULL, UNIQUE |
| order_id | UUID | NOT NULL, FK → orders.id |
| user_id | UUID | NOT NULL, FK → users.id |
| status | VARCHAR(30) | NOT NULL |
| reason | TEXT | nullable |
| requested_at | TIMESTAMPTZ | NOT NULL |
| approved_at | TIMESTAMPTZ | nullable |
| received_at | TIMESTAMPTZ | nullable |
| completed_at | TIMESTAMPTZ | nullable |

Possible statuses:

- requested
- approved
- rejected
- in_transit
- received
- completed
- cancelled

---

# 13. Return Items

A return does not necessarily include every item in an order.

## Table: return_items

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| return_id | UUID | NOT NULL, FK → returns.id |
| order_item_id | UUID | NOT NULL, FK → order_items.id |
| quantity | INTEGER | NOT NULL |
| reason | TEXT | nullable |

Relationship:

returns 1 → N return_items

quantity must be greater than zero.

Business logic must prevent returning more units than were purchased.

---

# 14. Refunds

Refunds represent money returned to a customer.

## Table: refunds

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| refund_number | VARCHAR(50) | NOT NULL, UNIQUE |
| order_id | UUID | NOT NULL, FK → orders.id |
| payment_id | UUID | nullable, FK → payments.id |
| return_id | UUID | nullable, FK → returns.id |
| amount | NUMERIC(12,2) | NOT NULL |
| currency | CHAR(3) | NOT NULL |
| status | VARCHAR(30) | NOT NULL |
| reason | TEXT | nullable |
| provider_refund_id | VARCHAR(255) | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| completed_at | TIMESTAMPTZ | nullable |

Possible statuses:

- pending
- processing
- succeeded
- failed
- cancelled

A refund may be associated with a return, but a return is not mandatory.

For example, customer support may issue a goodwill refund without requiring
the physical item to be returned.

---

# 15. Support Tickets

Represents cases escalated to human support.

## Table: support_tickets

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PRIMARY KEY |
| ticket_number | VARCHAR(50) | NOT NULL, UNIQUE |
| user_id | UUID | NOT NULL, FK → users.id |
| order_id | UUID | nullable, FK → orders.id |
| subject | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| status | VARCHAR(30) | NOT NULL |
| priority | VARCHAR(20) | NOT NULL |
| assigned_to | UUID | nullable, FK → users.id |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| resolved_at | TIMESTAMPTZ | nullable |

Possible statuses:

- open
- in_progress
- waiting_for_customer
- resolved
- closed

Possible priorities:

- low
- normal
- high
- urgent

---

# 16. Relationship Summary

users
  1 → N addresses
  1 → N orders
  1 → N returns
  1 → N support_tickets

products
  1 → 1 inventory
  1 → N order_items

orders
  1 → N order_items
  1 → N payments
  1 → N shipments
  1 → N returns
  1 → N refunds
  1 → N support_tickets

shipments
  1 → N tracking_events

returns
  1 → N return_items
  1 → N refunds

payments
  1 → N refunds

---

# 17. Initial Database Boundaries

PostgreSQL will contain operational business state.

It will NOT initially contain the static knowledge base used for RAG.

The knowledge system will be designed separately.

The AI architecture will therefore eventually distinguish between:

Operational question
→ authorized business tool
→ service
→ repository
→ PostgreSQL

and:

Knowledge question
→ retrieval
→ knowledge base
→ grounded LLM response