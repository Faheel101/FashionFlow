"""Product catalog definitions for the FashionFlow data generator.

Realistic fashion ecommerce categories, brands, products, materials,
colors, and sizes used by the historical data generator.
"""

# ── Category Hierarchy ───────────────────────────────────────────────────────
# (name, description, children)

CATEGORY_TREE: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "Women",
        "Women's clothing and fashion",
        [
            ("Dresses", "Casual and formal dresses"),
            ("Tops", "Blouses, shirts, and t-shirts"),
            ("Bottoms", "Pants, skirts, and shorts"),
            ("Outerwear", "Jackets, coats, and blazers"),
            ("Activewear", "Workout and athletic wear"),
            ("Swimwear", "Swimsuits and cover-ups"),
        ],
    ),
    (
        "Men",
        "Men's clothing and fashion",
        [
            ("Shirts", "Dress shirts, casual shirts, and polos"),
            ("Pants", "Chinos, jeans, and trousers"),
            ("Outerwear", "Jackets, coats, and vests"),
            ("T-Shirts", "Graphic and plain tees"),
            ("Activewear", "Workout and athletic wear"),
            ("Suits", "Business and formal suits"),
        ],
    ),
    (
        "Shoes",
        "Footwear for all occasions",
        [
            ("Sneakers", "Casual and athletic sneakers"),
            ("Boots", "Ankle boots, knee boots, and hiking boots"),
            ("Sandals", "Summer sandals and slides"),
            ("Heels", "Pumps, wedges, and stilettos"),
            ("Loafers", "Slip-on and moccasin styles"),
            ("Formal", "Oxford and derby dress shoes"),
        ],
    ),
    (
        "Accessories",
        "Fashion accessories and jewelry",
        [
            ("Bags", "Handbags, totes, and backpacks"),
            ("Jewelry", "Necklaces, bracelets, and earrings"),
            ("Watches", "Analog and digital watches"),
            ("Belts", "Leather and fabric belts"),
            ("Scarves", "Silk and wool scarves"),
            ("Sunglasses", "Designer and casual sunglasses"),
        ],
    ),
    (
        "Athleisure",
        "Performance meets street style",
        [
            ("Leggings", "High-waist and compression leggings"),
            ("Hoodies", "Pullover and zip-up hoodies"),
            ("Joggers", "Tapered and relaxed joggers"),
            ("Sports Bras", "Low, medium, and high impact"),
            ("Track Jackets", "Lightweight zip-ups"),
        ],
    ),
]

# ── Brands ───────────────────────────────────────────────────────────────────

BRANDS: dict[str, list[str]] = {
    "premium": [
        "Élan Studio",
        "Maison Vero",
        "Arden & Co",
        "Lux Collective",
        "Noir Atelier",
        "Casa Mira",
    ],
    "mid_range": [
        "Thread Republic",
        "Urban Weave",
        "Harper & Elm",
        "Coastal Standard",
        "Ridge & Valley",
        "Forma Basics",
        "Westbound Co",
        "Kinetic Label",
    ],
    "budget": [
        "DayWear Essentials",
        "Simple State",
        "Base Layer Co",
        "Everday Studio",
        "Plain Jane",
    ],
}

# ── Price Ranges by Category (min, max) ──────────────────────────────────────

PRICE_RANGES: dict[str, tuple[float, float]] = {
    "Dresses": (39.99, 249.99),
    "Tops": (19.99, 89.99),
    "Bottoms": (29.99, 129.99),
    "Outerwear": (59.99, 349.99),
    "Activewear": (24.99, 99.99),
    "Swimwear": (29.99, 149.99),
    "Shirts": (29.99, 129.99),
    "Pants": (34.99, 149.99),
    "T-Shirts": (14.99, 49.99),
    "Suits": (149.99, 599.99),
    "Sneakers": (49.99, 189.99),
    "Boots": (69.99, 299.99),
    "Sandals": (24.99, 119.99),
    "Heels": (49.99, 249.99),
    "Loafers": (59.99, 199.99),
    "Formal": (79.99, 299.99),
    "Bags": (39.99, 299.99),
    "Jewelry": (14.99, 199.99),
    "Watches": (49.99, 399.99),
    "Belts": (19.99, 89.99),
    "Scarves": (24.99, 149.99),
    "Sunglasses": (29.99, 199.99),
    "Leggings": (29.99, 89.99),
    "Hoodies": (34.99, 119.99),
    "Joggers": (34.99, 99.99),
    "Sports Bras": (24.99, 69.99),
    "Track Jackets": (39.99, 129.99),
}

