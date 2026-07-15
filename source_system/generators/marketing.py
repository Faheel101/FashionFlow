"""Marketing data generator for FashionFlow.

Generates realistic marketing data across Google Ads and Meta Ads:
    - ~40 campaigns
    - ~120 ad sets
    - ~360 ads
    - ~365 days × ~360 ads ≈ ~80,000 daily performance records

Usage::

    from source_system.generators.marketing import generate_marketing_data
    data = generate_marketing_data()
"""

import random
from datetime import datetime, timedelta

from source_system.generators.catalog import MONTHLY_ORDER_WEIGHTS

# ── Marketing Constants ──────────────────────────────────────────────────────

PLATFORMS = ["google_ads", "meta_ads"]

OBJECTIVES = {
    "google_ads": ["search", "shopping", "display", "performance_max"],
    "meta_ads": ["awareness", "traffic", "conversions", "catalog_sales"],
}

BID_STRATEGIES = {
    "google_ads": ["manual_cpc", "target_cpa", "maximize_conversions", "target_roas"],
    "meta_ads": ["lowest_cost", "cost_cap", "bid_cap", "target_cost"],
}

AD_TYPES = {
    "google_ads": ["text", "responsive_search", "shopping", "display_image"],
    "meta_ads": ["image", "video", "carousel", "collection"],
}

CTAS = ["shop_now", "learn_more", "sign_up", "buy_now", "get_offer"]

TARGETING_INTERESTS = [
    "Fashion", "Luxury Fashion", "Streetwear", "Sustainable Fashion",
    "Women's Fashion", "Men's Fashion", "Athleisure", "Sneakers",
    "Designer Brands", "Online Shopping", "Beauty & Fashion",
    "Fitness & Activewear", "Accessories", "Shoes",
]

CAMPAIGN_THEMES = [
    "Summer Collection Launch", "Winter Sale", "Black Friday Deals",
    "New Arrivals", "Clearance Event", "Holiday Gift Guide",
    "Back to School", "Spring Fashion", "Fall Essentials",
    "VIP Exclusive", "Flash Sale", "Brand Awareness",
    "Retargeting - Cart Abandoners", "Lookalike - Top Buyers",
    "Prospecting - Fashion Enthusiasts", "Seasonal Promotion",
    "Product Launch - Shoes", "Product Launch - Outerwear",
    "Weekend Special", "Loyalty Program",
]

HEADLINES = [
    "Shop the Latest Trends", "Up to 50% Off", "Free Shipping Today",
    "New Season, New Style", "Limited Time Offer", "Exclusive Collection",
    "Shop Now & Save", "Premium Quality Fashion", "Discover Your Style",
    "Trending This Season", "Must-Have Looks", "Style Starts Here",
]

WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL"]


