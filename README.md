# SuperStakerCheckup
A script to evaluate UTXOs for Super Staker and delegated addresses.

Uses qtum.info API calls to determine the number of mature UTXOs for an address.

Reads a configuration file SSCConfigurationFile.txt for inputs of staker address, required fee, and minimum UTXO size to analyze the Staker UTXOs and the delegate address UTXOs and determine the weight based on:

    for the super staker
    UTXO has > 500 confirmations from the current block height
    UTXO is >= 100.0 QTUM
    
    for the delegted addresses:
    Delegation meets minumum staker fee
    UTXO has > 500 confirmations from the current block height
    UTXO is >= the minimum UTXO size

qtum.info API reference https://github.com/qtumproject/qtuminfo-api#qtuminfo-api-documentation

The format of the UTXO API request is (mainnet):

https://qtum.info/api/address/q_address/utxo

Example output:

```
SuperStakerCheckup 2021-01-18 

Configuration file SSCConfigurationFile.txt:
Staker Address QTJDT..., Staker Fee 3, Staker Min UTXO 100, is Mainet True
Mainnet height 777320

Super Staker QTJDT... 
  Number Valid UTXOs = 257 Sum Valid UTXOs = 25704.36070569
  Number Immature (probably staked) UTXOs = 6 Sum Immature (probably staked) UTXOs = 608.48315254
  Number Too Small UTXOs = 0 Sum Too Small UTXOs = 0.0
  Number Total UTXOs = 263 Sum Total UTXOs 26312.84385823
  Percent Stake to Total = 2.312494825030787 

Delegate QLo9J... Fee 3
  Number Valid UTXOs = 4 Sum Valid UTXOs = 456.28494585
  Number Immature UTXOs = 0 Sum Immature UTXOs = 0.0
  Number Too Small UTXOs = 4 Sum Too Small UTXOs = 7.97643255
  Number Total UTXOs = 8 Sum Total UTXOs 464.2613784 

Delegate QM29f... Fee 3
  Number Valid UTXOs = 1 Sum Valid UTXOs = 132.55552601
  Number Immature UTXOs = 0 Sum Immature UTXOs = 0.0
  Number Too Small UTXOs = 1 Sum Too Small UTXOs = 0.1267916
  Number Total UTXOs = 2 Sum Total UTXOs 132.68231761 

<snip>

Number of valid Staker UTXOs (mature + immature) 263
Number of delegates being staked 33
Delegates weight 220148.20535546 
```
