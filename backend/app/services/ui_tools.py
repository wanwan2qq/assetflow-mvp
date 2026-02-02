"""
UI Tools Definition

This module defines the Pydantic models for UI tools that the LLM can call.
These are used to generate OpenAI-compatible tool definitions.
"""
from typing import Literal

from pydantic import BaseModel, Field


class ShowValuationCard(BaseModel):
    """
    Call this tool when the user asks about property value, valuation, price, or market worth.
    This will trigger a UI card showing detailed valuation data for their real estate assets.
    
    CRITICAL REQUIREMENT:
    - You MUST ONLY call this tool if the asset exists in your Context and has a valid `asset_id`.
    - Do NOT call this for newly mentioned assets that are not yet in `user_assets`.
    
    Example triggers:
    - "How much is my house worth?" (Only if house is already in context)
    - "Show me the valuation."
    - "What's the market price of my property?"
    """
    asset_id: int = Field(
        ..., 
        description="The ID of the EXISTING real estate asset. Do not invent IDs."
    )


class ShowActionPlan(BaseModel):
    """
    Call this tool when the user asks for a plan, proposal, advice summary, or next steps.
    This will trigger a UI card showing the recommended action plan.
    
    Example triggers:
    - "What is your proposal?"
    - "Give me a plan."
    - "Show action plan."
    - "How should I optimize my assets?"
    """
    focus_area: Literal["wealth_protection", "wealth_growth", "debt_optimization", "real_estate", "life_planning"] | None = Field(
        default=None,
        description="The specific area the plan should focus on, if specified by the user."
    )


class ShowPortfolioChart(BaseModel):
    """
    Call this tool when the user asks to see their asset allocation, portfolio structure, or visual analysis.
    This triggers a pie chart or quadrant chart.
    
    IMPORTANT CONSTRAINT:
    - Do NOT call this tool if the user has provided fewer than 2 assets.
    - If data is insufficient, just reply with text asking for more info.
    
    Example triggers:
    - "Show me my portfolio breakdown."
    - "Analyze my asset allocation."
    - "Visualise my assets."
    """
    chart_type: Literal["pie", "quadrant"] = Field(
        default="quadrant",
        description="The type of chart to display. Default to quadrant for Standard & Poor's analysis."
    )


class ShowActionCard(BaseModel):
    """
    Call this tool to recommend a single, specific action or product, usually after analyzing risks.
    
    Example triggers:
    - "What insurance should I buy?"
    - "Recommend a product for liquidity."
    """
    action_type: Literal["insurance", "investment", "loan", "general"] = Field(
        ...,
        description="The category of the action."
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Priority of the recommendation."
    )
    risk_type: str | None = Field(
        default=None,
        description="The specific risk this action addresses (e.g., 'liquidity_risk')."
    )
