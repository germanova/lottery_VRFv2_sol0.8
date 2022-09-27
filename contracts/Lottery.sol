// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

// for onlyowner require fuction
import "@openzeppelin/contracts/access/Ownable.sol";

// for VRF API
//import "smartcontractkit/chainlink-brownie-contracts/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "contracts/smartcontractkit/chainlink-brownie-contracts/contracts/src/v0.8/VRFConsumerBaseV2.sol";

// import "smartcontractkit/chainlink-brownie-contracts/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "contracts/smartcontractkit/chainlink-brownie-contracts/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";

// import "smartcontractkit/chainlink-brownie-contracts/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import "contracts/smartcontractkit/chainlink-brownie-contracts/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";

// for ETH/USD API
interface AggregatorV3Interface {
    function decimals() external view returns (uint8);

    function description() external view returns (string memory);

    function version() external view returns (uint256);

    // getRoundData and latestRoundData should both raise "No data present"
    // if they do not have data to report, instead of returning unset values
    // which could be misinterpreted as actual reported values.
    function getRoundData(uint80 _roundId)
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );

    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

// is Ownable as we are using openzeppelin import
// Contracts need to be marked as abstract when at least one of their functions is not implemented.
// Contracts may be marked as abstract even though all functions are implemented.
contract Lottery is VRFConsumerBaseV2, Ownable {
    // variables for lottery setting:

    address payable[] public players; // address of lottery participants
    address payable public recentWinner; // address of winner
    uint256 public randomCheck;
    uint256 public usdEntryFee; // minimum entry of lottery
    AggregatorV3Interface internal EthUsdPriceFeed; // EthUsd API interface

    // Define Lottery States in order to define rules and requirements inside functions
    // enum is used to represent states in the contract in an specific order. OPEN = 0, CLOSED = 1, CALCULATING_WINNER = 2
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;

    ////////////////////////////////////////////////////

    // variables for VRF setting:

    // Coordinator for VRF request
    VRFCoordinatorV2Interface COORDINATOR;

    // useful to transfer LINK to subscription
    LinkTokenInterface LINKTOKEN;

    // Your subscription ID.
    uint64 public s_subscriptionId;

    // The gas lane to use, which specifies the maximum gas price to bump to.
    // For a list of available gas lanes on each network,
    // for goerli is 0x79d3d8832d904592c0bf9818b621522c988bb8b0c05cdc3b15aea1b6e8db0c15
    // see https://docs.chain.link/docs/vrf-contracts/#configurations
    bytes32 public keyHash;

    // Depends on the number of requested values that you want sent to the
    // fulfillRandomWords() function. Storing each word costs about 20,000 gas,
    // so 100,000 is a safe default for this example contract. Test and adjust
    // this limit based on the network that you select, the size of the request,
    // and the processing of the callback request in the fulfillRandomWords()
    // function.
    uint32 public callbackGasLimit;

    // The default is 3, but you can set this higher.
    uint16 public requestConfirmations;

    // For this example, retrieve 1 random values in one request.
    // Cannot exceed VRFCoordinatorV2.MAX_NUM_WORDS.
    uint32 numWords = 2;

    uint256[] public s_randomWords;
    uint256 public s_requestId;

    // events are pieces of data executed and stored in the blockchain, but are not accesible by any smart contract
    // events are mucho more gas efficient than using a storage variable
    // think of them as the print statements of the blockchain

    // At ETHERSCAN in the logs section you can see all the events
    event requestRandomWords(uint256 requestId);
    event subscriptionCreation(uint64 subscriptionId);

    // VRFConsumerBaseV2() adds the VRFConsumerBaseV2 contructor
    // también se añade address _vrfCoordinator que va a ese constructor
    // Goerli coordinator = 0x2Ca8E0C643bDe4C2E08ab1fA0da3401AdAD7734D. For other networks,
    // see https://docs.chain.link/docs/vrf-contracts/#configurations
    constructor(
        address _priceFeedAddress, // of the network
        address _vrfCoordinator, // of the network
        address _link_token_contract, // of the network
        uint64 _subscriptionId, // user owned
        uint32 _callbackGasLimit, // specified by user, default is 100000
        uint16 _requestConfirmations, // specified by user, default is 3
        bytes32 _keyHash // of the network
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        usdEntryFee = 1 * (10**18); // to have unit of measure in wei
        EthUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;

        COORDINATOR = VRFCoordinatorV2Interface(_vrfCoordinator);
        LINKTOKEN = LinkTokenInterface(_link_token_contract);

        // la subscripción es para usar el VRF de ChainLink
        if (_subscriptionId != 0) {
            s_subscriptionId = _subscriptionId;
        }
        keyHash = _keyHash;
        callbackGasLimit = _callbackGasLimit;
        requestConfirmations = _requestConfirmations;
    }

    // Programmatic Subscription Functions:

    // Create a new subscription when the contract is initially deployed.
    function createNewSubscription() private onlyOwner {
        s_subscriptionId = COORDINATOR.createSubscription();
        // Add this contract as a consumer of its own subscription.
        COORDINATOR.addConsumer(s_subscriptionId, address(this));
        emit subscriptionCreation(s_subscriptionId);
    }

    // Assumes this contract owns link.
    // 1000000000000000000 = 1 LINK
    function topUpSubscription(uint256 amount) external onlyOwner {
        LINKTOKEN.transferAndCall(
            address(COORDINATOR),
            amount,
            abi.encode(s_subscriptionId)
        );
    }

    function addConsumer(address consumerAddress) external onlyOwner {
        // Add a consumer contract to the subscription.
        COORDINATOR.addConsumer(s_subscriptionId, consumerAddress);
    }

    function removeConsumer(address consumerAddress) external onlyOwner {
        // Remove a consumer contract from the subscription.
        COORDINATOR.removeConsumer(s_subscriptionId, consumerAddress);
    }

    function cancelSubscription(address receivingWallet) external onlyOwner {
        // Cancel the subscription and send the remaining LINK to a wallet address.
        COORDINATOR.cancelSubscription(s_subscriptionId, receivingWallet);
        s_subscriptionId = 0;
    }

    // Transfer this contract's funds to an address.
    // 1000000000000000000 = 1 LINK
    function withdraw(uint256 amount, address to) external onlyOwner {
        LINKTOKEN.transfer(to, amount);
    }

    // Lottery Functions:

    function enter() public payable {
        // solo se puede participar si el estado es abierto
        require(lottery_state == LOTTERY_STATE.OPEN);
        // 1 USD minimum
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(payable(msg.sender));
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = EthUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; // 18 decimals, ETH/USD price feed already has 8 decimals
        // solidity does not allow decimals so we cant do USD minimum/(ETH/USD conversion rate)
        // so we use (USD minimum * 1000000) /(ETH/USD conversion rate)
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
        createNewSubscription();
    }

    function endLottery() public onlyOwner {
        // so that nobody can start or end the lottery while calculating the winner
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        // make request of aleatory number
        // Assumes the subscription is funded sufficiently.
        // Will revert if subscription is not set and funded.
        s_requestId = COORDINATOR.requestRandomWords(
            keyHash,
            s_subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        // store requestId on event
        emit requestRandomWords(s_requestId);
    }

    // internal so that only the VRF coordinator can call this function
    // override mean we are overriding the original declaration of the function
    function fulfillRandomWords(
        uint256, /* requestId */
        uint256[] memory randomWords // array of random numbers
    ) internal override {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "To fulfill lottery must be in calculating state"
        );
        require(randomWords.length > 0, "random not found yet");
        // a%b divides a by b and returns the remainder
        // Example: 7 players, random number 22. So 22 % 7 = 1,
        uint256 indexofWinner = randomWords[0] % players.length;
        randomCheck = randomWords[0];
        recentWinner = players[indexofWinner];
        recentWinner.transfer(address(this).balance);
        // Reset
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        // store random number
        s_randomWords = randomWords;
    }
}
