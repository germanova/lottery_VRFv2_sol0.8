FreeCodeCamp course lottery using VRF V2 Mocks, Goerli Testnet and Solidity 0.8
1. Users can enter lottery with ETH based on USD fee
2. An admin will choose when the lottery is over
3. The lottery will select a random winner


How to test?
1. `development` with mocks, random number test returned with fulfillRandomWordsWithOverride() function
2. `testnet`
3. `mainnet-fork-dev` *** credentials are available, however not currently available to fund
subscription through fork, so no random number is returned

Considerations
1. Using ChainLink VRF V2, so subscription creation/delete and LINK subscription funding/cancelation are programmatic so that we can use mocks
2. For unit test, use mock V2 coordinator functions fundSubscription() and fulfillRandomWordsWithOverride()
3. Only openzeppelin dependencies are programmatically imported. For VRFCoordinator, V3Aggregator and LinkToken contracts and its dependencies, are already imported in order to make code understanding easier
4. Integrity test and actual deployment, only available for goerli testnet. Nevertheless, deployment will run 
for development and fork without returning a random number. 
5. For goerli testnet usage, account must have LINK tokens, available at https://faucets.chain.link/ LINK is returned to
account after deployment and testing is finished though subscription cancelation
6. Contract return two random number, if changed to one, it also must be changed at unit test function test_can_pick_winner_correctly(), as input to the mock function fulfillRandomWordsWithOverride()


