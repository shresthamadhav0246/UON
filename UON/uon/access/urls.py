from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login_page'),
    path('checkSim/', views.checkSim, name='checkSim_page'),
    path('register/', views.register, name='register_page'),
    #path('addPatient/', views.addPatient, name='addPatient_page'),
]
