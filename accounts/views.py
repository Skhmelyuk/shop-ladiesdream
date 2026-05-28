from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from orders.models import Order
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile

class ProfileView(LoginRequiredMixin, View):
    """
    Відображає та редагує основну сторінку профілю користувача.
    """
    template_name = 'accounts/profile.html'

    def get(self, request):
        u_form = UserUpdateForm(instance=request.user)
        profile, created = Profile.objects.get_or_create(user=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        context = {
            'u_form': u_form,
            'p_form': p_form,
            'active_tab': 'profile',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        u_form = UserUpdateForm(request.POST, instance=request.user)
        profile, created = Profile.objects.get_or_create(user=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Ваш профіль було успішно оновлено!')
            return redirect('accounts:profile')
        
        context = {
            'u_form': u_form,
            'p_form': p_form,
            'active_tab': 'profile',
        }
        return render(request, self.template_name, context)

class OrderHistoryView(LoginRequiredMixin, ListView):
    """
    Відображає список усіх замовлень, зроблених поточним авторизованим користувачем.
    """
    model = Order
    template_name = 'accounts/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'orders'
        return context