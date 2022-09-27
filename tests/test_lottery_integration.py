from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    FORKED_LOCAL_ENVIRONMENTS,
    get_account,
    get_contract,
)
import pytest
import time


def test_can_pick_winner():
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    LINK = 3000000000000000000
    link_token = get_contract("link_token_contract")
    link_token.transfer(lottery.address, LINK * 1.1, {"from": account})
    lottery.topUpSubscription(LINK, {"from": account})
    lottery.endLottery({"from": account})
    time.sleep(60)
    lottery.cancelSubscription(account, {"from": account})
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0


# brownie test -k test_can_pick_winner --network goerli --capture=no
