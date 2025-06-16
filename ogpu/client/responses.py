from typing import List, Optional

import requests
from eth_account import Account
from web3.exceptions import ContractLogicError

from .config import get_private_key
from .contracts import ControllerContract, load_response_contract, load_task_contract
from .types import ConfirmedResponse, Response
from .web3_manager import WEB3


def get_confirmed_response(task_address: str) -> ConfirmedResponse:
    """
    Get confirmed response data for a specific task address by calling the API.

    Args:
        task_address: The task contract address

    Returns:
        ConfirmedResponse object containing the confirmed response data

    Raises:
        Exception: If the API call fails or no confirmed response is found
    """
    try:
        # Make API request to get task responses
        api_url = (
            f"https://provider-viewer-backend.opengpu.network/api/tasks/{task_address}"
        )

        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        api_data = response.json()

        # Extract data and address from the API response
        if "data" not in api_data:
            raise Exception(f"Invalid API response format for task {task_address}")

        data_content = api_data["data"]
        if "address" not in data_content:
            raise Exception(
                f"Address not found in API response for task {task_address}"
            )

        # Create ConfirmedResponse object with the API data
        confirmed_response = ConfirmedResponse(
            address=data_content["address"],
            data=data_content,
        )

        return confirmed_response

    except requests.RequestException as e:
        raise Exception(f"API request failed for task {task_address}: {e}")
    except Exception as e:
        raise Exception(
            f"Error fetching confirmed response for task {task_address}: {e}"
        )


def get_task_responses(
    task_address: str, lower: int = 0, upper: Optional[int] = None
) -> List[Response]:
    """
    Get all responses for a specific task address.

    Args:
        task_address: The task contract address
        lower: Lower bound for response pagination (default: 0)
        upper: Upper bound for response pagination (default: None, gets all)

    Returns:
        List of TaskResponse objects containing response data

    Raises:
        Exception: If the contract call fails or task doesn't exist
    """
    try:
        # Load the task contract
        task_contract = load_task_contract(task_address)

        # Get response addresses from the task
        if upper is None:
            # Get all responses by setting upper to a large number
            # We'll handle the actual limit based on what's available
            try:
                response_addresses = task_contract.functions.getResponsesOf(
                    lower, lower + 1000
                ).call()
            except ContractLogicError:
                # If pagination fails, try to get responses one by one
                response_addresses = []
                i = lower
                while True:
                    try:
                        response_addr = task_contract.functions.getResponsesOf(
                            i, i + 1
                        ).call()
                        if not response_addr:
                            break
                        response_addresses.extend(response_addr)
                        i += 1
                    except (ContractLogicError, Exception):
                        break
        else:
            response_addresses = task_contract.functions.getResponsesOf(
                lower, upper
            ).call()

        # Filter out zero addresses
        response_addresses = [
            addr
            for addr in response_addresses
            if addr != "0x0000000000000000000000000000000000000000"
        ]

        responses = []

        # Get detailed information for each response
        for response_addr in response_addresses:
            try:
                response_contract = load_response_contract(response_addr)

                # Get response parameters
                response_params = response_contract.functions.getResponseParams().call()

                # Get response status
                status = response_contract.functions.getStatus().call()

                # Get response timestamp
                timestamp = response_contract.functions.responseTimestamp().call()

                # Get confirmation status
                confirmed = response_contract.functions.confirmedFinal().call()

                response_data = Response(
                    address=response_addr,
                    task=response_params[0],
                    provider=response_params[1],
                    data=response_params[2],
                    payment=response_params[3],
                    status=status,
                    timestamp=timestamp,
                    confirmed=confirmed,
                )

                responses.append(response_data)

            except Exception as e:
                # Log the error but continue with other responses
                print(f"Error fetching response {response_addr}: {e}")
                continue

        return responses

    except ContractLogicError as e:
        raise Exception(f"Contract call failed for task {task_address}: {e}")
    except Exception as e:
        raise Exception(f"Error fetching responses for task {task_address}: {e}")


def confirm_response(
    response_address: str,
    private_key: str | None = None,
) -> str:
    """
    Confirm a response using the Controller contract.

    Args:
        response_address: The response contract address to confirm
        private_key: Private key for signing the transaction. If None, will use CLIENT_PRIVATE_KEY environment variable.

    Returns:
        str: Transaction hash of the confirmation

    Raises:
        Exception: If the confirmation fails
    """
    if private_key is None:
        private_key = get_private_key()

    # Validate response address format
    if not WEB3.is_address(response_address):
        raise ValueError(f"Invalid response address format: {response_address}")

    acc = Account.from_key(private_key)

    try:
        # First, try to validate the response exists and can be confirmed
        response_contract = load_response_contract(response_address)

        # Check if response is already confirmed
        try:
            confirmed = response_contract.functions.confirmedFinal().call()
            if confirmed:
                raise Exception(f"Response {response_address} is already confirmed")
        except Exception as e:
            if "execution reverted" in str(e).lower():
                raise Exception(
                    f"Response contract {response_address} may not exist or is invalid"
                )
            # If it's another error, continue and let the transaction attempt provide more info

        # Execute the confirmation transaction
        controller_contract = ControllerContract()
        web3 = WEB3()

        tx = controller_contract.functions.confirmResponse(
            response_address
        ).build_transaction(
            {
                "from": acc.address,
                "nonce": web3.eth.get_transaction_count(acc.address),
            }
        )

        signed = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")
        return tx_hash.hex()

    except ContractLogicError as e:
        if "execution reverted" in str(e):
            raise Exception(
                f"Contract execution reverted. Possible reasons: "
                f"1) Response {response_address} doesn't exist, "
                f"2) Already confirmed, "
                f"3) Caller {acc.address} doesn't have permission to confirm, "
                f"4) Response is in invalid state for confirmation"
            )
        raise Exception(f"Contract logic error: {e}")
    except Exception as e:
        if "execution reverted" in str(e).lower():
            raise Exception(
                f"Transaction reverted for response {response_address}. "
                f"Check if the response exists and you have permission to confirm it."
            )
        raise Exception(f"Error confirming response {response_address}: {e}")
