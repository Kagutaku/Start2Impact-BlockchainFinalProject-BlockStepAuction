from datetime import datetime, timedelta
import redis
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import render, redirect
from .forms import CreateUserForm, CreateAuctionForm
from .models import Bidder, Auction
from .utils import updateAuctionTimeAndStatus, userLoginRequired, adminLoginRequired, getUserBids

# redis DB setup
myRedis = redis.Redis(
    host='redis-18815.c240.us-east-1-3.ec2.cloud.redislabs.com',
    port=18815,
    password='ZKCmfNpN2bZToP5sJal0eFgg3BHkRSRR')


def homePage(request):
    return render(request, 'blockstepauction/index.html')


def registerPage(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            bidder = Bidder(user=user)
            bidder.save()
            return redirect('loginPage')
    else:
        form = CreateUserForm
        return render(request, 'blockstepauction/Authentication/register.html', {'form': form})


def loginPage(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profilePage')
    return render(request, 'blockstepauction/Authentication/login.html')


@userLoginRequired
def logoutPage(request):
    logout(request)
    return redirect('loginPage')


@userLoginRequired
def profilePage(request):
    return render(request, 'blockstepauction/Authentication/profile.html')


@userLoginRequired
def dashboardPage(request):
    user = request.user
    bidder = Bidder.objects.get(user=user)
    context = {
        "bidder": bidder
    }
    return render(request, 'blockstepauction/UserActions/dashboard.html', context)


@adminLoginRequired
def newAuctionPage(request):
    if request.method == "POST":
        form = CreateAuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            if auction.durationDays < 101:
                auction.currentPrice = auction.startingPrice
                auction.creationDate = datetime.now()
                auction.endDate = auction.creationDate + timedelta(days=auction.durationDays)
                auction.save()
                return redirect('openAuctionsPage')
            else:
                return redirect('newAuctionPage')
    else:
        form = CreateAuctionForm()
        return render(request, 'blockstepauction/AdminActions/newAuction.html', {'form': form})


@userLoginRequired
def openAuctionsPage(request):
    openAuctions = Auction.objects.filter(status='open')
    updateAuctionTimeAndStatus(openAuctions)
    openAuctions = Auction.objects.filter(status='open')
    context = {
        "openAuctions": openAuctions,
    }
    return render(request, 'blockstepauction/UserActions/openAuctions.html', context)


@userLoginRequired
def closedAuctionsPage(request):
    closedAuctions = Auction.objects.filter(status='closed')
    context = {
        "closedAuctions": closedAuctions,
    }
    return render(request, 'blockstepauction/UserActions/closedAuctions.html', context)


@userLoginRequired
def newBidPage(request):
    # open auctions update
    openAuctions = Auction.objects.filter(status='open')
    updateAuctionTimeAndStatus(openAuctions)
    # get current user and bidder and open auctions he can bid
    user = request.user
    bidder = Bidder.objects.get(user=user)
    openAuctionsToBid = Auction.objects.filter(
        Q(status='open') & ~Q(highestUser=user) & ~Q(highestBidder=bidder))
    if request.method == "POST":
        # handle auction and bid
        auctionId = request.POST.get('auction')
        bid = int(request.POST.get('bid'))
        auction = Auction.objects.get(id=auctionId)
        if bid > auction.currentPrice:
            bidderBudget = bidder.balance - bidder.pendingBalance
            if bid <= bidderBudget:
                # update auction current price
                priceBefore = auction.currentPrice
                auction.currentPrice = bid
                raising = bid - priceBefore
                # set new bid creation date
                now = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                # update auction total bids number
                auction.totalBids = auction.totalBids + 1
                stringUser = str(user)
                # set hash key with auction and bid id
                key = f"auction:{auctionId}:bid:{auction.totalBids}:user:{user}"
                # create a hash for the bid on redis DB
                newBid = myRedis.hset(
                    key,
                    mapping={
                        "auctionId": auctionId,
                        "datetime": now,
                        "priceBefore": priceBefore,
                        "raising": raising,
                        "priceAfter": auction.currentPrice,
                        "user": stringUser,
                        "bidNumber": auction.totalBids,
                    },
                )
                # update last highest bidder balance
                lastHighestBidder = auction.highestBidder
                if lastHighestBidder is not None:
                    lastHighestBidder.pendingBalance = lastHighestBidder.pendingBalance - priceBefore
                    lastHighestBidder.save()
                # update highest bidder
                auction.highestBidder = bidder
                auction.highestUser = user
                auction.save()
                # bidder balance update
                bidder.totalBids = bidder.totalBids + 1
                bidder.pendingBalance = bidder.pendingBalance + bid
                # bidder save
                bidder.save()
                return redirect('openAuctionsPage')
            else:
                return redirect('newBidPage')
        else:
            return redirect('newBidPage')
    else:
        context = {
            "openAuctionsToBid": openAuctionsToBid,
        }
        return render(request, 'blockstepauction/UserActions/newBid.html', context)


@userLoginRequired
def myBidsPage(request):
    user = str(request.user)
    bids = getUserBids(user)
    context = {
        "bids": bids
    }
    return render(request, 'blockstepauction/UserActions/myBids.html', context)


@userLoginRequired
def wonAuctionsPage(request):
    user = request.user
    bidder = Bidder.objects.get(user=user)
    wonAuctions = Auction.objects.filter(
        Q(status='closed') & Q(highestUser=user) & Q(highestBidder=bidder))
    context = {
        "wonAuctions": wonAuctions,
        "bidder": bidder,
    }
    return render(request, 'blockstepauction/UserActions/wonAuctions.html', context)
