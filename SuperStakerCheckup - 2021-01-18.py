version = "2021-01-18"

'''
SuperStakerCheckup.py 

Copyright (c) 2020 Jackson Belove
Beta software, use at your own risk
MIT License, free, open software for the Qtum Community

= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

A program to use qtum.info API calls to determine the number of mature UTXOs for
an address.

Uses configuration file inputs of staker address, required fee, and minimum UTXO
size to analyze the Staker UTXOs and the delegate address UTXOs
and determine the weight based on:

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

To Add


Revisions

2020-12-26 Repurposed from GetWeightForAddresses - Multiple

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

Program Summary

On startup read the configuration file for staker address, fee,
  minimum delegated UTXO size, and mainnet true or false (false = testnet)

Call the qtum.info API to get the current block height.

Call the qtum.info API to analyse current UTXOs for staker.

Loop through all the delegates and analyze their UTXOs.

Print statistics, warnings, etc.

UTXos are sorted into three categores:
  valid UTXOs: mature and big enough for staking
  too small UTXOs (for delegated addresses) are smaller than the size a super staker will stake
  immature UTXOs have < 500 confirmations, may be new UTXOs or stakes

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

'''

from timeit import default_timer as timer               # for timer()
import sys                                              # for system exit
import urllib.request                                   # for reading Web sites, Python 3
from urllib.request import Request, urlopen
import urllib.request as urlRequest
from urllib.error import URLError, HTTPError            # for URL errors

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def read_config_file(configFileName):
    # read in parameters from the configuration file
    # print configuration at startup

    global stakerAddress            # Address of super staker
    global stakerFee                # Required fee for super staker
    global stakerMinUTXOSize        # minimum UTXO size for delegated addresses
    global isMainnet                # Boolean for mainnet or testnet
    global data                     # data from the config file
  
    '''
    "stakerAddress": qMUR738THXBXABfx1Rk6iWtiStEPtQKWYK,
    "stakerFee": 10,
    "stakerMinUTXOSize": 100,
    "isMainnet": false,
    '''

    try:
        configFile = open(configFileName, 'r', encoding="latin-1")  # check for success, or exit
    except:
        print("ERROR opening configuration file")
        print('The configuration file "SSCConfigurationFile.txt" must be in the same directory with SuperStakerCheckup')
        sys.exit()
        
    data = configFile.read()
    lenData = len(data)
    configFile.close()

    # print(data)

    # parse the configuration values
    
    dataIndex = data.find("stakerAddress", 0, lenData) + 16  # first character of staker address

    # print("dataIndex =", dataIndex)
	
    if dataIndex > 0:                       # found address
        for i in range(34):
            stakerAddress += data[dataIndex + i]

    # print("stakerAddress =", stakerAddress)

    dataIndex = data.find("stakerFee", dataIndex, lenData) + 12

    temp = ''

    if dataIndex > 0:                       # found fee
        for i in range(3):
            if data[dataIndex + i] >= "0" and data[dataIndex + i] <= "9":
                temp += data[dataIndex + i]
            else:
                break

    stakerFee = int(temp)

    # print("stakerFee =", stakerFee)

    dataIndex = data.find("stakerMinUTXOSize", dataIndex, lenData) + 20 

    temp = ''

    if dataIndex > 0:                       # found stakerMinUTXOSize
        for i in range(6):                  # but probably range is 0..100
            if data[dataIndex + i] >= "0" and data[dataIndex + i] <= "9":
                temp += data[dataIndex + i]
            else:
                break

    stakerMinUTXOSize = int(temp)

    # print("stakerMinUTXOSize =", stakerMinUTXOSize)

    temp = ''
    i = 0

    dataIndex = data.find("isMainnet", dataIndex, lenData) + 12
    
    if dataIndex > 0:
        while i <= lenData - 1:

            if data[dataIndex + i] >= 'a' and data[dataIndex + i] <= 'z':
                temp += data[dataIndex + i]
            elif data[dataIndex + i] == ",":
                break
            else:
                print("SSC error, bad character in isMainnet")
                sys.exit()
                    
            i += 1
                    
            if i >= lenData:
                break 
        
        if temp == "true":
            isMainnet = True
        elif temp == "false":	
            isMainnet = False
        else:
            print("Bad value in configuration file isMainnet")
            sys.exit()

    # print("isMainnet =", isMainnet)

    tempStr = "Configuration file " + config_file_name + ":"
    print(tempStr)
    tempStr = "Staker Address " + stakerAddress + ", Staker Fee " + str(stakerFee) + ", Staker Min UTXO " +\
           str(stakerMinUTXOSize) + ", is Mainet " + str(isMainnet)
    print(tempStr)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    

