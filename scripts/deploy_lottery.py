from scripts.helpful_scripts import (
    get_account,
    get_contract,
    FORKED_LOCAL_ENVIRONMENTS,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
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
    print("You entered the lottery for ", value)


def end_lottery(LINK):
    account = get_account()
    lottery = Lottery[-1]

    link_token = get_contract("link_token_contract")
    if network.show_active() in FORKED_LOCAL_ENVIRONMENTS:
        tx = link_token.transfer(account, LINK * 3, {"from": accounts[10]})
        tx.wait(1)
        print("LINK send to account from: ", accounts[10])

    tx = link_token.transfer(lottery.address, LINK * 1.2, {"from": account})
    tx.wait(1)
    print(tx.info())
    print(tx.events)
    print(
        "Contract Funded with",
        link_token.balanceOf(lottery.address) / 1000000000000000000,
        "LINK",
    )
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        tx = lottery.topUpSubscription(LINK, {"from": account})
        tx.wait(1)
        print("LINK added to subscription: ", round(LINK / 1000000000000000000, 2))

    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    # for waiting response of the VRF
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the winner!")
    print(f"{lottery.randomCheck()} is the VRF number")


def cancel_sub(LINK):
    account = get_account()
    lottery = Lottery[-1]
    print("Deleting subscription...")
    tx = lottery.cancelSubscription(account, {"from": account})
    tx.wait(1)
    print("Subscription deleted, remaining LINK transfered to: ", account)


def main():
    LINK = 3000000000000000000
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery(LINK)
    if network.show_active() not in FORKED_LOCAL_ENVIRONMENTS:
        cancel_sub(LINK)
