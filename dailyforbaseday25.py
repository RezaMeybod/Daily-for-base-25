# Truncated for brevity – replace with the full compiled bytecode of the contract
BASE_TOKEN_BYTECODE = (
    "608060405234801561001057600080fd5b506040516104b93803806104b983398101604081"
    "5281016040805180910390f35b600080fd5b600080fd5b600080fd5b6000908152602080fd"
    "6000819055507f5a0e1f1e2d2e3f5c4d6a5a5c5b6c4b7d8e9f5a6b7c8d9e0f1a2b3c4d5e6f7"
    "8a5b6c7d8e9f5a6b7c8d9e0f1a2b3c4d5e6000604051808303818602009a603f565b6000"
    "fd5b6100b58061006c6000396000f3fe608060405260043610610056576000357c01"
    # ... (full bytecode goes here) ...
    "0015f0b3f5e2c5f0b3a0d1c3f7e6d7c9b8a6c5d4e3f2c1b0a9e8d7c6b5a4f3e2d1c0b"
)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deploy a simple ERC‑20 Base Token")
    p.add_argument("--rpc", required=True, help="EVM RPC endpoint URL")
    p.add_argument("--private-key", required=True, help="Deployer private key")
    p.add_argument("--name", default="Base Token", help="Token name")
    p.add_argument("--symbol", default="BASE", help="Token symbol")
    p.add_argument("--decimals", type=int, default=18, help="Decimals (default 18)")
    p.add_argument(
        "--total-supply",
        type=float,
        required=True,
        help="Total supply in human‑readable units (e.g. 1_000_000)",
    )
    p.add_argument("--gas-price", type=int, default=None, help="Gas price in wei")
    p.add_argument("--nonce", type=int, default=None, help="Tx nonce (optional)")
    return p.parse_args()

def load_account(pk: str) -> Account:
    pk = pk.strip()
    if pk.startswith("0x"):
        pk = pk[2:]
    return Account.from_key(pk)

def build_constructor_args(name: str, symbol: str, decimals: int, total_supply: float):
    supply_int = int(total_supply * (10 ** decimals))
    return (name, symbol, decimals, supply_int)

def main() -> None:
    args = parse_args()
    w3 = Web3(Web3.HTTPProvider(args.rpc))
    if not w3.is_connected():
        sys.exit("❌ Cannot connect to the RPC endpoint")
    acct = load_account(args.private_key)
    print(f"🔑 Deployer address: {acct.address}")

    contract = w3.eth.contract(abi=BASE_TOKEN_ABI, bytecode=BASE_TOKEN_BYTECODE)

    ctor_args = build_constructor_args(
        args.name, args.symbol, args.decimals, args.total_supply
    )

    # Estimate gas
    try:
        gas_est = contract.constructor(*ctor_args).estimate_gas({"from": acct.address})
    except ContractLogicError as e:
        sys.exit(f"❌ Gas estimation failed: {e}")

    tx_dict = contract.constructor(*ctor_args).build_transaction(
        {
            "from": acct.address,
            "nonce": args.nonce if args.nonce is not None else w3.eth.get_transaction_count(acct.address),
            "gas": gas_est + 10_000,
            "gasPrice": args.gas_price if args.gas_price is not None else w3.eth.gas_price,
        }
    )

    signed = acct.sign_transaction(tx_dict)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"📤 Tx sent – hash: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"✅ Deployed at: {receipt.contractAddress}")
    else:
        print("❌ Deployment failed (receipt status = 0)")

if name == "main":
    main()
