# Aave V3 Risk Monitor

A lightweight Python tool for real-time monitoring of borrower positions on the Aave V3 protocol.

This script bypasses standard indexers (like The Graph or Etherscan APIs) and queries the Aave `Pool` smart contract directly via RPC. This ensures zero-latency data retrieval, which is critical for analyzing liquidation risks during high-volatility events.

## Motivation

Public dashboards often rely on indexed data, which can lag behind the current block state by several seconds or minutes. In liquidation scenarios, this latency renders data useless.

This tool was built to:
1. **Monitor Health Factor (HF)** precision at the block level.
2. **Detect "Looping" strategies** where collateral and debt are correlated assets (e.g., recursive ETH/ETH positions), which carry specific duration risks not always visible in standard UIs.
3. **Audit specific whales** known for high-risk leverage.

## Technical Mechanics

The monitor interacts with the `Pool` contract to fetch `getUserAccountData`. It focuses on the Health Factor metric, defined as:

$$HF = \frac{\sum (Collateral_i \times LT_i)}{Total\ Debt_{Base}}$$

Where `LT` (Liquidation Threshold) is used instead of LTV to determine the exact liquidation trigger point.

**Key Logic:**
- Connects to Ethereum Mainnet via Web3.py.
- Iterates through a pre-defined watchlist of addresses.
- Normalizes 18-decimal integer values to human-readable format.
- Triggers console alerts when `HF < 1.1` (Critical Zone).

## Installation

Requires Python 3.10+.

1. Clone the repository:
   ```bash
   git clone https://github.com/azduR/aave-v3-risk-monitor.git
   cd aave-v3-risk-monitor
    ```

2. Install dependencies:
```bash
pip install web3
```

3. Configure RPC (Optional):
By default, the script uses a public RPC endpoint. For better performance, replace the endpoint in `main.py` with your own (Alchemy/Infura).

## Usage

Run the monitor:

```bash
python main.py
```

**Output example:**

```text
[2025-12-29 14:00:01] Scanning...
User: 0x5AB... | HF: 1.18 | Status: SAFE
User: 0x7a1... | HF: 1.04 | Status: RISKY
```

## Roadmap

* Integration with Pendle Finance to monitor Implied Yield risk on PT-collateral.
* Telegram/Discord webhook integration for push notifications.

## Disclaimer

This software is for educational and research purposes only. It is not financial advice.