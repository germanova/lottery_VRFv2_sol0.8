from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)
import pytest

# Unit Tests: a way of testing the smallest pieces of code in an isolated instace. Run on the development network

# Integration Tests: a way of testing across multiple complex systems. Run on the testnet networks


# ETH 1662.85 usd
ETH_USD = 1578.63  # 30/08/2022 2:10 am
USD_min_fee = 1  # 1 usd
assert_dev = 0.00001


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # eth/usd = 2000, usdEntryFee = 50. Then 2000/1 == 50/x == 0.025
    # expected_entrance_fee = Web3.toWei(USD_min_fee / ETH_USD, "ether")
    expected_entrance_fee = 500000000000000
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert entrance_fee == expected_entrance_fee


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": account, "value": lottery.getEntranceFee()})


def test_cant_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # fund_with_link(lottery)
    # Act
    lottery.endLottery({"from": account})
    # Assert
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    transaction = lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})

    # fundSubscription allows funding a subscription with an arbitrary amount for testing.
    # 1000000000000000000 = 1 LINK
    subscription_id = transaction.events["subscriptionCreation"]["subscriptionId"]
    get_contract("vrf_coordinator").fundSubscription(
        subscription_id, 10000000000000000000, {"from": account}
    )

    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()

    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["requestRandomWords"]["requestId"]
    STATIC_RNG = [777, 888]
    random_request = get_contract("vrf_coordinator").fulfillRandomWordsWithOverride(
        request_id, lottery.address, STATIC_RNG, {"from": account}
    )
    # para que sea efectiva la transacción aumentar el callbackGasLimit en el .yaml. El default era 100000, aumento a 200000
    assert random_request.events["RandomWordsFulfilled"]["success"] is True
    random_request.wait(1)
    # 777%3=0, which means the winner will be the owner account
    assert lottery.s_randomWords(0) == 777
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
