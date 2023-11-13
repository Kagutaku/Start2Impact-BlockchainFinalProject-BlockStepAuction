from django.db import models
from django.contrib.auth.models import User
import json
from web3 import Web3
import hashlib


class Bidder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=5000)
    pendingBalance = models.IntegerField(default=0)
    totalBids = models.IntegerField(default=0)
    totalAuctionsWon = models.IntegerField(default=0)


class Auction(models.Model):
    title = models.CharField(max_length=80)
    status = models.CharField(max_length=6, choices=[
        ('open', 'open'),
        ('closed', 'closed')
    ], default='open')
    startingPrice = models.IntegerField(default=0)
    currentPrice = models.IntegerField(default=0)
    durationDays = models.IntegerField(default=0)
    creationDate = models.DateTimeField(default=None, blank=True, null=True)
    endDate = models.DateTimeField(default=None, blank=True, null=True)
    timeleft = models.CharField(default=None, blank=True, null=True, max_length=100)
    totalBids = models.IntegerField(default=0)
    highestBidder = models.ForeignKey(Bidder, on_delete=models.CASCADE, default=None, null=True)
    highestUser = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)
    onchainTxHash = models.CharField(default=None, blank=True, null=True, max_length=100)
    jsonReportHash = models.CharField(default=None, blank=True, null=True, max_length=100)

    # function to create closed auction json report and its hash
    def createJsonReport(self):
        if self.status == 'closed':
            creationDate = self.creationDate.strftime("%m/%d/%Y, %H:%M:%S")
            endDate = self.endDate.strftime("%m/%d/%Y, %H:%M:%S")
            report = {
                'auctionId': self.pk,
                'title': self.title,
                'startingPrice': self.startingPrice,
                'closingPrice': self.currentPrice,
                'winner': str(self.highestUser),
                'creationDate': creationDate,
                'endDate': endDate,
                'totalBids': self.totalBids,
            }
            jsonReport = json.dumps(report, indent=4)
            reportHash = hashlib.sha256(jsonReport.encode()).hexdigest()
            self.jsonReportHash = reportHash
            self.save()
            return True
        else:
            return False

    # function to send on chain tx with json report hash
    def sendOnchainTx(self):
        if self.jsonReportHash is not None:
            w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/17cfb4b3e3cb48399d9584f948071dda'))
            privKey = '0xa97816c13c7c15b8e11a6783e8281a6a49d501b1ad4a1d831444ca2666f273a2'
            pubKey = Web3.to_checksum_address('0x73Efc26C0910Ea25005e2EEf09ADe963de75aef9')
            nonce = w3.eth.get_transaction_count(pubKey)
            gasPrice = w3.to_wei(50, 'gwei')
            value = w3.to_wei(0, 'ether')
            message = self.jsonReportHash.encode('utf-8')
            signedTx = w3.eth.account.sign_transaction(dict(
                nonce=nonce,
                gasPrice=gasPrice,
                gas=100000,
                to='0x0000000000000000000000000000000000000000',
                value=value,
                data=message
            ), privKey)
            tx = w3.eth.send_raw_transaction(signedTx.rawTransaction)
            txId = w3.to_hex(tx)
            self.onchainTxHash = txId
            self.save()
            return True
        else:
            return False
