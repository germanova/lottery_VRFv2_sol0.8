from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import Lottery, network, config, accounts
import time


def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token_contract").address,
        config["params"]["subscriptionId"],
        config["params"]["callbackGasLimit"],
        config["params"]["requestConfirmations"],
        config["networks"][network.show_active()]["key_hash"],
        {"from": account},
        # get verify bool, but if there is no verify use False
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Lottery Deployed: ", Lottery[-1].address)
    return lottery  # for unit test


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("Lottery started and subscription created")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000  # 100000000 to prevent possible errors
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    LINK = 5000000000000000000
    tx = fund_with_link(
        lottery.address,
        amount=LINK,
    )
    tx.wait(1)
    print("LINK added to subscription: ", round(LINK / 100000000000000000, 2))
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    # for waiting response of the VRF
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the winner!")


def cancel_sub():
    account = get_account()
    lottery = Lottery[-1]
    print("Deleting subscription...")
    tx = lottery.cancelSubscription(account, {"from": account})
    tx.wait(1)
    print("Subscription deleted, remaining LINK transfered to: ", account)


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
    cancel_sub()
