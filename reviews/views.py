from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Review, ReviewReply
from .forms import ReviewForm
from main.models import Product

class ReviewView(LoginRequiredMixin, View):
    login_url = 'account_login'
    redirect_field_name = 'next'

    def get(self, request, product_pk):
        product = get_object_or_404(Product, pk=product_pk)
        form = ReviewForm()
        return render(request, 'reviews/add_review.html', {'product': product, 'form': form})

    def post(self, request, product_pk):
        product = get_object_or_404(Product, pk=product_pk)
        if Review.objects.filter(product=product, author=request.user).exists():
            messages.error(request, "Ви вже залишали відгук для цього товару 💗")
            return redirect('main:product-detail', id=product.id, slug=product.slug)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.author = request.user
            review.product = product
            review.save()
            messages.success(request, '✅ Ваш відгук успішно додано та очікує на модерацію.')
            return redirect('main:product-detail', id=product.id, slug=product.slug)
        return render(request, 'reviews/add_review.html', {'product': product, 'form': form})


class AddReplyView(LoginRequiredMixin, View):
    login_url = 'account_login'
    redirect_field_name = 'next'

    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Тільки адміністратори можуть відповідати на відгуки'}, status=403)

        parent_review_id = request.POST.get('parent_review_id')
        content = request.POST.get('content', '').strip()

        if not parent_review_id or not content:
            return JsonResponse({'success': False, 'error': 'Текст відповіді є обов\'язковим'})

        try:
            parent_review = get_object_or_404(Review, pk=parent_review_id)

            ReviewReply.objects.create(
                review=parent_review,
                author=request.user,
                content=content,
                is_active=True
            )

            return JsonResponse({'success': True, 'message': '✅ Відповідь успішно додано!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
