import streamlit as st
import pandas as pd
import time
from web3 import Web3

# =============================================================================
# Configuration
# =============================================================================
RPC_URL = "https://eth.llamarpc.com"
POOL_ADDRESS = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"

# Whale Watchlist
WHALE_WATCHLIST = {
    "0x176F3DAb24a159341c0509bB36B833E7fdd0a132": "Justin Sun",
    "0x1bE2056cA0b95113E2FAf8EB590b5b572cc71Ac1": "Random user",
    "0x1129Eca5365F84a6De641f343fDbA1069c1C4B8f": "Random user #2",
    '0x2d8873c5270c64C66E831e1E359f88f9E81A91Fd': 'Random user #3',
    '0x11ec133ec18d2a7ecc48898c84e4395b961f1359': 'Random user #4',
}

# Max uint256 for "No Debt" check
MAX_UINT256 = 115792089237316195423570985008687907853269984665640564039457584007913129639935

# ABI for getUserAccountData
POOL_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
            {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
            {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
            {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
            {"internalType": "uint256", "name": "ltv", "type": "uint256"},
            {"internalType": "uint256", "name": "healthFactor", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# =============================================================================
# Core Logic
# =============================================================================
def get_status(hf: float) -> str:
    """Determine status based on Health Factor."""
    if hf < 1.0:
        return "LIQUIDATABLE"
    elif hf < 1.1:
        return "CRITICAL"
    elif hf < 1.5:
        return "WARNING"
    else:
        return "SAFE"

def format_currency(value: float) -> str:
    """Format a number as USD currency."""
    return f"${value:,.2f}"

@st.cache_resource
def get_web3_connection():
    """Cached Web3 connection."""
    return Web3(Web3.HTTPProvider(RPC_URL))

def fetch_data() -> pd.DataFrame:
    """Fetch Aave V3 account data for all whales in the watchlist."""
    w3 = get_web3_connection()
    
    if not w3.is_connected():
        st.error("Failed to connect to RPC")
        return pd.DataFrame()
    
    pool_address = w3.to_checksum_address(POOL_ADDRESS)
    pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)
    
    data = []
    for address, alias in WHALE_WATCHLIST.items():
        try:
            user_address = w3.to_checksum_address(address)
            user_data = pool_contract.functions.getUserAccountData(user_address).call()
            
            # Parse data
            total_collateral_raw = user_data[0]  # 8 decimals (USD)
            total_debt_raw = user_data[1]        # 8 decimals (USD)
            health_factor_raw = user_data[5]     # 18 decimals
            
            # Convert values
            total_collateral = total_collateral_raw / 10**8
            total_debt = total_debt_raw / 10**8
            
            if health_factor_raw >= MAX_UINT256:
                health_factor = float('inf')
                hf_display = "∞"
            else:
                health_factor = health_factor_raw / 10**18
                hf_display = f"{health_factor:.2f}"
            
            status = get_status(health_factor)
            
            data.append({
                "Alias": alias,
                "Address": address,
                "Health Factor": hf_display,
                "HF_numeric": health_factor,
                "Status": status,
                "Collateral ($)": format_currency(total_collateral),
                "Debt ($)": format_currency(total_debt),
            })
        except Exception as e:
            data.append({
                "Alias": alias,
                "Address": address,
                "Health Factor": "Error",
                "HF_numeric": float('inf'),
                "Status": "ERROR",
                "Collateral ($)": "-",
                "Debt ($)": "-",
            })
    
    return pd.DataFrame(data)

def style_status(row):
    """Apply row styling based on status."""
    status = row["Status"]
    if status == "LIQUIDATABLE":
        return ["background-color: #ff4d4d; color: white"] * len(row)
    elif status == "CRITICAL":
        return ["background-color: #ff9999; color: black"] * len(row)
    elif status == "WARNING":
        return ["background-color: #ffcc00; color: black"] * len(row)
    elif status == "ERROR":
        return ["background-color: #999999; color: white"] * len(row)
    else:
        return ["background-color: #90EE90; color: black"] * len(row)

# =============================================================================
# Streamlit UI
# =============================================================================
st.set_page_config(
    page_title="Aave V3 Risk Monitor",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Aave V3 Risk Monitor")
st.caption("Monitoring whale positions on Aave V3 (Ethereum Mainnet)")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    refresh_rate = st.slider("Refresh Rate (seconds)", min_value=5, max_value=60, value=10)
    auto_refresh = st.checkbox("Auto-Refresh", value=False)
    st.divider()
    st.markdown(f"**RPC:** `{RPC_URL}`")
    st.markdown(f"**Whales Tracked:** {len(WHALE_WATCHLIST)}")

# Manual refresh button
if st.button("🔄 Update Data"):
    st.cache_resource.clear()

# Fetch and display data
df = fetch_data()

if not df.empty:
    # Calculate metrics
    total_whales = len(df)
    numeric_hfs = [hf for hf in df["HF_numeric"] if hf != float('inf')]
    lowest_hf = min(numeric_hfs) if numeric_hfs else float('inf')
    
    if lowest_hf == float('inf'):
        lowest_hf_display = "∞ (All Safe)"
        riskiest_user = "N/A"
    else:
        lowest_hf_display = f"{lowest_hf:.2f}"
        riskiest_idx = df["HF_numeric"].idxmin()
        riskiest_user = df.loc[riskiest_idx, "Alias"]
    
    # Top Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Whales Monitored", total_whales)
    with col2:
        st.metric("Lowest HF Found", lowest_hf_display)
    with col3:
        st.metric("Riskiest User", riskiest_user)
    
    st.divider()
    
    # Main Table
    st.subheader("📊 Whale Positions")
    
    # Prepare display dataframe (drop numeric HF column)
    display_df = df[["Alias", "Health Factor", "Status", "Collateral ($)", "Debt ($)"]].copy()
    
    # Apply styling based on Status column
    def style_row(row):
        status = row["Status"]
        if status == "LIQUIDATABLE":
            return ["background-color: #ff4d4d; color: white"] * len(row)
        elif status == "CRITICAL":
            return ["background-color: #ff9999; color: black"] * len(row)
        elif status == "WARNING":
            return ["background-color: #ffcc00; color: black"] * len(row)
        elif status == "ERROR":
            return ["background-color: #999999; color: white"] * len(row)
        else:
            return ["background-color: #90EE90; color: black"] * len(row)
    
    styled_df = display_df.style.apply(style_row, axis=1)
    
    st.dataframe(styled_df, width="stretch", hide_index=True)
    
    # Status Legend
    with st.expander("📖 Status Legend"):
        st.markdown("""
        | Status | Health Factor | Description |
        |--------|---------------|-------------|
        | 🔴 LIQUIDATABLE | < 1.0 | Position can be liquidated NOW |
        | 🟠 CRITICAL | 1.0 - 1.1 | Extremely high risk of liquidation |
        | 🟡 WARNING | 1.1 - 1.5 | Moderate risk, should add collateral |
        | 🟢 SAFE | > 1.5 | Position is healthy |
        """)

else:
    st.warning("No data available. Check your connection.")

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
