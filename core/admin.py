from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Category, Product, ProductImage, Transaction, Report,
    Conversation, Message, Cart, CartItem, Order, OrderItem
)

# Custom UserAdmin for our custom User model.
class CustomUserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_active', 'balance', 'created_at')
    list_filter = ('role', 'is_active',)
    search_fields = ('username', 'email')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('profile_picture_url', 'contact_details')}),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Financial', {'fields': ('balance',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'balance', 'is_active', 'is_staff'),
        }),
    )

# Register the custom User model with the custom admin.
admin.site.register(User, CustomUserAdmin)

# Register remaining models with default ModelAdmin.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'description', 'created_at')
    search_fields = ('category_name',)
    ordering = ('category_name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'price', 'condition', 'is_active', 'is_sold', 'listing_date')
    list_filter = ('condition', 'is_active', 'is_sold', 'category')
    search_fields = ('title', 'description', 'seller__username')
    ordering = ('-listing_date',)
    
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'caption', 'order', 'created_at')
    list_filter = ('order',)
    ordering = ('order',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'product', 'buyer', 'seller', 'amount', 'transaction_status', 'transaction_date')
    list_filter = ('transaction_status', 'payment_method')
    search_fields = ('product__title', 'buyer__username', 'seller__username')
    ordering = ('-transaction_date',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'reporter', 'reason', 'status', 'report_date')
    list_filter = ('status',)
    search_fields = ('reporter__username', 'reason')
    ordering = ('-report_date',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__title',)
    ordering = ('-created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'sender', 'conversation', 'sent_timestamp')
    list_filter = ('sent_timestamp', 'read_status')
    search_fields = ('sender__username', 'conversation__id')
    ordering = ('sent_timestamp',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'added_at')
    search_fields = ('cart__user__username', 'product__title')
    ordering = ('-added_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username',)
    ordering = ('-created_at',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__title')
    ordering = ('id',)
