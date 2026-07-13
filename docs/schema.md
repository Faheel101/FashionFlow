# FashionFlow — Ecommerce Database Schema

## Entity Relationship Diagram

```
┌──────────────┐
│  categories  │
├──────────────┤        ┌──────────────┐
│ id (PK)      │◄─┐     │   products   │
│ name         │  │     ├──────────────┤        ┌──────────────┐
│ description  │  ├────▶│ id (PK)      │        │ order_items  │
│ parent_id(FK)│──┘     │ sku (UQ)     │◄───────┤──────────────┤
│ is_active    │        │ name         │        │ id (PK)      │
│ created_at   │        │ category_id  │        │ order_id(FK) │──┐
│ updated_at   │        │ brand        │        │ product_id   │  │
└──────────────┘        │ price        │        │ quantity     │  │
                        │ cost_price   │        │ unit_price   │  │
┌──────────────┐        │ size         │        │ discount_amt │  │
│  customers   │        │ color        │        │ total_price  │  │
├──────────────┤        │ material     │        │ created_at   │  │
│ id (PK)      │◄──┐    │ stock_qty    │        │ updated_at   │  │
│ email (UQ)   │   │    │ is_active    │        └──────────────┘  │
│ first_name   │   │    │ created_at   │                          │
│ last_name    │   │    │ updated_at   │                          │
│ phone        │   │    └──────────────┘                          │
│ dob          │   │                                              │
│ gender       │   │    ┌──────────────┐                          │
│ address_1    │   │    │   orders     │                          │
│ address_2    │   │    ├──────────────┤                          │
│ city         │   ├───▶│ id (PK)      │◄─────────────────────────┘
│ state        │   │    │ order_number │
│ postal_code  │   │    │ customer_id  │     ┌──────────────┐
│ country      │   │    │ status       │     │   payments   │
│ is_active    │   │    │ subtotal     │     ├──────────────┤
│ created_at   │   │    │ discount_amt │     │ id (PK)      │
│ updated_at   │   │    │ tax_amount   │◄────│ order_id(FK) │◄──┐
└──────────────┘        │ shipping_amt │     │ method       │   │
                        │ total_amount │     │ status       │   │
                        │ ship_addr_1  │     │ amount       │   │
                        │ ship_addr_2  │     │ txn_id (UQ)  │   │
                        │ ship_city    │     │ created_at   │   │
                        │ ship_state   │     │ updated_at   │   │
                        │ ship_postal  │     └──────────────┘   │
                        │ ship_country │                         │
                        │ notes        │     ┌──────────────┐   │
                        │ created_at   │     │   refunds    │   │
                        │ updated_at   │     ├──────────────┤   │
                        └──────────────┘◄────│ order_id(FK) │   │
                                             │ payment_id   │───┘
                                             │ item_id(FK)  │
                                             │ reason       │
                                             │ status       │
                                             │ amount       │
                                             │ notes        │
                                             │ created_at   │
                                             │ updated_at   │
                                             └──────────────┘
```

## Tables

### categories

Hierarchical product taxonomy. Self-referencing `parent_category_id` enables nesting (e.g. Women → Dresses → Maxi Dresses).

| Column             | Type         | Constraints          |
| ------------------ | ------------ | -------------------- |
| id                 | INTEGER      | PK, AUTO             |
| name               | VARCHAR(100) | NOT NULL             |
| description        | TEXT         | NULLABLE             |
| parent_category_id | INTEGER      | FK → categories.id   |
| is_active          | BOOLEAN      | NOT NULL, DEFAULT 1  |
| created_at         | DATETIME     | NOT NULL             |
| updated_at         | DATETIME     | NOT NULL             |

### products

Fashion products with pricing, inventory, and physical attributes.

| Column         | Type         | Constraints          |
| -------------- | ------------ | -------------------- |
| id             | INTEGER      | PK, AUTO             |
| sku            | VARCHAR(50)  | UNIQUE, NOT NULL     |
| name           | VARCHAR(200) | NOT NULL             |
| description    | TEXT         | NULLABLE             |
| category_id    | INTEGER      | FK → categories.id   |
| brand          | VARCHAR(100) | NOT NULL             |
| price          | FLOAT        | NOT NULL             |
| cost_price     | FLOAT        | NOT NULL             |
| size           | VARCHAR(20)  | NULLABLE             |
| color          | VARCHAR(50)  | NULLABLE             |
| material       | VARCHAR(100) | NULLABLE             |
| stock_quantity | INTEGER      | NOT NULL, DEFAULT 0  |
| is_active      | BOOLEAN      | NOT NULL, DEFAULT 1  |
| created_at     | DATETIME     | NOT NULL             |
| updated_at     | DATETIME     | NOT NULL             |

### customers

Customer profiles with contact info and shipping addresses.

