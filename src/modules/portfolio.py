from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

import yaml

ISIN_RE = re.compile(r"^[A-Z0-9]{12}$")
VALID_TYPES = {"action", "etf", "fonds", "autre"}


class PortfolioError(ValueError):
    """Raised when the portfolio file is invalid."""


@dataclass(slots=True)
class Asset:
    name: str
    isin: str
    asset_type: str
    currency: str
    notes: str = ""


@dataclass(slots=True)
class Portfolio:
    assets: list[Asset] = field(default_factory=list)

    def add_asset(self, asset: Asset) -> None:
        if self.has_isin(asset.isin):
            raise PortfolioError(f"Duplicate ISIN: {asset.isin}")
        self.assets.append(asset)

    def remove_asset(self, isin: str) -> None:
        before = len(self.assets)
        self.assets = [a for a in self.assets if a.isin != isin.upper()]
        if len(self.assets) == before:
            raise PortfolioError(f"Unknown ISIN: {isin}")

    def has_isin(self, isin: str) -> bool:
        isin = isin.upper()
        return any(a.isin == isin for a in self.assets)


def _validate_isin(isin: str) -> str:
    value = isin.strip().upper()
    if not ISIN_RE.match(value):
        raise PortfolioError(f"Invalid ISIN format: {isin}")
    return value


def _parse_asset(raw: dict) -> Asset:
    required = {"name", "isin", "type", "currency"}
    missing = required - set(raw)
    if missing:
        raise PortfolioError(f"Missing fields: {sorted(missing)}")

    asset_type = str(raw["type"]).strip().lower()
    if asset_type not in VALID_TYPES:
        raise PortfolioError(f"Unsupported asset type: {raw['type']}")

    return Asset(
        name=str(raw["name"]).strip(),
        isin=_validate_isin(str(raw["isin"])),
        asset_type=asset_type,
        currency=str(raw["currency"]).strip().upper(),
        notes=str(raw.get("notes", "")).strip(),
    )


def load_portfolio(path: str | Path) -> Portfolio:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    raw_assets: Iterable[dict] = payload.get("assets", [])

    portfolio = Portfolio()
    for raw in raw_assets:
        asset = _parse_asset(raw)
        portfolio.add_asset(asset)
    return portfolio
