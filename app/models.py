from django.db import models
from django.conf import settings
from django.db import models

#Itemモデル（タイトル、値段、カテゴリー、スラッグ、説明、画像）
class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.IntegerField()
    category = models.CharField(max_length=100)
    #スラッグは文字、ハイフン、数字、アンダースコアだけを含んだ文字列
    #スラッグを使用すると、商品ごとに割り当てたURLを使用することができる
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(upload_to='images')

    def __str__(self):
        return self.title

class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    #get_total_item_price関数を作ることにより、注文アイテムの金額を取得することができる
    #モデルで設定しておくと、テンプレートで容易に取得することができます。
    def get_total_item_price(self):
        return self.quantity * self.item.price

    def __str__(self):
        return f"{self.item.title}:{self.quantity}"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    #注文が完了すると、orderedが True になる。
    ordered = models.BooleanField(default=False)

    #get_total関数を作ることにより、注文の合計金額を取得することができる
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_item_price()
        return total

    def __str__(self):
        return self.user.email

#Orderモデルに関連付け
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email