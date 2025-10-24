from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.verify, name='verify'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('detail/', views.detail, name='detail'),
    path('feature/', views.feature, name='feature'),
    path('price/', views.price, name='price'),
    path('quote/', views.quote, name='quote'),
    path('service/', views.service, name='service'),
    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('LogOut/', views.LogOut, name='LogOut'),
    path('reset_profile/', views.reset_profile, name='reset_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('crypto/', views.crypto, name='crypto'),
    path('paypal/', views.paypal, name='paypal'),
    path('linking_view/', views.linking_view, name='linking_view'),
    path('profile/', views.profile, name='profile'),
    path('Upgrade_Account/', views.Upgrade_Account, name='Upgrade_Account'),
    path('tac/', views.tac, name='tac'),
    path('vat/', views.vat, name='vat'),
    path('imf/', views.imf, name='imf'),
    path('pending/', views.pending, name='pending'),
    path('bank_transfer/', views.bank_transfer, name='bank_transfer'),
]
