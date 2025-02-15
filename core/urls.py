from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, PasswordResetView, ProfileView,
    ProductViewSet, ProductImageViewSet, CategoryViewSet, TransactionViewSet,
    ReportViewSet, MessageViewSet, AdminUserViewSet, AdminProductViewSet,
    ConversationViewSet,  # Correct viewset registration for conversations
    AdminReportViewSet, CartItemViewSet, CheckoutView, OrderViewSet,EmptyCartView,CustomTokenRefreshView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='productimage')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'cart-items', CartItemViewSet, basename='cartitem')
router.register(r'orders', OrderViewSet, basename='order')

# Admin endpoints (accessible only by admins)
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'admin/products', AdminProductViewSet, basename='admin-product')
router.register(r'admin/reports', AdminReportViewSet, basename='admin-report')

urlpatterns = [
    # Authentication & Profile endpoints
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/password-reset', PasswordResetView.as_view(), name='password_reset'),
    path('auth/profile', ProfileView.as_view(), name='profile'),
    path('auth/checkout', CheckoutView.as_view(), name='checkout'),
    path('auth/cart/empty', EmptyCartView.as_view(), name='empty_cart'),
    path('auth/token/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # All other endpoints via the router
    path('', include(router.urls)),
]
