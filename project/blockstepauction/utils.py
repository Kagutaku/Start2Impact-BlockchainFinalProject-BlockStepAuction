from pytz import timezone
from django.utils import timezone as djtimezone
from datetime import datetime
from string import Template
import redis
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# redis DB setup
myRedis = redis.Redis(
    host='redis-18815.c240.us-east-1-3.ec2.cloud.redislabs.com',
    port=18815,
    password='ZKCmfNpN2bZToP5sJal0eFgg3BHkRSRR')


class DeltaTemplate(Template):
    delimiter = "%"


# function to format time left to auction end date
def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    d["H"], rem = divmod(tdelta.seconds, 3600)
    d["M"], d["S"] = divmod(rem, 60)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


# function to check auction status and update time left to end
def updateAuctionTimeAndStatus(auctions):
    now = datetime.now(timezone('Europe/Rome'))
    for auction in auctions:
        if auction.endDate < now:
            if auction.status == "open":
                auction.status = "closed"
                # highest bidder balance update
                winner = auction.highestBidder
                winner.pendingBalance = winner.pendingBalance - auction.currentPrice
                winner.balance = winner.balance - auction.currentPrice
                winner.totalAuctionsWon = winner.totalAuctionsWon + 1
                winner.save()
                # auction create report and send onchain tx
                auction.createJsonReport()
                auction.sendOnchainTx()
                auction.save()
        else:
            timeleft = auction.endDate - djtimezone.now()
            timeleft = strfdelta(timeleft, "%D days, %H hours and %M minutes")
            auction.timeleft = timeleft
            auction.save()


# custom decorator to assure only logged users can access the page
def userLoginRequired(view_func):
    decorated_view_func = login_required(view_func)

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('homePage')
        else:
            return decorated_view_func(request, *args, **kwargs)

    return wrapper


# custom decorator to assure only logged admin users can access the page
def adminLoginRequired(view_func):
    decorated_view_func = login_required(view_func)

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return decorated_view_func(request, *args, **kwargs)
        else:
            return redirect('homePage')

    return wrapper


# function to get all bids of passed user
def getUserBids(my_user):
    bids = []
    bidCounter = 1
    for key in myRedis.scan_iter("auction:*"):
        bid = myRedis.hgetall(key)
        user = bid.get(b"user").decode('utf-8')
        if user == my_user:
            auctionId = bid.get(b"auctionId").decode('utf-8')
            date = bid.get(b"datetime").decode('utf-8')
            priceBefore = bid.get(b"priceBefore").decode('utf-8')
            raising = bid.get(b"raising").decode('utf-8')
            priceAfter = bid.get(b"priceAfter").decode('utf-8')
            bidNumber = bid.get(b"bidNumber").decode('utf-8')
            bids.append({
                'auctionId': auctionId,
                'datetime': date,
                'priceBefore': priceBefore,
                'raising': raising,
                'priceAfter': priceAfter,
                'bidNumber': bidNumber,
                'bidCounter': bidCounter,
            })
            bidCounter = bidCounter + 1
    return bids
