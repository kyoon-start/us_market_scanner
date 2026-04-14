"""FastAPI application entrypoint for scanner recommendations."""

from __future__ import annotations

import logging
import time
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import get_default_symbols
from .ranking import rank_recommendations
from .stocks import InvalidSymbolError, StockNotFoundError, get_stock_detail


def configure_logging() -> None:
    """Configure app logging once for scanner processing output."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


configure_logging()
logger = logging.getLogger(__name__)


def utf8_json_response(content: BaseModel | dict[str, Any]) -> JSONResponse:
    """Return a UTF-8 JSON response without ASCII escaping."""
    serializable_content = (
        content.model_dump(mode="json")
        if isinstance(content, BaseModel)
        else content
    )
    return JSONResponse(
        content=serializable_content,
        media_type="application/json; charset=utf-8",
    )


class RecommendationItem(BaseModel):
    """One ranked recommendation item."""

    symbol: str = Field(..., description="Ticker symbol")
    score: int = Field(..., description="Calculated strategy score")
    probability: float | None = Field(
        default=None,
        description="Historical-pattern win probability for the next 5 trading days",
    )
    reason: list[str] = Field(..., description="Reasons that contributed to the score")


class RecommendationResponse(BaseModel):
    """API response for scanner recommendations."""

    swing: list[RecommendationItem]
    long: list[RecommendationItem]


class StockPricePointResponse(BaseModel):
    """One recent daily close point for charting."""

    date: str
    close: float


class StockDetailResponse(BaseModel):
    """API response for one stock's latest detail and scoring breakdown."""

    symbol: str
    latest_close_price: float = Field(..., description="Most recent daily close price")
    swing_score: int = Field(..., description="Calculated swing setup score")
    long_term_score: int = Field(..., description="Calculated long-term setup score")
    swing_probability: float | None = Field(
        default=None,
        description="Historical-pattern swing win probability for the next 5 trading days",
    )
    long_term_probability: float | None = Field(
        default=None,
        description="Historical-pattern long-term win probability for the next 5 trading days",
    )
    swing_reasons: list[str] = Field(..., description="Reasons supporting the swing score")
    long_term_reasons: list[str] = Field(..., description="Reasons supporting the long-term score")
    price_history: list[StockPricePointResponse] = Field(
        default_factory=list,
        description="Last 30 daily closing prices for charting",
    )


app = FastAPI(
    title="US Market Scanner API",
    description="Simple FastAPI backend that ranks US stocks for swing and long-term setups.",
    version="1.0.0",
    default_response_class=JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def root() -> JSONResponse:
    """Basic health endpoint."""
    return utf8_json_response({"message": "US market scanner backend is running"})


@app.get("/recommendations", response_model=RecommendationResponse, tags=["scanner"])
def get_recommendations(
    symbols: Annotated[
        list[str] | None,
        Query(description="Optional repeated query param, for example ?symbols=AAPL&symbols=MSFT"),
    ] = None,
) -> JSONResponse:
    """Return the top ranked swing and long-term stock ideas."""
    selected_symbols = symbols or get_default_symbols()
    logger.info("/recommendations scanning %d symbols", len(selected_symbols))

    start_time = time.perf_counter()
    recommendations = rank_recommendations(selected_symbols)
    elapsed_seconds = time.perf_counter() - start_time

    logger.info("/recommendations completed in %.2f seconds", elapsed_seconds)
    return utf8_json_response(RecommendationResponse(**recommendations))


@app.get("/stocks/{symbol}", response_model=StockDetailResponse, tags=["scanner"])
def get_stock(symbol: str) -> JSONResponse:
    """Return latest price and both scoring views for a single symbol."""
    try:
        stock_detail = get_stock_detail(symbol)
    except InvalidSymbolError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except StockNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return utf8_json_response(StockDetailResponse(**stock_detail))