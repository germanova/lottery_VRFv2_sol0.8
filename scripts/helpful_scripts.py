from brownie import (
    network,
    config,
    accounts,
    Contract,
    MockV3Aggregator,
    VRFCoordinatorV2Mock,
    LinkToken,
)

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def get_account(index=None, id=None):

    if index:
        return accounts[index]
    elif (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    elif id:
        accounts.load(id)
    else:
        return accounts.load(config["wallets"]["account_name"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorV2Mock,
    "link_token_contract": LinkToken,
}


def get_contract(contract_name):
    """
    This Function will gran contract addresses from the brownie config
    if defined, otherwise, it will deploy a mock version of that contract,
    and return that mock contract

        Args:
            contract_name (string)

        Returns:
            brownie.network.contract.ProjectContract: the most recently deployed
            version of this contract

    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            # if no mock have been deployed we deploy one
            deploy_mocks()
            # grab the most recent deployment of the MockV3Aggregator
        contract = contract_type[-1]
    else:  # for testnets
        contract_address = config["networks"][network.show_active()][contract_name]
        print("contract address:", contract_address)
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


# only 8 decimals because in getPrice() function we already multiply by 10 zeroes
DECIMALS = 8
STARTING_PRICE = 200000000000

# VRFCoordinatorV2Mock contructor params
BASE_FEE = 0.25  # LINK Premium found on documentation, same for all networks (Goerli, Rinkeby, Mainnet)
GAS_PRICE_LINK = 1e9  # is some value set dynamically on-chain based on the price of the layer 1 (like ETH, or MATIC) and LINK
# For mocking, setting the GAS_PRICE_LINK to something like 1e9 is probably good.
# https://github.com/smartcontractkit/chainlink-brownie-contracts/issues/13


def deploy_mocks(
    decimals=DECIMALS,
    initial_value=STARTING_PRICE,
    base_fee=BASE_FEE,
    gas_price_link=GAS_PRICE_LINK,
):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    LinkToken.deploy({"from": account})
    VRFCoordinatorV2Mock.deploy(base_fee, gas_price_link, {"from": account})
    print("Mock Deployed")


# 1000000000000000000 = 1 LINK
def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1 LINK
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token_contract")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("Contract Funded")
    return tx
