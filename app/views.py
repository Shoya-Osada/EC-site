from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from .models import Item, OrderItem, Order, Payment
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import CustomUser
from django.conf import settings
import stripe


class IndexView(LoginRequiredMixin, TemplateView):
    #固定ページ
    template_name = "app/index.html"
    login_url = '/accounts/login/'

class IndexView(View):
    def get(self, request, *args, **kwargs):
        #item_dataにItemのすべてを取得して入れる
        item_data = Item.objects.all()
        return render(request, 'app/index.html', {
            'item_data': item_data
        })

#詳細画面のビュー
class ItemDetailView(View):
    def get(self, request, *args, **kwargs):
        item_data = Item.objects.get(slug=self.kwargs['slug'])
        return render(request, 'app/product.html', {
            'item_data': item_data
        })

#LoginRequiredMixinクラスを継承することにより、ログインユーザーのみショッピングカートが表示。
class OrderView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            context = {
                'order': order
            }
            return render(request, 'app/order.html', context)
        #注文がない場合に、ショッピングカート画面を表示したときの動作。
        except ObjectDoesNotExist:
            return render(request, 'app/order.html')

class PaymentView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        #ユーザー情報を表示したいので、CustomUserモデルから情報を取得
        user_data = CustomUser.objects.get(id=request.user.id)
        context = {
            'order': order,
            'user_data': user_data
        }
        return render(request, 'app/payment.html', context)

    def post(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        order_items = order.items.all()
        amount = order.get_total()

        #Paymentモデルに、stripe の id と合計金額を保存。
        payment = Payment(user=request.user)
        #仮のID
        payment.stripe_charge_id = 'test_stripe_charge_id'
        payment.amount = amount
        payment.save()

        order_items.update(ordered=True)
        for item in order_items:
            item.save()

        #注文が確定したら、orderedを True にして注文が確定されたフラグを立てる。
        order.ordered = True
        order.payment = payment
        order.save()
        return redirect('thanks')

class ThanksView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'app/thanks.html')

@login_required
def addItem(request, slug):
    #get_object_or_404関数は、指定したモデルを取得し、モデルが存在しない場合は Http404 を送出する。
    item = get_object_or_404(Item, slug=slug)

    #get_or_createメソッドは、データベースが存在する場合はデータを取得
    #データベースが存在しない場合は、データを登録。
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    #filter を使用してデータをリストで取得
    order = Order.objects.filter(user=request.user, ordered=False)

    if order.exists():
        #[0]を使用して、リストの最初を取得することにより、最新の注文を取得。
        order = order[0]
        #すでに商品がある場合は、数量をプラスして、商品がない場合は、新たに追加
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
        else:
            order.items.add(order_item)
    else:
        order = Order.objects.create(user=request.user, ordered_date=timezone.now())
        order.items.add(order_item)

    return redirect('order')

#決済システムクラス
class PaymentView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        user_data = CustomUser.objects.get(id=request.user.id)
        context = {
            'order': order,
            'user_data': user_data
        }
        return render(request, 'app/payment.html', context)

    def post(self, request, *args, **kwargs):
        #本番運用するためには、Stripe にユーザー情報を渡す必要アリ。
        #今回は、合計金額と商品説明のみ Stripe に渡す。
        stripe.api_key = settings.STRIPE_SECRET_KEY
        order = Order.objects.get(user=request.user, ordered=False)
        token = request.POST.get('stripeToken')
        amount = order.get_total()
        order_items = order.items.all()
        item_list = []
        for order_item in order_items:
            item_list.append(str(order_item.item) + ':' + str(order_item.quantity))
        description = ' '.join(item_list)

        charge = stripe.Charge.create(
            amount=amount,
            currency='jpy',
            description=description,
            source=token,
        )

        payment = Payment(user=request.user)
        payment.stripe_charge_id = charge['id']

        payment.amount = amount
        payment.save()

        order_items.update(ordered=True)
        for item in order_items:
            item.save()

        order.ordered = True
        order.payment = payment
        order.save()
        return redirect('thanks')

@login_required
def removeItem(request, slug):
    #[0]でリストの最初を取得することにより、最新の注文を取得
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    #最新の注文でslugで検索をして、ヒットした最新の注文アイテムを削除
    if order.exists():
        order = order[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            return redirect("order")

    return redirect("product", slug=slug)

@login_required
def removeSingleItem(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order.exists():
        order = order[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            #商品が 1 つ以上であれば、数量を 1 つ減らす。
            #もし商品が 1 つであれば、商品を削除する。
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order_item.delete()
            return redirect("order")

    return redirect("product", slug=slug)