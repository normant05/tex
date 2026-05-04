from pathlib import Path

import pytest

from src.modules.portfolio import PortfolioError, load_portfolio


def test_load_portfolio_ok() -> None:
    p = load_portfolio("data/portfolio.yaml")
    assert len(p.assets) == 3
    assert p.has_isin("fr0000120073")


def test_reject_invalid_isin(tmp_path: Path) -> None:
    fp = tmp_path / "bad.yaml"
    fp.write_text(
        "assets:\n  - name: x\n    isin: BAD123\n    type: action\n    currency: EUR\n",
        encoding="utf-8",
    )
    with pytest.raises(PortfolioError):
        load_portfolio(fp)


def test_reject_duplicate_isin(tmp_path: Path) -> None:
    fp = tmp_path / "dup.yaml"
    fp.write_text(
        """assets:
  - name: a
    isin: FR0000120073
    type: action
    currency: EUR
  - name: b
    isin: FR0000120073
    type: action
    currency: EUR
""",
        encoding="utf-8",
    )
    with pytest.raises(PortfolioError):
        load_portfolio(fp)
