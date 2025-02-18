from django.contrib.auth import authenticate
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from .models import (
    User, Category, Product, ProductImage,
    Transaction, Report, Conversation, Message,
    Cart, CartItem, Order, OrderItem
)
from .serializers import (
    UserSerializer, CategorySerializer, ProductSerializer,
    ProductImageSerializer, TransactionSerializer, ReportSerializer,
    ConversationSerializer, MessageSerializer,
    CartItemSerializer, CartSerializer, OrderSerializer
)

# ---------------------------------------------------
# Authentication Related Views
# ---------------------------------------------------
class RegisterView(generics.CreateAPIView):
    """
    Allow new users to register.
    
    This view handles user registration by creating new user accounts.
    It uses the UserSerializer to validate and create user records.
    """
    permission_classes = []
    serializer_class = UserSerializer


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs) -> Response:
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            request.data['refresh'] = refresh_token
            response = super().post(request, *args, **kwargs)
            tokens = response.data
            access_token = tokens['access']
            refresh_token = tokens['refresh']

            res = Response()
            res.data = {'refreshed': True}
            res.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True,
                samesite='None',
                path='/'
            )
            res.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite='None',
                path='/'
            )
            res.data.update({'access_token': access_token, 'refresh_token': refresh_token})
            return res
        except Exception as e:
            return Response({'refreshed': False, "error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class LoginView(APIView):
    """
    Authenticate user credentials and issue JWT tokens.
    
    Endpoints:
    - POST: Accepts email and password, returns JWT tokens if valid.
    - Sets httponly cookie with access token for enhanced security.
    """
    permission_classes = []
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response(
                {"error": "Bad Request", "detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = authenticate(email=email, password=password)
        if user is None:
            return Response(
                {"error": "Authentication Failed", "detail": "Incorrect email or password. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_active:
            return Response(
                {"error": "Account Inactive", "detail": "Your account is currently inactive. Please contact support."},
                status=status.HTTP_403_FORBIDDEN
            )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        response = Response({
            "detail": "Login successful.",
            "access_token": access_token,
            "refresh_token": str(refresh),
            "user": UserSerializer(user).data,
        }, status=status.HTTP_200_OK)
        response.set_cookie(key='access_token', value=access_token, httponly=True,secure=True,samesite='None',
                path='/')
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True ,secure=True,samesite='None')
        return response


class LogoutView(APIView):
    """
    Log out the user by clearing the JWT cookie.
    
    Endpoints:
    - POST: Clears the access token cookie and logs out the user.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        response = Response(
            {"detail": "You have been logged out successfully."},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class PasswordResetView(APIView):
    """Dummy password reset endpoint."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"error": "Bad Request", "detail": "Email is required for password reset."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # In a production system, send the reset instructions.
        return Response(
            {"detail": "If an account with that email exists, password recovery instructions have been sent."},
            status=status.HTTP_200_OK
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the current user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


# ---------------------------------------------------
# Product & Category Related Views
# ---------------------------------------------------
class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for products.
    
    Features:
    - Filters products by title, category, price range, location, and condition.
    - Excludes sold products and user's own listings (except for admins).
    - Only owners and admins can update/delete products.
    - Soft deletion by setting is_active=False.
    
    Endpoints:
    - GET: List products with optional filters.
    - POST: Create new product.
    - PUT/PATCH: Update product (owner/admin only).
    - DELETE: Soft delete product (owner/admin only).
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_sold=False, is_active=True).select_related('category', 'seller')
        title = self.request.query_params.get('title')
        category = self.request.query_params.get('category')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        location = self.request.query_params.get('location')
        condition = self.request.query_params.get('condition')
        if title:
            queryset = queryset.filter(title__icontains=title)
        if category:
            queryset = queryset.filter(category__name__iexact=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if condition:
            queryset = queryset.filter(condition__iexact=condition)
        if self.request.user.role != 'Admin':
            queryset = queryset.exclude(seller=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
    def update(self, request, *args, **kwargs):
        product = self.get_object()
        if product.seller != request.user and request.user.role != 'Admin':
            return Response(
                {"error": "Unauthorized", "detail": "You are not authorized to update this product because you are not its owner."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        if product.seller != request.user and request.user.role != 'Admin':
            return Response(
                {"error": "Unauthorized", "detail": "You are not authorized to delete this product because you are not its owner."},
                status=status.HTTP_403_FORBIDDEN
            )
        product.is_active = False
        product.save()
        return Response(
            {"detail": "Product deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    CRUD for product images.
    Only the product owner may add images.
    """
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProductImage.objects.all()
    
    def perform_create(self, serializer):
        product = serializer.validated_data.get('product')
        if product.seller != self.request.user and self.request.user.role != 'Admin':
            raise PermissionDenied("You are only allowed to add images to your own products.")
        serializer.save()


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()


# ---------------------------------------------------
# Transaction Related ViewSet
# ---------------------------------------------------
class TransactionViewSet(viewsets.ModelViewSet):
    """
    Manage buying and selling transactions.
    
    Features:
    - Users can view their transactions as buyer or seller.
    - Admins can view all transactions.
    - Automatically records transaction details during checkout.
    
    Endpoints:
    - GET: List user's transactions.
    - POST: Create new transaction (usually via checkout).
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'Admin':
            return Transaction.objects.all()
        return Transaction.objects.filter(Q(buyer=user) | Q(seller=user))
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data.get('product')
        if not product.is_active:
            return Response(
                {"error": "Product Unavailable", "detail": "This product is not available for purchase."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(
            buyer=request.user,
            seller=product.seller,
            transaction_status='Successful'
        )
        headers = self.get_success_headers(serializer.data)
        response_data = {"detail": "Transaction recorded successfully."}
        response_data.update(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


# ---------------------------------------------------
# Report Related ViewSet
# ---------------------------------------------------
class ReportViewSet(viewsets.ModelViewSet):
    """
    CRUD for reports.
    Non-admin users see only their reports; only admins can update report statuses.
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'Admin':
            return Report.objects.all()
        return Report.objects.filter(reporter=user)
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    def update(self, request, *args, **kwargs):
        if request.user.role != 'Admin':
            return Response(
                {"error": "Unauthorized", "detail": "Only administrators can update report statuses."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


# ---------------------------------------------------
# Conversation & Message (Chat) Related ViewSets
# ---------------------------------------------------
class ConversationViewSet(viewsets.ModelViewSet):
    """
    Manage conversations (chat between users).
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(participants=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conv = serializer.save()
        conv.participants.add(self.request.user)
        headers = self.get_success_headers(serializer.data)
        response_data = {
            "detail": "Conversation created successfully.",
            "conversation": serializer.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class MessageViewSet(viewsets.ModelViewSet):
    """
    Manage messages within a conversation.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(conversation__participants=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.validated_data.get('conversation')
        if self.request.user not in conversation.participants.all():
            conversation.participants.add(self.request.user)
        message = serializer.save(sender=self.request.user)
        headers = self.get_success_headers(serializer.data)
        response_data = {
            "detail": "Message sent successfully.",
            "message": MessageSerializer(message).data
        }
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


# ---------------------------------------------------
# Cart & Order Related ViewSets
# ---------------------------------------------------
class CartItemViewSet(viewsets.ModelViewSet):
    """
    Manage shopping cart items.
    
    Features:
    - Automatically creates cart for new users.
    - Prevents duplicate products in cart.
    - Associates items with user's cart.
    
    Endpoints:
    - GET: List cart items.
    - POST: Add item to cart.
    - DELETE: Remove item from cart.
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart.items.all()
    
    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {"error": "Bad Request", "detail": "Product ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Check for duplicate items using the improved Product model's primary key field: id.
        if cart.items.filter(product__id=product_id).exists():
            return Response(
                {"error": "Duplicate Item", "detail": "This product is already in your cart."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)


class EmptyCartView(APIView):
    """
    Empty your cart by deleting all cart items.
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        cart.items.all().delete()
        return Response(
            {"detail": "Your cart has been emptied successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


class OrderViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for orders.
    Non-admin users can create (if needed) and retrieve their orders.
    Only administrators are allowed to update or delete orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'Admin':
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        # Typically orders are created via checkout.
        return Response(
            {"error": "Method Not Allowed", "detail": "Orders must be created via the checkout process."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        if request.user.role != 'Admin':
            return Response(
                {"error": "Unauthorized", "detail": "Only administrators can update orders."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        if request.user.role != 'Admin':
            return Response(
                {"error": "Unauthorized", "detail": "Only administrators can update orders."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'Admin':
            return Response(
                {"error": "Unauthorized", "detail": "Only administrators can delete orders."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class CheckoutView(APIView):
    """
    Process checkout from shopping cart.
    
    Features:
    - Validates sufficient balance.
    - Creates order and transactions.
    - Updates user balances.
    - Marks products as sold.
    - Clears cart after successful checkout.
    
    Process flow:
    1. Validate cart contents and user balance.
    2. Create order record.
    3. Process payments.
    4. Create transactions.
    5. Update product status.
    6. Clear cart.
    
    Security:
    - Prevents self-purchase of products.
    - Uses atomic transactions for data consistency.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.select_related('product', 'product__seller').all()
        if not cart_items.exists():
            return Response(
                {"error": "Empty Cart", "detail": "Your cart is empty. Please add products before checking out."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate: Ensure you are not purchasing your own products.
        invalid_items = [item for item in cart_items if item.product.seller == request.user]
        if invalid_items:
            titles = ", ".join([item.product.title for item in invalid_items])
            return Response(
                {"error": "Self Purchase Not Allowed", "detail": f"You cannot purchase your own products: {titles}. Please remove these items from your cart."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        total = sum(item.product.price * item.quantity for item in cart_items)
        if request.user.balance < total:
            return Response(
                {"error": "Insufficient Funds", "detail": "Your balance is insufficient to complete the purchase. Please add funds or remove items from your cart."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Deduct the total from the buyer's balance.
            request.user.balance = F('balance') - total
            request.user.save()
            
            # Create the order.
            order = Order.objects.create(user=request.user, total=total, status='Pending')
            
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                seller = item.product.seller
                seller.balance = F('balance') + (item.product.price * item.quantity)
                seller.save()
                
                product = item.product
                product.is_sold = True
                product.bought_by = request.user
                product.save()
                
                Transaction.objects.create(
                    product=product,
                    buyer=request.user,
                    seller=seller,
                    payment_method="Balance",
                    amount=product.price * item.quantity,
                    transaction_status='Successful'
                )
            
            # Clear the cart.
            cart.items.all().delete()
            request.user.refresh_from_db()
            
            order_serializer = OrderSerializer(order)
            return Response(
                {"detail": "Your order has been placed successfully.", "order": order_serializer.data},
                status=status.HTTP_201_CREATED
            )


# ---------------------------------------------------
# Admin Dashboard Related ViewSets
# ---------------------------------------------------
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only endpoints for user management.
    
    Features:
    - Full CRUD access to user accounts.
    - Restricted to admin users only.
    - Manages user roles and permissions.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()


class AdminProductViewSet(viewsets.ModelViewSet):
    """
    Admin-only endpoints for product management.
    
    Features:
    - Override user restrictions.
    - Access to all products including inactive.
    - Can modify any product regardless of owner.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()


class AdminReportViewSet(viewsets.ModelViewSet):
    """
    Admin-only endpoints for report management.
    
    Features:
    - Access to all user reports.
    - Can update report status.
    - Manage dispute resolution.
    """
    serializer_class = ReportSerializer
    permission_classes = [IsAdminUser]
    queryset = Report.objects.all()