| Column        | Type         | Constraints          |
| ------------- | ------------ | -------------------- |
| id            | INTEGER      | PK, AUTO             |
| email         | VARCHAR(255) | UNIQUE, NOT NULL     |
| first_name    | VARCHAR(100) | NOT NULL             |
| last_name     | VARCHAR(100) | NOT NULL             |
| phone         | VARCHAR(20)  | NULLABLE             |
| date_of_birth | VARCHAR(10)  | NULLABLE             |
| gender        | VARCHAR(20)  | NULLABLE             |
| address_line1 | VARCHAR(255) | NULLABLE             |
| address_line2 | VARCHAR(255) | NULLABLE             |
| city          | VARCHAR(100) | NULLABLE             |
| state         | VARCHAR(100) | NULLABLE             |
| postal_code   | VARCHAR(20)  | NULLABLE             |
| country       | VARCHAR(100) | NOT NULL, DEFAULT US |
| is_active     | BOOLEAN      | NOT NULL, DEFAULT 1  |
| created_at    | DATETIME     | NOT NULL             |
| updated_at    | DATETIME     | NOT NULL             |

### orders

Purchase orders with status lifecycle and financial breakdown.

**Status values:** pending → confirmed → processing → shipped → delivered | cancelled | returned

| Column                 | Type         | Constraints          |
| ---------------------- | ------------ | -------------------- |
| id                     | INTEGER      | PK, AUTO             |
| order_number           | VARCHAR(50)  | UNIQUE, NOT NULL     |
| customer_id            | INTEGER      | FK → customers.id    |
| status                 | VARCHAR(20)  | NOT NULL             |
| subtotal               | FLOAT        | NOT NULL, DEFAULT 0  |
| discount_amount        | FLOAT        | NOT NULL, DEFAULT 0  |
| tax_amount             | FLOAT        | NOT NULL, DEFAULT 0  |
| shipping_amount        | FLOAT        | NOT NULL, DEFAULT 0  |
| total_amount           | FLOAT        | NOT NULL, DEFAULT 0  |
| shipping_address_line1 | VARCHAR(255) | NULLABLE             |
| shipping_address_line2 | VARCHAR(255) | NULLABLE             |
| shipping_city          | VARCHAR(100) | NULLABLE             |
| shipping_state         | VARCHAR(100) | NULLABLE             |
| shipping_postal_code   | VARCHAR(20)  | NULLABLE             |
| shipping_country       | VARCHAR(100) | NULLABLE             |
| notes                  | TEXT         | NULLABLE             |
| created_at             | DATETIME     | NOT NULL             |
| updated_at             | DATETIME     | NOT NULL             |

### order_items

Individual line items within an order.

| Column          | Type    | Constraints          |
| --------------- | ------- | -------------------- |
| id              | INTEGER | PK, AUTO             |
| order_id        | INTEGER | FK → orders.id       |
| product_id      | INTEGER | FK → products.id     |
| quantity        | INTEGER | NOT NULL, DEFAULT 1  |
| unit_price      | FLOAT   | NOT NULL             |
| discount_amount | FLOAT   | NOT NULL, DEFAULT 0  |
| total_price     | FLOAT   | NOT NULL             |
| created_at      | DATETIME| NOT NULL             |
| updated_at      | DATETIME| NOT NULL             |

### payments

Payment transactions linked to orders.

**Method values:** credit_card, debit_card, paypal, apple_pay, google_pay

**Status values:** pending → completed | failed | refunded

| Column         | Type         | Constraints          |
| -------------- | ------------ | -------------------- |
| id             | INTEGER      | PK, AUTO             |
| order_id       | INTEGER      | FK → orders.id       |
| payment_method | VARCHAR(50)  | NOT NULL             |
| payment_status | VARCHAR(20)  | NOT NULL             |
| amount         | FLOAT        | NOT NULL             |
| transaction_id | VARCHAR(100) | UNIQUE, NOT NULL     |
| created_at     | DATETIME     | NOT NULL             |
| updated_at     | DATETIME     | NOT NULL             |

### refunds

Refund records linked to orders and payments, optionally to a specific line item.

**Reason values:** damaged, wrong_item, not_as_described, changed_mind, size_issue, quality_issue

**Status values:** pending → approved → processed | rejected

| Column        | Type         | Constraints              |
| ------------- | ------------ | ------------------------ |
| id            | INTEGER      | PK, AUTO                 |
| order_id      | INTEGER      | FK → orders.id           |
| payment_id    | INTEGER      | FK → payments.id         |
| order_item_id | INTEGER      | FK → order_items.id, NUL |
| reason        | VARCHAR(50)  | NOT NULL                 |
| status        | VARCHAR(20)  | NOT NULL                 |
| amount        | FLOAT        | NOT NULL                 |
| notes         | TEXT         | NULLABLE                 |
| created_at    | DATETIME     | NOT NULL                 |
| updated_at    | DATETIME     | NOT NULL                 |

## Relationships

| From        | To          | Type      | FK Column          |
| ----------- | ----------- | --------- | ------------------ |
| categories  | categories  | Self-ref  | parent_category_id |
| products    | categories  | Many-to-1 | category_id        |
| orders      | customers   | Many-to-1 | customer_id        |
| order_items | orders      | Many-to-1 | order_id           |
| order_items | products    | Many-to-1 | product_id         |
| payments    | orders      | Many-to-1 | order_id           |
| refunds     | orders      | Many-to-1 | order_id           |
| refunds     | payments    | Many-to-1 | payment_id         |
| refunds     | order_items | Many-to-1 | order_item_id      |