# ── Product Attributes ───────────────────────────────────────────────────────

SIZES: dict[str, list[str]] = {
    "clothing": ["XS", "S", "M", "L", "XL", "XXL"],
    "shoes": ["6", "7", "8", "9", "10", "11", "12"],
    "accessories": ["One Size"],
}

COLORS: list[str] = [
    "Black", "White", "Navy", "Grey", "Charcoal",
    "Cream", "Beige", "Olive", "Burgundy", "Forest Green",
    "Dusty Rose", "Camel", "Slate Blue", "Terracotta", "Sage",
    "Ivory", "Mocha", "Stone", "Denim Blue", "Rust",
]

MATERIALS: dict[str, list[str]] = {
    "clothing": [
        "100% Cotton", "Cotton Blend", "Linen", "Silk",
        "Polyester", "Wool", "Cashmere", "Denim",
        "Jersey Knit", "French Terry", "Modal", "Tencel",
    ],
    "shoes": [
        "Full-Grain Leather", "Suede", "Canvas", "Synthetic",
        "Knit Mesh", "Nubuck", "Patent Leather",
    ],
    "accessories": [
        "Genuine Leather", "Stainless Steel", "Sterling Silver",
        "Gold-Plated", "Silk", "Wool Blend", "Acetate",
        "Canvas", "Nylon",
    ],
}

# ── Product Name Templates ───────────────────────────────────────────────────
# {color} {material_adj} {style} — populated by the generator

PRODUCT_STYLES: dict[str, list[str]] = {
    "Dresses": ["Midi Dress", "Maxi Dress", "Wrap Dress", "Shift Dress", "A-Line Dress", "Shirt Dress"],
    "Tops": ["Button-Down Blouse", "Relaxed Tee", "Crop Top", "Tank Top", "Peplum Top", "Henley"],
    "Bottoms": ["Wide-Leg Pants", "Slim Chinos", "Pencil Skirt", "Midi Skirt", "Cargo Pants", "Culottes"],
    "Outerwear": ["Trench Coat", "Puffer Jacket", "Blazer", "Bomber Jacket", "Wool Overcoat", "Denim Jacket"],
    "Activewear": ["Performance Tank", "Running Shorts", "Yoga Pants", "Training Tee", "Mesh Panel Top"],
    "Swimwear": ["One-Piece Swimsuit", "Bikini Set", "High-Waist Bottom", "Rash Guard", "Cover-Up Wrap"],
    "Shirts": ["Oxford Shirt", "Chambray Shirt", "Linen Shirt", "Flannel Shirt", "Polo Shirt", "Camp Collar Shirt"],
    "Pants": ["Slim Fit Chinos", "Straight Leg Jeans", "Tailored Trousers", "Cargo Pants", "Jogger Pants"],
    "T-Shirts": ["Classic Crew Tee", "V-Neck Tee", "Graphic Tee", "Pocket Tee", "Oversized Tee"],
    "Suits": ["Two-Piece Suit", "Three-Piece Suit", "Linen Suit", "Slim Fit Suit"],
    "Sneakers": ["Low-Top Sneaker", "High-Top Sneaker", "Running Shoe", "Slip-On Sneaker", "Platform Sneaker"],
    "Boots": ["Chelsea Boot", "Ankle Boot", "Combat Boot", "Knee-High Boot", "Hiking Boot", "Desert Boot"],
    "Sandals": ["Slide Sandal", "Gladiator Sandal", "Platform Sandal", "Sport Sandal", "Flip Flop"],
    "Heels": ["Block Heel Pump", "Stiletto", "Wedge Sandal", "Kitten Heel", "Mule"],
    "Loafers": ["Penny Loafer", "Driving Moc", "Tassel Loafer", "Bit Loafer"],
    "Formal": ["Oxford Shoe", "Derby Shoe", "Monk Strap", "Cap Toe"],
    "Bags": ["Tote Bag", "Crossbody Bag", "Backpack", "Clutch", "Bucket Bag", "Messenger Bag"],
    "Jewelry": ["Chain Necklace", "Hoop Earrings", "Cuff Bracelet", "Pendant Necklace", "Stud Earrings", "Ring Set"],
    "Watches": ["Analog Watch", "Chronograph Watch", "Minimalist Watch", "Dive Watch", "Smart Watch"],
    "Belts": ["Leather Belt", "Woven Belt", "Chain Belt", "Reversible Belt"],
    "Scarves": ["Silk Scarf", "Wool Scarf", "Blanket Scarf", "Infinity Scarf", "Bandana"],
    "Sunglasses": ["Aviator", "Wayfarer", "Cat Eye", "Round Frame", "Sport Wrap", "Oversized Frame"],
    "Leggings": ["High-Waist Legging", "Cropped Legging", "Pocket Legging", "Compression Legging"],
    "Hoodies": ["Pullover Hoodie", "Zip-Up Hoodie", "Cropped Hoodie", "Oversized Hoodie"],
    "Joggers": ["Slim Jogger", "Relaxed Jogger", "Tech Fleece Jogger", "Woven Jogger"],
    "Sports Bras": ["Racerback Sports Bra", "Longline Sports Bra", "Adjustable Sports Bra"],
    "Track Jackets": ["Quarter-Zip Pullover", "Full-Zip Track Jacket", "Windbreaker"],
}

