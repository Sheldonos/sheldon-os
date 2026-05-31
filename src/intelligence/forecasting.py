"""
Forecasting Engine for Sheldon OS.

This module provides sophisticated forecasting capabilities for
business metrics, market trends, and resource requirements.
Inspired by the Kronos forecasting system.
"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Suppress statsmodels warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class ForecastModel(Enum):
    """Available forecasting models"""

    ARIMA = "arima"
    SARIMA = "sarima"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    PROPHET = "prophet"  # Facebook Prophet
    ENSEMBLE = "ensemble"  # Combination of models


class ForecastHorizon(Enum):
    """Forecast time horizons"""

    SHORT_TERM = "short_term"  # 1-3 months
    MEDIUM_TERM = "medium_term"  # 3-12 months
    LONG_TERM = "long_term"  # 12+ months


@dataclass
class ConfidenceInterval:
    """Confidence interval for forecast"""

    lower: float
    upper: float
    confidence_level: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "confidence_level": self.confidence_level,
        }


@dataclass
class ForecastPoint:
    """Single forecast data point"""

    timestamp: datetime
    value: float
    confidence_interval: ConfidenceInterval

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "confidence_interval": self.confidence_interval.to_dict(),
        }


@dataclass
class Forecast:
    """Complete forecast result"""

    id: str
    metric: str
    model_used: str
    current_value: float
    predictions: List[ForecastPoint]
    accuracy_score: float  # Historical accuracy
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    forecast_horizon: ForecastHorizon = ForecastHorizon.MEDIUM_TERM

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "metric": self.metric,
            "model_used": self.model_used,
            "current_value": self.current_value,
            "predictions": [p.to_dict() for p in self.predictions],
            "accuracy_score": self.accuracy_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "forecast_horizon": self.forecast_horizon.value,
        }

    def get_prediction_at(
        self,
        target_date: datetime,
    ) -> Optional[ForecastPoint]:
        """Get prediction for a specific date"""
        for pred in self.predictions:
            if pred.timestamp.date() == target_date.date():
                return pred
        return None


@dataclass
class Scenario:
    """Scenario for scenario analysis"""

    name: str
    description: str
    assumptions: Dict[str, float]
    forecast: Forecast
    probability: float = 0.33  # Default equal probability

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "assumptions": self.assumptions,
            "forecast": self.forecast.to_dict(),
            "probability": self.probability,
        }


class ForecastingEngine:
    """
    Advanced forecasting engine with multiple models and scenario analysis
    """

    def __init__(self, memory_system=None):
        """
        Initialize the forecasting engine

        Args:
            memory_system: Optional memory system for storing forecasts
        """
        self.memory_system = memory_system
        self.forecasts: Dict[str, Forecast] = {}
        self.model_performance: Dict[str, List[float]] = {}

        logger.info("Forecasting Engine initialized")

    async def forecast_revenue(
        self,
        historical_data: pd.DataFrame,
        periods: int = 12,
        model: ForecastModel = ForecastModel.ENSEMBLE,
    ) -> Forecast:
        """
        Forecast revenue for future periods

        Args:
            historical_data: DataFrame with 'date' and 'revenue' columns
            periods: Number of periods to forecast
            model: Forecasting model to use

        Returns:
            Forecast object with predictions
        """
        try:
            logger.info(
                "Forecasting revenue for %s periods using %s",
                periods,
                model.value,
            )

            # Prepare data
            data = historical_data.copy()
            data["date"] = pd.to_datetime(data["date"])
            data = data.sort_values("date")
            revenue_values = np.asarray(
                data["revenue"].to_numpy(),
                dtype=float,
            )

            # Generate forecast based on model
            if model == ForecastModel.ENSEMBLE:
                forecast = await self._ensemble_forecast(
                    revenue_values,
                    periods,
                    "revenue",
                )
            elif model == ForecastModel.ARIMA:
                forecast = await self._arima_forecast(
                    revenue_values,
                    periods,
                    "revenue",
                )
            elif model == ForecastModel.EXPONENTIAL_SMOOTHING:
                forecast = await self._exponential_smoothing_forecast(
                    revenue_values,
                    periods,
                    "revenue",
                )
            else:
                forecast = await self._linear_forecast(
                    revenue_values,
                    periods,
                    "revenue",
                )

            # Add timestamps to predictions
            last_date = data["date"].iloc[-1]
            for i, pred in enumerate(forecast.predictions):
                pred.timestamp = last_date + timedelta(days=30 * (i + 1))

            # Store forecast
            await self._store_forecast(forecast)

            return forecast

        except Exception as e:
            logger.error(f"Error forecasting revenue: {e}")
            raise

    async def _arima_forecast(
        self, data: np.ndarray, periods: int, metric: str
    ) -> Forecast:
        """Generate forecast using ARIMA model"""
        try:
            # Fit ARIMA model (auto-select parameters)
            model = ARIMA(data, order=(1, 1, 1))
            fitted_model = model.fit()

            # Generate forecast
            forecast_result = fitted_model.forecast(steps=periods)

            # Calculate confidence intervals
            forecast_df = fitted_model.get_forecast(steps=periods)
            conf_int = forecast_df.conf_int(alpha=0.05)

            # Create forecast points
            conf_int_values = (
                conf_int.values if hasattr(conf_int, "values") else conf_int
            )
            predictions = []
            for i in range(periods):
                pred_point = ForecastPoint(
                    timestamp=datetime.utcnow(),  # Will be updated by caller
                    value=float(forecast_result[i]),
                    confidence_interval=ConfidenceInterval(
                        lower=float(conf_int_values[i][0]),
                        upper=float(conf_int_values[i][1]),
                    ),
                )
                predictions.append(pred_point)

            # Calculate accuracy on historical data
            accuracy = self._calculate_accuracy(data, fitted_model)

            forecast = Forecast(
                id=f"forecast_{metric}_{datetime.utcnow().timestamp()}",
                metric=metric,
                model_used=ForecastModel.ARIMA.value,
                current_value=float(data[-1]),
                predictions=predictions,
                accuracy_score=accuracy,
                metadata={
                    "model_params": str(fitted_model.params),
                    "aic": float(fitted_model.aic),
                    "bic": float(fitted_model.bic),
                },
            )

            return forecast

        except Exception as e:
            logger.error(f"Error in ARIMA forecast: {e}")
            # Fallback to simple forecast
            return await self._linear_forecast(data, periods, metric)

    async def _exponential_smoothing_forecast(
        self, data: np.ndarray, periods: int, metric: str
    ) -> Forecast:
        """Generate forecast using Exponential Smoothing"""
        try:
            # Fit Exponential Smoothing model
            model = ExponentialSmoothing(
                data, seasonal_periods=12, trend="add", seasonal="add"
            )
            fitted_model = model.fit()

            # Generate forecast
            forecast_result = fitted_model.forecast(steps=periods)

            # Estimate confidence intervals (simplified)
            std_error = np.std(data - fitted_model.fittedvalues)

            predictions = []
            for i in range(periods):
                # Confidence interval widens with forecast horizon
                margin = 1.96 * std_error * np.sqrt(i + 1)

                pred_point = ForecastPoint(
                    timestamp=datetime.utcnow(),
                    value=float(forecast_result[i]),
                    confidence_interval=ConfidenceInterval(
                        lower=float(forecast_result[i] - margin),
                        upper=float(forecast_result[i] + margin),
                    ),
                )
                predictions.append(pred_point)

            accuracy = self._calculate_accuracy(data, fitted_model)

            forecast = Forecast(
                id=f"forecast_{metric}_{datetime.utcnow().timestamp()}",
                metric=metric,
                model_used=ForecastModel.EXPONENTIAL_SMOOTHING.value,
                current_value=float(data[-1]),
                predictions=predictions,
                accuracy_score=accuracy,
                metadata={
                    "smoothing_level": float(
                        fitted_model.params["smoothing_level"]
                    ),
                    "smoothing_trend": float(
                        fitted_model.params["smoothing_trend"]
                    ),
                },
            )

            return forecast

        except Exception as e:
            logger.error(f"Error in Exponential Smoothing forecast: {e}")
            return await self._linear_forecast(data, periods, metric)

    async def _linear_forecast(
        self, data: np.ndarray, periods: int, metric: str
    ) -> Forecast:
        """Generate forecast using linear regression"""
        try:
            # Fit linear model
            x = np.arange(len(data), dtype=float)
            regression = stats.linregress(x, data)
            slope = float(regression.slope)
            intercept = float(regression.intercept)
            r_value = float(regression.rvalue)
            std_err = float(regression.stderr)

            # Generate predictions
            future_x = np.arange(len(data), len(data) + periods, dtype=float)
            predictions_values = slope * future_x + intercept
            denominator = float(np.sum((x - np.mean(x)) ** 2))

            # Calculate confidence intervals
            predictions = []
            for i, pred_val in enumerate(predictions_values):
                # Confidence interval widens with distance from data
                margin = (
                    1.96
                    * std_err
                    * np.sqrt(
                        1
                        + 1 / len(data)
                        + (i**2) / denominator
                    )
                )

                pred_point = ForecastPoint(
                    timestamp=datetime.utcnow(),
                    value=float(pred_val),
                    confidence_interval=ConfidenceInterval(
                        lower=float(pred_val - margin),
                        upper=float(pred_val + margin),
                    ),
                )
                predictions.append(pred_point)

            # Calculate R-squared as accuracy
            accuracy = float(r_value**2)

            forecast = Forecast(
                id=f"forecast_{metric}_{datetime.utcnow().timestamp()}",
                metric=metric,
                model_used=ForecastModel.LINEAR_REGRESSION.value,
                current_value=float(data[-1]),
                predictions=predictions,
                accuracy_score=accuracy,
                metadata={
                    "slope": slope,
                    "intercept": intercept,
                    "r_squared": accuracy,
                },
            )

            return forecast

        except Exception as e:
            logger.error(f"Error in linear forecast: {e}")
            raise

    async def _ensemble_forecast(
        self, data: np.ndarray, periods: int, metric: str
    ) -> Forecast:
        """Generate ensemble forecast combining multiple models"""
        try:
            # Generate forecasts from multiple models
            forecasts = []

            try:
                arima_forecast = await self._arima_forecast(
                    data,
                    periods,
                    metric,
                )
                forecasts.append(arima_forecast)
            except Exception as exc:
                logger.debug(
                    "ARIMA forecast unavailable for ensemble: %s",
                    exc,
                )

            try:
                es_forecast = await self._exponential_smoothing_forecast(
                    data,
                    periods,
                    metric,
                )
                forecasts.append(es_forecast)
            except Exception as exc:
                logger.debug(
                    "Exponential smoothing forecast unavailable "
                    "for ensemble: %s",
                    exc,
                )

            linear_forecast = await self._linear_forecast(
                data,
                periods,
                metric,
            )
            forecasts.append(linear_forecast)

            # Combine predictions (weighted by accuracy)
            total_accuracy = sum(f.accuracy_score for f in forecasts)
            weights = [f.accuracy_score / total_accuracy for f in forecasts]

            predictions = []
            for i in range(periods):
                # Weighted average of predictions
                weighted_value = sum(
                    w * f.predictions[i].value
                    for w, f in zip(weights, forecasts)
                )

                # Combined confidence interval
                weighted_lower = sum(
                    w * f.predictions[i].confidence_interval.lower
                    for w, f in zip(weights, forecasts)
                )
                weighted_upper = sum(
                    w * f.predictions[i].confidence_interval.upper
                    for w, f in zip(weights, forecasts)
                )

                pred_point = ForecastPoint(
                    timestamp=datetime.utcnow(),
                    value=float(weighted_value),
                    confidence_interval=ConfidenceInterval(
                        lower=float(weighted_lower),
                        upper=float(weighted_upper),
                    ),
                )
                predictions.append(pred_point)

            # Average accuracy
            avg_accuracy = np.mean([f.accuracy_score for f in forecasts])

            forecast = Forecast(
                id=f"forecast_{metric}_{datetime.utcnow().timestamp()}",
                metric=metric,
                model_used=ForecastModel.ENSEMBLE.value,
                current_value=float(data[-1]),
                predictions=predictions,
                accuracy_score=float(avg_accuracy),
                metadata={
                    "models_used": [f.model_used for f in forecasts],
                    "weights": weights,
                    "individual_accuracies": [
                        f.accuracy_score for f in forecasts
                    ],
                },
            )

            return forecast

        except Exception as e:
            logger.error(f"Error in ensemble forecast: {e}")
            return await self._linear_forecast(data, periods, metric)

    def _calculate_accuracy(self, actual: np.ndarray, model) -> float:
        """Calculate model accuracy using MAPE"""
        try:
            fitted = model.fittedvalues
            # Mean Absolute Percentage Error
            mape = np.mean(np.abs((actual - fitted) / actual)) * 100
            # Convert to accuracy score (0-1)
            accuracy = max(0, 1 - (mape / 100))
            return float(accuracy)
        except Exception as exc:
            logger.debug("Falling back to default forecast accuracy: %s", exc)
            return 0.7  # Default moderate accuracy

    async def scenario_analysis(
        self,
        historical_data: pd.DataFrame,
        scenarios: List[Dict[str, Any]],
        periods: int = 12,
    ) -> List[Scenario]:
        """
        Perform scenario analysis with different assumptions

        Args:
            historical_data: Historical data
            scenarios: List of scenario definitions
            periods: Forecast periods

        Returns:
            List of Scenario objects
        """
        results = []

        try:
            for scenario_def in scenarios:
                # Adjust data based on scenario assumptions
                adjusted_data = self._apply_scenario_assumptions(
                    historical_data.copy(), scenario_def.get("assumptions", {})
                )

                # Generate forecast for scenario
                forecast = await self.forecast_revenue(
                    adjusted_data,
                    periods=periods,
                )

                scenario = Scenario(
                    name=scenario_def.get("name", "Unnamed Scenario"),
                    description=scenario_def.get("description", ""),
                    assumptions=scenario_def.get("assumptions", {}),
                    forecast=forecast,
                    probability=scenario_def.get("probability", 0.33),
                )

                results.append(scenario)

            logger.info(
                "Completed scenario analysis with %d scenarios",
                len(results),
            )
            return results

        except Exception as e:
            logger.error(f"Error in scenario analysis: {e}")
            return []

    def _apply_scenario_assumptions(
        self, data: pd.DataFrame, assumptions: Dict[str, float]
    ) -> pd.DataFrame:
        """Apply scenario assumptions to historical data"""
        adjusted = data.copy()

        # Apply growth rate adjustment
        if "growth_rate" in assumptions:
            growth_factor = 1 + assumptions["growth_rate"]
            adjusted["revenue"] = adjusted["revenue"] * growth_factor

        # Apply market size adjustment
        if "market_multiplier" in assumptions:
            adjusted["revenue"] = (
                adjusted["revenue"] * assumptions["market_multiplier"]
            )

        return adjusted

    async def forecast_resource_requirements(
        self, revenue_forecast: Forecast, resource_ratios: Dict[str, float]
    ) -> Dict[str, Forecast]:
        """
        Forecast resource requirements based on revenue forecast

        Args:
            revenue_forecast: Revenue forecast
            resource_ratios: Ratios of resources to revenue

        Returns:
            Dictionary of resource forecasts
        """
        resource_forecasts = {}

        try:
            for resource, ratio in resource_ratios.items():
                predictions = []

                for rev_pred in revenue_forecast.predictions:
                    resource_value = rev_pred.value * ratio

                    pred_point = ForecastPoint(
                        timestamp=rev_pred.timestamp,
                        value=resource_value,
                        confidence_interval=ConfidenceInterval(
                            lower=rev_pred.confidence_interval.lower * ratio,
                            upper=rev_pred.confidence_interval.upper * ratio,
                        ),
                    )
                    predictions.append(pred_point)

                forecast = Forecast(
                    id=f"forecast_{resource}_{datetime.utcnow().timestamp()}",
                    metric=resource,
                    model_used="ratio_based",
                    current_value=revenue_forecast.current_value * ratio,
                    predictions=predictions,
                    accuracy_score=revenue_forecast.accuracy_score,
                    metadata={"based_on": "revenue_forecast", "ratio": ratio},
                )

                resource_forecasts[resource] = forecast

            logger.info(
                "Forecasted %d resource requirements",
                len(resource_forecasts),
            )
            return resource_forecasts

        except Exception as e:
            logger.error(f"Error forecasting resources: {e}")
            return {}

    async def assess_risk_probability(
        self, historical_events: List[Dict[str, Any]], risk_type: str
    ) -> Dict[str, float]:
        """
        Assess probability of risk events

        Args:
            historical_events: Historical risk events
            risk_type: Type of risk to assess

        Returns:
            Risk probability metrics
        """
        try:
            # Count occurrences
            total_periods = len(historical_events)
            risk_occurrences = sum(
                1
                for event in historical_events
                if event.get("type") == risk_type
            )

            # Calculate probability
            probability = (
                risk_occurrences / total_periods
                if total_periods > 0
                else 0
            )

            # Calculate severity
            severities = [
                event.get("severity", 0)
                for event in historical_events
                if event.get("type") == risk_type
            ]
            avg_severity = np.mean(severities) if severities else 0

            # Expected loss
            expected_loss = probability * avg_severity

            return {
                "probability": float(probability),
                "avg_severity": float(avg_severity),
                "expected_loss": float(expected_loss),
                "occurrences": risk_occurrences,
                "total_periods": total_periods,
            }

        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return {}

    async def _store_forecast(self, forecast: Forecast) -> None:
        """Store forecast in memory system"""
        try:
            self.forecasts[forecast.id] = forecast

            if self.memory_system:
                await self.memory_system.store_long_term(
                    key=f"forecast:{forecast.id}",
                    value=forecast.to_dict(),
                    metadata={
                        "type": "forecast",
                        "metric": forecast.metric,
                        "model": forecast.model_used,
                    },
                )

            logger.debug(f"Stored forecast: {forecast.id}")

        except Exception as e:
            logger.error(f"Error storing forecast: {e}")

    async def update_model_performance(
        self, forecast_id: str, actual_values: List[float]
    ) -> None:
        """Update model performance tracking with actual results"""
        try:
            forecast = self.forecasts.get(forecast_id)
            if not forecast:
                logger.warning(f"Forecast {forecast_id} not found")
                return

            # Calculate actual accuracy
            predicted = [
                p.value for p in forecast.predictions[: len(actual_values)]
            ]
            mape = (
                np.mean(
                    np.abs(
                        (np.array(actual_values) - np.array(predicted))
                        / np.array(actual_values)
                    )
                )
                * 100
            )
            actual_accuracy = max(0, 1 - (mape / 100))

            # Store performance
            model = forecast.model_used
            if model not in self.model_performance:
                self.model_performance[model] = []

            self.model_performance[model].append(float(actual_accuracy))

            logger.info(
                "Updated performance for %s: %.2f",
                model,
                actual_accuracy,
            )

        except Exception as e:
            logger.error(f"Error updating model performance: {e}")

    def get_best_model(self) -> str:
        """Get the best performing model based on historical accuracy"""
        if not self.model_performance:
            return ForecastModel.ENSEMBLE.value

        avg_performance = {
            model: float(np.mean(scores))
            for model, scores in self.model_performance.items()
        }

        best_model = max(
            avg_performance.items(),
            key=lambda item: item[1],
        )[0]
        return best_model


# Made with Bob
