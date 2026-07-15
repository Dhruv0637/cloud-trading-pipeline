import os
import json
import logging
import pandas as pd
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Set up structured logging for AWS CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for the EMA Crossover Trading Strategy.
    Triggered by Amazon EventBridge before market open.
    """
    logger.info("Initializing trading pipeline execution...")

    # 1. Retrieve secure API credentials from AWS Environment Variables
    API_KEY = os.environ.get("ALPACA_API_KEY")
    SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")

    if not API_KEY or not SECRET_KEY:
        logger.error("Missing Alpaca API credentials in environment variables.")
        return {"statusCode": 500, "body": json.dumps("Configuration Error")}

    # 2. Initialize Alpaca Clients (Using paper trading environment)
    data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

    # Target Configuration
    symbol = "SPY"
    fast_period = 9
    slow_period = 21
    qty_to_trade = 1

    logger.info(f"Fetching historical market data for asset: {symbol}")

    try:
        # 3. Request sufficient bars to calculate the slow EMA accurately
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=pd.Timestamp.now() - pd.Timedelta(days=45)
        )
        bars = data_client.get_stock_bars(request_params)
        df = bars.df

        # Calculate Exponential Moving Averages
        df['EMA_Fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['EMA_Slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

        # Extract the latest fully closed calculation values
        latest_row = df.iloc[-1]
        previous_row = df.iloc[-2]

        current_fast = latest_row['EMA_Fast']
        current_slow = latest_row['EMA_Slow']
        prev_fast = previous_row['EMA_Fast']
        prev_slow = previous_row['EMA_Slow']

        logger.info(f"Calculated Fast EMA ({fast_period}d): {current_fast:.2f} | Slow EMA ({slow_period}d): {current_slow:.2f}")

        # 4. Check for Crossover Signals
        # Bullish Crossover: Fast EMA crosses ABOVE Slow EMA
        if prev_fast <= prev_slow and current_fast > current_slow:
            logger.info(f"Bullish crossover detected for {symbol}. Constructing BUY order.")
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty_to_trade,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = trading_client.submit_order(order_data)
            logger.info(f"BUY order successfully submitted to Alpaca. Order ID: {order.id}")

            return {
                "statusCode": 200,
                "action": "BUY",
                "symbol": symbol,
                "fast_ema": float(current_fast),
                "slow_ema": float(current_slow)
            }

        # Bearish Crossover: Fast EMA crosses BELOW Slow EMA
        elif prev_fast >= prev_slow and current_fast < current_slow:
            logger.info(f"Bearish crossover detected for {symbol}. Constructing SELL order.")
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty_to_trade,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            order = trading_client.submit_order(order_data)
            logger.info(f"SELL order successfully submitted to Alpaca. Order ID: {order.id}")

            return {
                "statusCode": 200,
                "action": "SELL",
                "symbol": symbol,
                "fast_ema": float(current_fast),
                "slow_ema": float(current_slow)
            }

        else:
            logger.info("No EMA crossover signal identified. Holding current positions.")
            return {
                "statusCode": 200,
                "action": "HOLD",
                "symbol": symbol,
                "fast_ema": float(current_fast),
                "slow_ema": float(current_slow)
            }

    except Exception as e:
        logger.error(f"Pipeline execution failed due to exception: {str(e)}")
        return {"statusCode": 500, "body": json.dumps("Runtime Exception During Execution")}


# --- LOCAL TESTING BLOCK ---
if __name__ == "__main__":
    import os

    # 1. Mock the AWS Environment Variables locally
    # Replace these strings with your actual Alpaca Paper Trading keys
    os.environ["ALPACA_API_KEY"] = "YOUR_PAPER_API_KEY_HERE"
    os.environ["ALPACA_SECRET_KEY"] = "YOUR_PAPER_SECRET_KEY_HERE"

    # 2. Mock the AWS Event and Context
    test_event = {}
    test_context = None

    # 3. Execute the function and print the result
    print("--- STARTING LOCAL TEST ---")
    result = lambda_handler(test_event, test_context)
    print("\n--- TEST COMPLETE ---")
    print(f"Final Output: {json.dumps(result, indent=2)}")