def get_staker_address_weight(address, height):

    global headers
    global intStakerValidUTXOs  # number of valid UTXOs for this staker, mature + immature
    
    intsatsSumTotalUTXOs = 0    # total sum of all delegate UTXOs evaluated
    intsatsSumValidUTXOs = 0    # delegate weight, sum value of UTXOs that are mature and big enough to stake
    intsatsSumImmatureUTXOs = 0 # sum of the immature UTXOs
    intsatsSumTooSmallUTXOs = 0 # sum of too small UTXOs
    splitFlag = False           # found a UTXO > 200.0, should be split

    if isMainnet == True:
        url = APIEndpointMainnet + "address/" + address + "/utxo"
    else:
        url = APIEndpointTestnet + "address/" + address + "/utxo"

    # print("url ", url)

    # sys.exit()

    result = ""            

    try:                
        req = Request(url, headers = headers)
        # open the url
        x = urlRequest.urlopen(req)
        result = x.read()

    except URLError as e:
        print("We failed to reach a server for ", url)
        print("ULR Reason: ", e.reason)

    # print(result)

    data = str(result)
    lenData = len(data)

    # print("lenData", lenData)

    '''
    b'[
    {"transactionId":"e5ec014b5021c2905faebc0774202cc9418331e0b645229ca1cca677e40229c3",
    "outputIndex":1,"scriptPubKey":"21031f48b26481bea513a84573de5f62b4b23d2989a823158e897ce85f755818f04fac",
    "address":"qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","value":"10179000000","isStake":true,
    "blockHeight":358641,"confirmations":274890},

    {"transactionId":"3350acdf13625897f53570b87969c3086b0f2d087fb4c88be7b4fa6d884c54ef",
    "outputIndex":1,"scriptPubKey":"21031f48b26481bea513a84573de5f62b4b23d2989a823158e897ce85f755818f04fac",
    "address":"qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","value":"10967000000","isStake":true,
    "blockHeight":368196,"confirmations":265335},

    <snip>

    '''

    # sys.exit()

    dataIndex = 0

    numTotalUTXOs = 0       # total number of UTXOs evaluated
    numValidUTXOs = 0       # number of UTXOs that are mature and big enough (for delegates) to stake
    numTooSmallUTXOs = 0    # the number of too small UTXOs (immature or mature)
    numImmatureUTXOs = 0    # number of immature UTXOs

    minimumSatsValue = 10000000000  # consensus requirement, 100.0 QTUM minimum
    maturity = 500
    matureUTXOHeight = int(height) - maturity

    while dataIndex < lenData:

        value = ' '
        blockHeight = ' '
            
        dataIndex = data.find("value", dataIndex)

        # print("dataIndex =", dataIndex)

        if dataIndex > 0:       # found "value"

            numTotalUTXOs += 1

            dataIndex += 8      # point at the first digit

            while data[dataIndex] != '"':
                
                value += data[dataIndex]
                dataIndex += 1

        else:
            break

        if int(value) >= 20000000000:    # >= 200.0 QTUM, should be split
            splitFlag = True    

        # print("value", value)

        dataIndex = data.find("blockHeight", dataIndex)

        # print("dataIndex height =", dataIndex)

        if dataIndex > 0:           # found "blockHeight"

            dataIndex +=13  	# point at the first digit

            while data[dataIndex] != ",":
                blockHeight += data[dataIndex]

                dataIndex += 1
                
        else:                   # should not get here
            break

        intsatsSumTotalUTXOs += int(value)

        # print("value =", value)
        
        # do not sum immature or too small UTXOs
        
        if int(blockHeight) <= matureUTXOHeight and int(value) >= minimumSatsValue:    
                intsatsSumValidUTXOs += int(value)
                numValidUTXOs += 1

        else:
            if int(value) < minimumSatsValue:   # too small (immature or mature)
                intsatsSumTooSmallUTXOs += int(value)
                numTooSmallUTXOs += 1
            else:                               # must be large enough but immature
                intsatsSumImmatureUTXOs += int(value)
                numImmatureUTXOs += 1

        dataIndex += 100        # work on this

    splitWarning = ''    

    if splitFlag == True:  # has UTXOs that should be split
        splitWarning = "UTXO(s) >= 200 SHOULD BE SPLIT"

    tempStr = "Super Staker " + address

    if len(splitWarning) > 0:
        pad = "." * (72 - len(tempStr))   # "tab" over to align warning messages vertically
    else:
        pad = ""  
        
    tempStr += pad + splitWarning
        
    print(tempStr)

    print("  Number Valid UTXOs =", numValidUTXOs, "Sum Valid UTXOs =", intsatsSumValidUTXOs / 100000000)

    # these are probably staked
    print("  Number Immature (probably staked) UTXOs =", numImmatureUTXOs, "Sum Immature (probably staked) UTXOs =",\
          intsatsSumImmatureUTXOs / 100000000)

    splitWarning = ''
    
    if intsatsSumTooSmallUTXOs > 10000000000:          # the small UTXOs should be split (recombined)
        splitWarning = "SMALL UTXOs SHOULD SPLIT (RECOMBINED)"

    tempStr = "  Number Too Small UTXOs = " + str(numTooSmallUTXOs) + " Sum Too Small UTXOs = " + str(intsatsSumTooSmallUTXOs / 100000000)

    if len(splitWarning) > 0:
        pad = "." * (72 - len(tempStr))
    else:
        pad = ""
        
    tempStr += pad + splitWarning
                
    print(tempStr)
    print("  Number Total UTXOs =", numTotalUTXOs, "Sum Total UTXOs", intsatsSumTotalUTXOs / 100000000)

    if (intsatsSumImmatureUTXOs + intsatsSumValidUTXOs > 0):
        print("  Percent Stake to Total =", 100 * intsatsSumImmatureUTXOs / (intsatsSumImmatureUTXOs + intsatsSumValidUTXOs), "\n")
    else:
        print("  No valid UTXOs\n")

    # Save number total UTXOs for analysis after getting total delegate weight
    intStakerValidUTXOs = numValidUTXOs + numImmatureUTXOs
    
    return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    

