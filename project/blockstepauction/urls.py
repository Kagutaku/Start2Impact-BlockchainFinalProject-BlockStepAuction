from django.urls import path
from . import views

urlpatterns = [
    # homepage
    path('', views.homePage, name='homePage'),
    # authentication
    path('login/', views.loginPage, name='loginPage'),
    path('logout/', views.logoutPage, name='logoutPage'),
    path('register/', views.registerPage, name='registerPage'),
    path('profile/', views.profilePage, name='profilePage'),
    # user actions
    path('dashboard/', views.dashboardPage, name='dashboardPage'),
    path('open-auctions/', views.openAuctionsPage, name='openAuctionsPage'),
    path('closed-auctions/', views.closedAuctionsPage, name='closedAuctionsPage'),
    path('new-bid/', views.newBidPage, name='newBidPage'),
    path('my-bids/', views.myBidsPage, name='myBidsPage'),
    path('auctions-won/', views.wonAuctionsPage, name='wonAuctionsPage'),
    # admin actions
    path('new-auction/', views.newAuctionPage, name='newAuctionPage'),
]
