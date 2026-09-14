from dataclasses import dataclass
from typing import Optional


VALID_COUNTRIES = {"Brazilian Stock", "USA Stock"}


@dataclass
class ModelStock:
    ticker: str
    country: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

    def __post_init__(self):
        self.ticker = self.ticker.upper().strip()

        if self.country not in VALID_COUNTRIES:
            raise ValueError(
                f"Invalid country '{self.country}'. "
                f"Must be one of: {VALID_COUNTRIES}"
            )

    @property
    def is_brazilian(self) -> bool:
        return self.country == "Brazilian Stock"

    @property
    def is_american(self) -> bool:
        return self.country == "USA Stock"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ticker={self.ticker!r}, country={self.country!r})"


@dataclass
class Stock(ModelStock):
    """Representa uma ação americana (USA Stock)."""

    def __init__(self, ticker: str, name: Optional[str] = None, sector: Optional[str] = None, industry: Optional[str] = None):
        super().__init__(
            ticker=ticker,
            country="USA Stock",
            name=name,
            sector=sector,
            industry=industry,
        )


@dataclass
class Acao(ModelStock):
    """Representa uma ação brasileira (Brazilian Stock)."""

    def __init__(self, ticker: str, name: Optional[str] = None, sector: Optional[str] = None, industry: Optional[str] = None):
        super().__init__(
            ticker=ticker,
            country="Brazilian Stock",
            name=name,
            sector=sector,
            industry=industry,
        )