# ── Seasonal Weights ─────────────────────────────────────────────────────────
# Monthly multipliers for order volume (1.0 = baseline)

MONTHLY_ORDER_WEIGHTS: list[float] = [
    0.85,   # Jan — post-holiday dip
    0.80,   # Feb — lowest month
    0.90,   # Mar — spring arrivals
    1.00,   # Apr — baseline
    1.05,   # May — warm weather shopping
    1.00,   # Jun — steady
    0.90,   # Jul — mid-summer lull
    0.95,   # Aug — back to school
    1.05,   # Sep — fall fashion
    1.10,   # Oct — pre-holiday
    1.40,   # Nov — Black Friday / holiday push
    1.30,   # Dec — holiday gifting
]

# ── Order & Payment Constants ────────────────────────────────────────────────

ORDER_STATUSES: list[str] = [
    "pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned",
]

# Probability distribution for final order status
ORDER_STATUS_WEIGHTS: dict[str, float] = {
    "delivered": 0.82,
    "cancelled": 0.06,
    "returned": 0.04,
    "shipped": 0.03,
    "processing": 0.02,
    "confirmed": 0.02,
    "pending": 0.01,
}

PAYMENT_METHODS: list[tuple[str, float]] = [
    ("credit_card", 0.45),
    ("debit_card", 0.20),
    ("paypal", 0.20),
    ("apple_pay", 0.10),
    ("google_pay", 0.05),
]

REFUND_REASONS: list[tuple[str, float]] = [
    ("size_issue", 0.30),
    ("changed_mind", 0.25),
    ("not_as_described", 0.15),
    ("quality_issue", 0.12),
    ("damaged", 0.10),
    ("wrong_item", 0.08),
]

TAX_RATE: float = 0.08
SHIPPING_RATES: list[tuple[float, float]] = [
    (0.00, 0.30),     # Free shipping (30%)
    (5.99, 0.25),     # Standard
    (9.99, 0.25),     # Priority
    (14.99, 0.15),    # Express
    (24.99, 0.05),    # Overnight
]

DISCOUNT_CHANCE: float = 0.25  # 25% of orders get a discount
DISCOUNT_RANGE: tuple[float, float] = (0.05, 0.30)  # 5% to 30% off
