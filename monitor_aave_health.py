from web3 import Web3
import time
from datetime import datetime

# Configuration
RPC_URL = "https://eth.llamarpc.com"
POOL_ADDRESS = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2" 
TARGET_USER = "0xc4aa37375ac1004945d7bced3f222090b3db5bd0"

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

def main():
    # 1. Connect to Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("Failed to connect to RPC")
        return

    print(f"Connected to {RPC_URL}")
    
    # 2. Instantiate Contract
    try:
        pool_address = w3.to_checksum_address(POOL_ADDRESS)
        target_user = w3.to_checksum_address(TARGET_USER)
    except ValueError as e:
        print(f"Error normalizing addresses: {e}")
        return

    pool_contract = w3.eth.contract(address=pool_address, abi=POOL_ABI)
    
    last_status = None
    print(f"Monitoring User: {target_user}")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            # Get Current Timestamp
            now = datetime.now().strftime("%H:%M:%S")
            
            # 3. Call getUserAccountData
            user_data = pool_contract.functions.getUserAccountData(target_user).call()
            health_factor_wei = user_data[5]
            
            current_status = ""
            hf_display = ""
            is_alert = False

            if health_factor_wei >= MAX_UINT256:
                current_status = "SAFE"
                hf_display = "∞ (No Debt)"
            else:
                health_factor = health_factor_wei / 10**18
                hf_display = f"{health_factor:.2f}"
                
                if health_factor < 1.0:
                    current_status = "LIQUIDATION"
                    is_alert = True
                elif health_factor < 1.2:
                    current_status = "RISKY"
                    is_alert = True
                else:
                    current_status = "SAFE"

            # Smart Alert Logic:
            # - Always print if is_alert (HF < 1.2)
            # - Only print "SAFE" if status changed
            if is_alert or current_status != last_status:
                alert_tag = " [ALERT]" if is_alert else ""
                print(f"[{now}] HF: {hf_display} | Status: {current_status}{alert_tag}")
                last_status = current_status
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
