from ogpu.client import confirm_response

tx_hash = confirm_response(
    response_address="0x575162Fb2b19Fd6C3bC8af5Fd1D4F9b832311a34"
)


print(f"Response confirmed in transaction: {tx_hash}")
