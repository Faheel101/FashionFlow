"""SQLAlchemy ORM models for the FashionFlow marketing domain.

Tables:
    - campaigns: Marketing campaigns across Google Ads and Meta Ads
    - ad_sets: Ad sets/groups within campaigns (targeting, budget)
    - ads: Individual ads within ad sets
    - daily_performance: Daily aggregated metrics per ad
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from source_system.database.models import Base


class Campaign(Base):
    """Marketing campaign across ad platforms."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # google_ads, meta_ads
    objective: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # awareness, traffic, conversions, sales
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # draft, active, paused, completed, archived
    daily_budget: Mapped[float] = mapped_column(Float, nullable=False)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    ad_sets: Mapped[list["AdSet"]] = relationship("AdSet", back_populates="campaign")

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name='{self.name}', platform='{self.platform}')>"


class AdSet(Base):
    """Ad set / ad group within a campaign."""

    __tablename__ = "ad_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    targeting_gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    targeting_age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    targeting_age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    targeting_interests: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_budget: Mapped[float] = mapped_column(Float, nullable=False)
    bid_strategy: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # manual_cpc, target_cpa, maximize_conversions, lowest_cost
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, paused, archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="ad_sets")
    ads: Mapped[list["Ad"]] = relationship("Ad", back_populates="ad_set")

    def __repr__(self) -> str:
        return f"<AdSet(id={self.id}, name='{self.name}')>"


class Ad(Base):
    """Individual ad within an ad set."""

    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ad_sets.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ad_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # image, video, carousel, collection, text
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_to_action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # shop_now, learn_more, sign_up, buy_now
    destination_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, paused, rejected, archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    ad_set: Mapped["AdSet"] = relationship("AdSet", back_populates="ads")
    daily_performance: Mapped[list["DailyPerformance"]] = relationship(
        "DailyPerformance", back_populates="ad"
    )

    def __repr__(self) -> str:
        return f"<Ad(id={self.id}, name='{self.name}')>"


class DailyPerformance(Base):
    """Daily aggregated performance metrics per ad."""

    __tablename__ = "daily_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ads.id"), nullable=False
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spend: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ctr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cpc: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    purchases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    ad: Mapped["Ad"] = relationship("Ad", back_populates="daily_performance")

    def __repr__(self) -> str:
        return f"<DailyPerformance(id={self.id}, ad_id={self.ad_id}, date='{self.date}')>"