def generate_marketing_data(seed: int = 42, history_days: int = 365) -> dict[str, list[dict]]:
    """Generate marketing data across platforms.

    Args:
        seed: Random seed for reproducibility.
        history_days: Days of historical performance data.

    Returns:
        Dictionary with keys: campaigns, ad_sets, ads, daily_performance.
    """
    random.seed(seed)

    end_date = datetime(2026, 7, 13)
    start_date = end_date - timedelta(days=history_days)

    campaigns: list[dict] = []
    ad_sets: list[dict] = []
    ads: list[dict] = []
    daily_performance: list[dict] = []

    campaign_id = 1
    ad_set_id = 1
    ad_id = 1
    perf_id = 1

    for platform in PLATFORMS:
        num_campaigns = random.randint(18, 22)

        for _ in range(num_campaigns):
            # Campaign
            theme = random.choice(CAMPAIGN_THEMES)
            objective = random.choice(OBJECTIVES[platform])
            daily_budget = round(random.uniform(20, 500), 2)
            total_budget = round(daily_budget * random.randint(30, 180), 2)

            camp_start = start_date + timedelta(days=random.randint(0, history_days - 60))
            camp_end = camp_start + timedelta(days=random.randint(30, 180))
            camp_end = min(camp_end, end_date)

            status = random.choices(
                ["active", "paused", "completed", "archived"],
                weights=[0.40, 0.15, 0.35, 0.10],
            )[0]
            if camp_end < end_date - timedelta(days=14):
                status = "completed"

            campaigns.append({
                "id": campaign_id,
                "name": f"[{platform.upper().replace('_', ' ')}] {theme}",
                "platform": platform,
                "objective": objective,
                "status": status,
                "daily_budget": daily_budget,
                "total_budget": total_budget,
                "start_date": camp_start.strftime("%Y-%m-%d"),
                "end_date": camp_end.strftime("%Y-%m-%d"),
                "created_at": camp_start - timedelta(days=random.randint(1, 7)),
                "updated_at": camp_end if status == "completed" else end_date,
            })

            # Ad Sets (2-4 per campaign)
            num_ad_sets = random.randint(2, 4)
            for as_idx in range(num_ad_sets):
                gender = random.choice(["All", "Female", "Male"])
                age_min = random.choice([18, 21, 25, 30, 35])
                age_max = age_min + random.choice([15, 20, 25, 30])
                interests = ", ".join(random.sample(TARGETING_INTERESTS, random.randint(2, 5)))

                ad_sets.append({
                    "id": ad_set_id,
                    "campaign_id": campaign_id,
                    "name": f"{theme} - Set {as_idx + 1}",
                    "targeting_gender": gender,
                    "targeting_age_min": age_min,
                    "targeting_age_max": min(age_max, 65),
                    "targeting_interests": interests,
                    "daily_budget": round(daily_budget / num_ad_sets, 2),
                    "bid_strategy": random.choice(BID_STRATEGIES[platform]),
                    "status": "active" if status == "active" else random.choice(["active", "paused"]),
                    "created_at": camp_start,
                    "updated_at": camp_end if status == "completed" else end_date,
                })

                # Ads (2-4 per ad set)
                num_ads = random.randint(2, 4)
                for ad_idx in range(num_ads):
                    headline = random.choice(HEADLINES)
                    ad_type = random.choice(AD_TYPES[platform])

                    ads.append({
                        "id": ad_id,
                        "ad_set_id": ad_set_id,
                        "name": f"{theme} - {ad_type.replace('_', ' ').title()} {ad_idx + 1}",
                        "ad_type": ad_type,
                        "headline": headline,
                        "description": f"Discover {theme.lower()} at FashionFlow. {headline}.",
                        "call_to_action": random.choice(CTAS),
                        "destination_url": f"https://fashionflow.com/promo/{theme.lower().replace(' ', '-')}",
                        "status": "active" if status == "active" else random.choice(["active", "paused", "archived"]),
                        "created_at": camp_start,
                        "updated_at": camp_end if status == "completed" else end_date,
                    })

                    # Daily Performance for this ad
                    base_impressions = random.randint(500, 15000)
                    base_ctr = random.uniform(0.005, 0.06)
                    base_cpc = random.uniform(0.3, 4.0)
                    conv_rate = random.uniform(0.005, 0.04)
                    avg_order_value = random.uniform(60, 200)

                    current = camp_start
                    while current <= camp_end:
                        # Seasonal multiplier
                        month_weight = MONTHLY_ORDER_WEIGHTS[current.month - 1]
                        # Day of week effect
                        dow_mult = 1.1 if current.weekday() < 5 else 0.85
                        # Random daily variance
                        day_mult = random.uniform(0.6, 1.4) * month_weight * dow_mult

                        impressions = max(0, int(base_impressions * day_mult))
                        clicks = max(0, int(impressions * base_ctr * random.uniform(0.7, 1.3)))
                        ctr = round(clicks / impressions, 6) if impressions > 0 else 0.0
                        spend = round(clicks * base_cpc * random.uniform(0.8, 1.2), 2)
                        cpc = round(spend / clicks, 2) if clicks > 0 else 0.0
                        purchases = max(0, int(clicks * conv_rate * random.uniform(0.5, 1.5)))
                        revenue = round(purchases * avg_order_value * random.uniform(0.8, 1.2), 2)

                        daily_performance.append({
                            "id": perf_id,
                            "ad_id": ad_id,
                            "date": current.strftime("%Y-%m-%d"),
                            "impressions": impressions,
                            "clicks": clicks,
                            "spend": spend,
                            "ctr": ctr,
                            "cpc": cpc,
                            "purchases": purchases,
                            "revenue": revenue,
                            "created_at": current + timedelta(hours=23),
                            "updated_at": current + timedelta(hours=23),
                        })
                        perf_id += 1
                        current += timedelta(days=1)

                    ad_id += 1
                ad_set_id += 1
            campaign_id += 1

    return {
        "campaigns": campaigns,
        "ad_sets": ad_sets,
        "ads": ads,
        "daily_performance": daily_performance,
    }


if __name__ == "__main__":
    print("Generating FashionFlow marketing data...")
    data = generate_marketing_data()
    for table, records in data.items():
        print(f"  {table:20s} {len(records):>8,} records")
