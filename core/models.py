import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# ---------------------------------------------------
# Choice Constants
# ---------------------------------------------------
ROLE_CHOICES = [
    ('User', 'User'),
    ('Admin', 'Admin'),
]

CONDITION_CHOICES = [
    ('New', 'New'),
    ('Used', 'Used'),
]

PAYMENT_METHOD_CHOICES = [
    ('CreditCard', 'Credit Card'),
    ('PayPal', 'PayPal'),
    ('CashOnDelivery', 'Cash on Delivery'),
    ('Balance', 'Balance'),
]

TRANSACTION_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Successful', 'Successful'),
    ('Failed', 'Failed'),
]

REPORT_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Reviewed', 'Reviewed'),
    ('Resolved', 'Resolved'),
]

ORDER_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Processing', 'Processing'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
]


# ---------------------------------------------------
# Abstract Base Model for UUID Primary Key and Timestamps
# ---------------------------------------------------
class UUIDTimeStampedModel(models.Model):
    """
    Abstract base model that provides a UUID primary key, created_at, and updated_at fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, help_text="The time when the record was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="The time when the record was last updated.")

    class Meta:
        abstract = True


# ---------------------------------------------------
# Custom User Manager
# ---------------------------------------------------
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='User', **extra_fields):
        """
        Create and save a User with the given username, email, password, and role.
        """
        if not username:
            raise ValueError('The Username must be set')
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Create and save a superuser with role 'Admin' and appropriate privileges.
        """
        extra_fields.setdefault('role', 'Admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('role') != 'Admin':
            raise ValueError('Superuser must have role of Admin.')
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, email, password, **extra_fields)


# ---------------------------------------------------
# Custom User Model
# ---------------------------------------------------
class User(AbstractBaseUser, PermissionsMixin, UUIDTimeStampedModel):
    """
    Custom User model for the Buy and Sell Pre-owned Items web application.
    """
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = models.EmailField(unique=True)
    profile_picture_url = models.URLField(blank=True, null=True)
    contact_details = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='User')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1000.00'),
        help_text="User's wallet balance. Defaults to 1000.00."
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------
# Category Model
# ---------------------------------------------------
class Category(UUIDTimeStampedModel):
    """
    Represents a product category (e.g., Electronics, Furniture, Clothing).
    """
    name = models.CharField(max_length=100, unique=True, help_text="Unique category name.")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"


# ---------------------------------------------------
# Product Model
# ---------------------------------------------------
class Product(UUIDTimeStampedModel):
    """
    Represents a product listing uploaded by a seller.
    """
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    location = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    is_active = models.BooleanField(default=True)
    is_sold = models.BooleanField(default=False)
    bought_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_products'
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------
# Product Image Model
# ---------------------------------------------------
class ProductImage(UUIDTimeStampedModel):
    """
    Represents an image associated with a product listing.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=1000)
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Determines the display order of images.")

    def __str__(self):
        return f"Image for {self.product.title} (Order: {self.order})"

    class Meta:
        ordering = ['order']


# ---------------------------------------------------
# Transaction Model
# ---------------------------------------------------
class Transaction(UUIDTimeStampedModel):
    """
    Records a product sale transaction.
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='transaction')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Transaction {self.id} for {self.product.title}"

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------
# Report Model
# ---------------------------------------------------
class Report(UUIDTimeStampedModel):
    """
    Represents a user report regarding a product or another user.
    """
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    reported_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reports', blank=True, null=True
    )
    reported_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_reports', blank=True, null=True
    )
    reason = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='Pending')
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='reviewed_reports', blank=True, null=True
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Report {self.id} by {self.reporter.username}"

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------
# Conversation Model (for Chat)
# ---------------------------------------------------
class Conversation(UUIDTimeStampedModel):
    """
    Groups messages between users, optionally linked to a specific product.
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='conversations', blank=True, null=True
    )
    participants = models.ManyToManyField(User, related_name='conversations')

    def __str__(self):
        return f"Conversation for {self.product.title}" if self.product else f"Conversation {self.id}"

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------
# Message Model (Chat)
# ---------------------------------------------------
class Message(UUIDTimeStampedModel):
    """
    Represents an individual chat message within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(help_text="Content of the message.")
    read_status = models.BooleanField(default=False, help_text="Indicates whether the message has been read.")

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

    class Meta:
        ordering = ['created_at']


# ---------------------------------------------------
# Cart Model
# ---------------------------------------------------
class Cart(UUIDTimeStampedModel):
    """
    Represents a user's shopping cart.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')

    def __str__(self):
        return f"Cart({self.user.username})"


# ---------------------------------------------------
# CartItem Model
# ---------------------------------------------------
class CartItem(UUIDTimeStampedModel):
    """
    Represents an item added to a user's cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"


# ---------------------------------------------------
# Order Model
# ---------------------------------------------------
class Order(UUIDTimeStampedModel):
    """
    Represents an order placed by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Total order amount.")

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    class Meta:
        ordering = ['-created_at']


# ---------------------------------------------------
# OrderItem Model
# ---------------------------------------------------
class OrderItem(UUIDTimeStampedModel):
    """
    Represents an individual item within an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per item at the time of order.")

    def __str__(self):
        product_title = self.product.title if self.product else 'Unknown Product'
        return f"{self.quantity} x {product_title}"
