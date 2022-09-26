from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
)
import pytest
import time


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})
    fund_with_link({"from": account})
    LINK = 2000000000000000000
    lottery.endLottery(LINK, {"from": account})
    time.sleep(60)
    lottery.withdraw(LINK, account, {"from": account})
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0


# brownie test -k test_can_pick_winner --network goerli --capture=no
