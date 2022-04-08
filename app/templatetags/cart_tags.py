from django import template
from app.models import Order

register = template.Library()

@register.filter
def itemCount(user):
  #ログインしてるかどうかの判断
    if user.is_authenticated:
      #注文完了していない注文をすべて取得。
        order = Order.objects.filter(user=user, ordered=False)
        if order.exists():
          #最新の注文を取得して、数量をカウント
            return order[0].items.count()
    return 0