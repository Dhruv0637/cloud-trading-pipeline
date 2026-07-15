# cloud-trading-pipeline
A serverless automated algorithmic trading pipeline utilizing Python, AWS Lambda, Amazon EventBridge, and the Alpaca API.


# Cloud-Hosted Algorithmic Trading Pipeline

A serverless, automated quantitative trading pipeline deployed on AWS infrastructure. This system utilizes the Alpaca Trading API to execute a momentum-based Exponential Moving Average (EMA) crossover strategy, running entirely hands-off via scheduled cloud triggers.

## Architecture & Tech Stack
* **Compute:** AWS Lambda (Python 3.12, customized manylinux environment)
* **Automation:** Amazon EventBridge (Cron-based market-open scheduling)
* **Market Data & Execution:** Alpaca API (Paper Trading Environment)
* **Core Libraries:** `pandas`, `numpy`, `alpaca-py`

## trategy Logic
The pipeline executes a **Fast/Slow EMA Crossover** strategy on the SPY ETF:
1. Wakes up automatically at 9:25 AM EST via EventBridge.
2. Fetches a 45-day rolling window of historical market data.
3. Calculates a 9-day (Fast) and 21-day (Slow) Exponential Moving Average.
4. Identifies bullish/bearish crossover events and routes automated execution orders via Alpaca.

## Deployment Notes
* Dependencies were bundled natively for the AWS Linux runtime to prevent Mac OS binary collisions.
* API credentials are strictly managed outside the source code via secure AWS Environment Variables.
