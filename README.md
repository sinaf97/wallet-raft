# Wallet with Raft
Sina Farahani Nia

Mohammad AghaNabi

Alireza Sharzeh

Yasaman ...

# Client
The highest level of the application is the interface with which a user can communicate with the network.
These commands are:
- Check balance
- Deposite
- Withdrawal
- Transfer
- New Wallet

## Check balance
It received a wallet id and returns its balance

## Deposite
It receives a wallet id and the amount of deposite

## Withdrawal
It receives a wallet id and the amount of withdrawal

## Transfer
It receives the origin and destination wallet ids and the amount of transfer

## New Wallet
It creates a new wallet with random id

The client sends request to the proxy server and then the proxy server sends the request to the leader. The rest is at the hands of the leader in the raft network. 
