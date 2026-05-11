from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from main.models import Category
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from orders.models import Order
from orders.models import OrderItem
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm




@login_required
def profile_view(request):
    """
    Відображає та редагує основну сторінку профілю користувача.
    """
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Ваш профіль було успішно оновлено!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'active_tab': 'profile',
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def order_history_view(request):
    """
    Відображає список усіх замовлень, зроблених поточним авторизованим користувачем.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created')
    context = {
        'orders': orders,
        'active_tab': 'orders',
    }
    
    return render(request, 'accounts/order_history.html', context)