def get_delegate_address_weight(address, height, localStakerMinUTXOSize):

    global headers
    global intsatsDelegatesSumValidUTXOs
    global stakingDelegationsCount          # count of delegations with at least one staking UTXO

    intsatsSumImmatureUTXOs = 0
    intsatsSumTotalUTXOs = 0               # total sum of all delegate UTXOs evaluated

    if isMainnet == True:
        url = APIEndpointMainnet + "address/" + address + "/utxo"
    else:
        url = APIEndpointTestnet + "address/" + address + "/utxo"

    # print("url ", url)

    result = ""            

    try:                
        req = Request(url, headers = headers)
        # open the url
        x = urlRequest.urlopen(req)
        result = x.read()

    except URLError as e:
        print("We failed to reach a server for ", url)
        print("ULR Reason: ", e.reason)

    # print(result)

    data = str(result)
    lenData = len(data)

    # print("lenData", lenData)

    '''
    b'[
    {"transactionId":"e5ec014b5021c2905faebc0774202cc9418331e0b645229ca1cca677e40229c3",
    "outputIndex":1,"scriptPubKey":"21031f48b26481bea513a84573de5f62b4b23d2989a823158e897ce85f755818f04fac",
    "address":"qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","value":"10179000000","isStake":true,
    "blockHeight":358641,"confirmations":274890},

    {"transactionId":"3350acdf13625897f53570b87969c3086b0f2d087fb4c88be7b4fa6d884c54ef",
    "outputIndex":1,"scriptPubKey":"21031f48b26481bea513a84573de5f62b4b23d2989a823158e897ce85f755818f04fac",
    "address":"qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","value":"10967000000","isStake":true,
    "blockHeight":368196,"confirmations":265335},

    <snip>

    '''

    # sys.exit()

    dataIndex = 0

    numTotalUTXOs = 0       # total number of UTXOs evaluated
    numValidUTXOs = 0       # number of UTXOs that are mature and big enough (for delegates) to stake
    numTooSmallUTXOs = 0    # the number of too small UTXOs (immature or mature)
    numImmatureUTXOs = 0    # number of immature UTXOs

    minimumSatsValue = localStakerMinUTXOSize * 100000000
    maturity = 500
    matureUTXOHeight = int(height) - maturity
    intsatsSumTooSmallUTXOs = 0
    intsatsSumValidUTXOs = 0

    foundStakingUTXO = False      # set below if find staking UTXO for this delegate

    while dataIndex < lenData:

        value = ' '
        blockHeight = ' '
            
        dataIndex = data.find("value", dataIndex)

        # print("dataIndex value =", dataIndex)

        if dataIndex > 0:       # found "value"

            numTotalUTXOs += 1

            dataIndex += 8      # point at the first digit

            while data[dataIndex] != '"':
                
                value += data[dataIndex]
                dataIndex += 1

        else:
            break

        # print("value", value)

        dataIndex = data.find("blockHeight", dataIndex)

        # print("dataIndex height =", dataIndex)

        if dataIndex > 0:           # found "blockHeight"

            dataIndex +=13  	# point at the first digit

            while data[dataIndex] != ",":
                blockHeight += data[dataIndex]

                dataIndex += 1
                
        else:                   # should not get here
            break

        intsatsSumTotalUTXOs += int(value)
        
        # do not sum immature or too small UTXOs
        
        if int(blockHeight) <= matureUTXOHeight and int(value) >= minimumSatsValue:    
                intsatsSumValidUTXOs += int(value)
                numValidUTXOs += 1
                foundStakingUTXO = True

        else:
            if int(value) < minimumSatsValue:   # too small (immature or mature)
                intsatsSumTooSmallUTXOs += int(value)
                numTooSmallUTXOs += 1
            else:                               # must be large enough but immature
                intsatsSumImmatureUTXOs += int(value)
                numImmatureUTXOs += 1

        dataIndex += 100        # work on this

    print("  Number Valid UTXOs =", numValidUTXOs, "Sum Valid UTXOs =", intsatsSumValidUTXOs / 100000000)

    print("  Number Immature UTXOs =", numImmatureUTXOs, "Sum Immature UTXOs =", intsatsSumImmatureUTXOs / 100000000)
    
    if intsatsSumTooSmallUTXOs >= stakerMinUTXOSize * 100000000:   # the delegate UTXOs should be split (recombined)
        splitWarning = "SHOULD SPLIT UTXOS"
    else:
        splitWarning = ''

    tempStr = "  Number Too Small UTXOs = " + str(numTooSmallUTXOs) + " Sum Too Small UTXOs = " + str(intsatsSumTooSmallUTXOs / 100000000)

    if len(splitWarning) > 0:
        pad = "." * (72 - len(tempStr))
    else:
        pad = ""
        
    tempStr += pad + splitWarning    

    print(tempStr)
    print("  Number Total UTXOs =", numTotalUTXOs, "Sum Total UTXOs", intsatsSumTotalUTXOs / 100000000, "\n")

    intsatsDelegatesSumValidUTXOs += intsatsSumValidUTXOs

    if foundStakingUTXO == True:            # this delegate has UTXOs being staked
        stakingDelegationsCount += 1

    return

