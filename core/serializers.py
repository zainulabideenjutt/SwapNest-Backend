from rest_framework import serializers
from .models import (
    User,
    Category,
    Product,
    ProductImage,
    Transaction,
    Report,
    Conversation,
    Message,
    Cart,
    CartItem,
    Order,
    OrderItem
)

# ---------------------------------------------------
# ProductImage Serializer
# ---------------------------------------------------
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'caption', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_order(self, value):
        if value < 0:
            raise serializers.ValidationError("Order must be a non-negative integer.")
        return value


# ---------------------------------------------------
# Product Serializer
# ---------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    seller = serializers.StringRelatedField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source='category'
    )
    category_name = serializers.CharField(source='category.name', read_only=True)
    bought_by = serializers.StringRelatedField(read_only=True)
    # Add this field to accept base64 images during creation
    base64_images = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'title', 'description', 'price',
            'condition', 'location', 'category_id', 'category_name',
            'is_active', 'is_sold', 'bought_by', 'created_at', 'updated_at', 
            'images', 'base64_images'  # Add base64_images to fields
        ]
        read_only_fields = ['id', 'seller', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


# ---------------------------------------------------
# Report Serializer
# ---------------------------------------------------
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reported_product', 'reported_user',
            'reason', 'description', 'created_at', 'status',
            'reviewed_by', 'reviewed_at'
        ]
        read_only_fields = ['id', 'reporter', 'created_at']

    def validate(self, data):
        # Ensure that at least one of reported_product or reported_user is provided.
        if not data.get('reported_product') and not data.get('reported_user'):
            raise serializers.ValidationError("You must report either a product or a user.")
        return data


# ---------------------------------------------------
# User Serializer
# ---------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    listings = ProductSerializer(many=True, read_only=True, source='products')
    purchased_products = ProductSerializer(many=True, read_only=True)
    reports = ReportSerializer(many=True, read_only=True)  # Reports filed by the user

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'profile_picture_url', 'contact_details', 'role', 'balance',
            'is_active', 'created_at', 'updated_at',
            'listings', 'purchased_products', 'reports'
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at', 'listings', 'purchased_products', 'reports']

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', 'User')
        if role == 'Admin':
            user = User.objects.create_superuser(password=password, **validated_data)
        else:
            user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ---------------------------------------------------
# Category Serializer
# ---------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ---------------------------------------------------
# Transaction Serializer
# ---------------------------------------------------
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'product', 'buyer', 'seller',
            'payment_method', 'amount',
            'transaction_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be greater than zero.")
        return value


# ---------------------------------------------------
# Conversation Serializer
# ---------------------------------------------------
class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    messages = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'product', 'participants', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at', 'participants', 'messages']


# ---------------------------------------------------
# Message Serializer
# ---------------------------------------------------
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'created_at', 'read_status']
        read_only_fields = ['id', 'sender', 'created_at', 'read_status']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value


# ---------------------------------------------------
# CartItem Serializer
# ---------------------------------------------------
class CartItemSerializer(serializers.ModelSerializer):
    # For output: nested full product representation.
    product = ProductSerializer(read_only=True)
    # For input: accept product's UUID as primary key.
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source='product'
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'created_at']
        read_only_fields = ['id', 'product', 'created_at']

    def validate_product(self, value):
        if value.is_sold:
            raise serializers.ValidationError("Cannot add a sold product to the cart.")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


# ---------------------------------------------------
# Cart Serializer
# ---------------------------------------------------
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'items', 'created_at', 'updated_at']


# ---------------------------------------------------
# OrderItem Serializer
# ---------------------------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # Nested full product details

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


# ---------------------------------------------------
# Order Serializer
# ---------------------------------------------------
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'user', 'status', 'total', 'created_at', 'updated_at', 'items']
