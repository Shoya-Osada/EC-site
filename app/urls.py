from django.urls import path
from app import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),#商品リストをトップページに表示
    #slugを URL をとして使用
    path('product/<slug>', views.ItemDetailView.as_view(), name='product'),
    path('additem/<slug>', views.addItem, name='additem'),
    path('order/', views.OrderView.as_view(), name='order'),#ショッピングカートの URL
    path('removeitem/<slug>', views.removeItem, name='removeitem'),#削除処理の URL 
    path('removesingleitem/<slug>', views.removeSingleItem, name='removesingleitem'),#商品減量のURL
    path('payment/', views.PaymentView.as_view(), name='payment'),#注文確定画面の URL
    path('thanks/', views.ThanksView.as_view(), name='thanks'),#注文が完了したときの URL
]