# global variables

# configuration file parameters - - - - - - - - - - - - - - - - - - - - - - - - - -
# these parameters are all set from the configuration file

stakerAddress = ""
stakerFee = -1
stakerMinUTXOSize = -1
isMainnet = False
config_file_name = "SSCConfigurationFile.txt"           # name of configuration file
APIEndpointTestnet = "https://testnet.qtum.info/api/"   # for testnet
APIEndpointMainnet = "https://qtum.info/api/"           # for mainnet
APIEndpointThisChain = ''                               # for the chain we are on
# MinimumUTXOValue = 100                                # minimum UTXO size from super staker
intsatsSumTotalUTXOs = 0                                # sum of all the UTXOs
intsatsSumValidUTXOs = 0                                # for staker
intStakerValidUTXOs = 0                                 # for staker, mature + immature
intsatsDelegatesSumValidUTXOs = 0                       # for delegates, mature + immature ???
stakingDelegationsCount = 0                             # the count of delegates with at least one staking UTXO

# for API calls pretend to be a chrome 87 browser on a windows 10 machine
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"}

data = ""                                               # data read from API calls
    
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# MAIN PROGRAM STARTS HERE  = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def main():
                            
    print("SuperStakerCheckup", version, "\n")
    
    start = timer()

    # configuration file parameters - - - - - - - - - - - - - - - - - - - - - - - - - -
    # these parameters are all set from the configuration file

    '''
    stakerAddress = ""
    stakerFee = -1
    stakerMinUTXOSize = -1
    isMainnet = False
    '''

    read_config_file(config_file_name)   # read configuration file parameters

    # for API calls pretend to be a chrome 87 browser on a windows 10 machine
                                  
    # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"}

    if isMainnet:
        APIEndpointThisChain = APIEndpointMainnet
    else:
        APIEndpointThisChain = APIEndpointTestnet

    # get the current blockheight

    url = APIEndpointThisChain + "info"    
       
    try:                
        req = Request(url, headers = headers)
        # open the url
        x = urlRequest.urlopen(req)
        result = x.read()

    except URLError as e:
        print("We failed to reach a server for ", url)
        print("ULR Reason: ", e.reason)

    # print(result)

    data = str(result)

    '''
    b'{"height":760992,
    "supply":103023968,
    "circulatingSupply":103023968,
    "blockTime":1609008176,
    "difficulty":4371001.580485245,
    "stakeWeight":2151586138402970,
    "fullnodes":1158,
    "feeRate":0.00440734,
    "dgpInfo":{"maxBlockSize":2000000,"minGasPrice":40,"blockGasLimit":40000000},
    "addresses":2071441,
    "netStakeWeight":2151586138402970}'
    '''

    height = ""
    lenData = len(data)

    dataIndex = data.find("height", 0, lenData)

    if dataIndex > 0:       # found "height"

        dataIndex += 8      # point at the first digit

        while data[dataIndex] != ',':
            
            height += data[dataIndex]
            dataIndex += 1

    # note, leave height as string        

    temp = ""

    if isMainnet == True:
        temp += "Mainnet height "

    else:
        temp += "Testnet height "

    temp += height + "\n"

    print(temp)

    get_staker_address_weight(stakerAddress, height)

    # analyze UTXOs for delegates, get delegate addresses

    url = APIEndpointThisChain + "address/" + stakerAddress

    # print("url ", url)

    try:                
        req = Request(url, headers = headers)
        x = urlRequest.urlopen(req)
        result = x.read()

    except URLError as e:
            print("We failed to reach a server for ", url)
            print("ULR Reason: ", e.reason)

    data = str(result)
    lenData = len(data)

    # print("lenData", lenData)
    # print(result)

    '''
    b'{"balance":"1824098919765","totalReceived":"1824220837752","totalSent":"121917987","unconfirmed":"0",
    "staking":"175219168342","mature":"1648879751423","qrc20Balances":[],"qrc721Balances":[],"ranking":95,
    "transactionCount":6678,"blocksMined":6613,
    "delegations":[
    {"delegator":"qKdVVUt1sRiBSpNRXMrbgTr8j8sZDv9pc9","fee":10},
    {"delegator":"qMbS62scKpLkfr1i4o52ypEP1RwoKNiKPV","fee":10},
    <snip>
    {"delegator":"qesrgJUvUKJdqk1XGsYmXyCP3XsQ3Ec14N","fee":10}]}'
    '''

    dataIndex = data.find("delegator", 0, lenData)

    if dataIndex > 0:   # found first delegate

        while True:

            dataIndex += 12         # first character of delegate address
            delegateAddress = ''

            for i in range(34):
                delegateAddress += data[dataIndex + i]

            # print("delegateAddress =", delegateAddress)

            dataIndex += i

            temp = ""

            dataIndex = data.find("fee", dataIndex, lenData)

            if dataIndex > 0:       # found the fee

                dataIndex += 5

                for i in range(3):
                    if data[dataIndex + i] >= "0" and data[dataIndex + i] <= "9":
                        temp += data[dataIndex + i]
                    else:
                        break

                delegateFee = int(temp)

            if (delegateFee >= stakerFee):
                if delegateFee == stakerFee:
                    print("Delegate", delegateAddress, "Fee", delegateFee)
                else:
                    tempStr = "Delegate" + str(delegateAddress) + " Fee " + str(delegateFee)
                    pad = "." * (72 - len(tempStr))        
                    tempStr += pad + "FEE TOO HIGH"    
                    print(tempStr)
                    
                get_delegate_address_weight(delegateAddress, height, stakerMinUTXOSize)

            else:
                tempStr = "Delegate" + str(delegateAddress) + " Fee " + str(delegateFee)
                pad = "." * (72 - len(tempStr))
                tempStr += pad + "FEE TOO LOW, NOT STAKED" + "\n"
                print(tempStr)
                
            dataIndex += i

            dataIndex = data.find("delegator", dataIndex, lenData)

            if dataIndex < 0:   # no more delegates to find
                break
            
        print("Number of valid Staker UTXOs (mature + immature)", intStakerValidUTXOs)
        print("Number of delegates being staked", stakingDelegationsCount)      # have valid UTXO(s)
        print("Delegates weight", intsatsDelegatesSumValidUTXOs / 100000000, "\n")

    else:
        print("This staker address has no delegations", "\n")

    print("Duration:", format(timer() - start, "0.2f"), "seconds")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -    

if __name__ == '__main__':
    main()


    

