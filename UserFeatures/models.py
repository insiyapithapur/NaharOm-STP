from datetime import time
from django.utils import timezone
import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _
import string
import random
from django.db import models, transaction


class CustomUserManager(BaseUserManager):
    def create_user(self, email, mobile, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not mobile:
            raise ValueError("The Mobile field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superadmin", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)

        user = self.create_user(email, mobile, password, **extra_fields)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField()
    mobile = models.CharField(max_length=15, unique=True)
    is_admin = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.email} ({self.mobile})"


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=50, choices=[("company", "Company"), ("individual", "Individual")]
    )
    user_role_id = models.CharField(max_length=8, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.user_role_id:
            with transaction.atomic():
                last_user_role = UserRole.objects.order_by("id").last()

                if last_user_role:
                    last_id = last_user_role.user_role_id
                    last_char = last_id[1]
                    last_number = int(last_id[2:])

                    if last_number < 999999:
                        new_number = last_number + 1
                        new_user_role_id = f"U{last_char}{str(new_number).zfill(6)}"
                    else:
                        new_char = chr(ord(last_char) + 1) if last_char != "Z" else "A"
                        new_user_role_id = f"U{new_char}000001"
                else:
                    new_user_role_id = "UA000001"

                self.user_role_id = new_user_role_id

        super(UserRole, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.mobile} - {self.role} - {self.user_role_id}"


class CompanyDetails(models.Model):
    user_role = models.OneToOneField(UserRole, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200, editable=False)
    addressLine1 = models.CharField(max_length=200)
    addressLine2 = models.CharField(max_length=300)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    pin_no = models.CharField(max_length=20)
    alternate_phone_no = models.CharField(max_length=15)
    public_url_company = models.URLField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class IndividualDetails(models.Model):
    user_role = models.OneToOneField(UserRole, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200, editable=False)
    last_name = models.CharField(max_length=200, editable=False)
    addressLine1 = models.CharField(max_length=200)
    addressLine2 = models.CharField(max_length=200)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    pin_code = models.BigIntegerField()
    alternate_phone_no = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class PanCardNos(models.Model):
    user_role = models.OneToOneField(UserRole, on_delete=models.CASCADE)
    pan_card_no = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)


class GSTIN_Nos(models.Model):
    user_role = models.OneToOneField(UserRole, on_delete=models.CASCADE)
    GSTIN_no = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)


class BankAccountDetails(models.Model):
    user_role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    account_number = models.BigIntegerField(unique=True)
    ifc_code = models.CharField(max_length=20)
    account_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)


class Wallet(models.Model):
    user_role = models.OneToOneField(UserRole, on_delete=models.CASCADE, unique=True)
    primary_bankID = models.OneToOneField(
        BankAccountDetails, on_delete=models.CASCADE, unique=True
    )
    OutstandingBalance = models.FloatField()
    updated_at = models.DateTimeField()


class Invoices(models.Model):
    invoice_id = models.CharField(max_length=10, unique=True, editable=False)
    primary_invoice_id = models.IntegerField(unique=True)
    product_name = models.CharField(max_length=100)
    principal_price = models.FloatField()
    interest = models.FloatField()
    xirr = models.FloatField()
    irr = models.FloatField()
    tenure_in_days = models.IntegerField()
    expiration_time = models.DateTimeField()
    expired = models.BooleanField(default=False)
    created_At = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            with transaction.atomic():
                last_invoice = Invoices.objects.all().order_by("id").last()
                if last_invoice:
                    last_id = last_invoice.invoice_id[2:]
                    prefix = last_invoice.invoice_id[:2]

                    if last_id.isdigit() and int(last_id) == 999999:
                        prefix = self.increment_prefix(prefix)
                        new_id = 1
                    else:
                        new_id = int(last_id) + 1
                else:
                    prefix = "IA"
                    new_id = 1

                self.invoice_id = f"{prefix}{new_id:06d}"

            super(Invoices, self).save(*args, **kwargs)

    def increment_prefix(self, prefix):
        """
        Increment the alphabetic prefix, cycling through letters like 'IA', 'IB', ..., 'IZ', 'JA', etc.
        """
        if not prefix:
            return "AA"

        prefix_chars = list(prefix)

        for i in reversed(range(len(prefix_chars))):
            if prefix_chars[i] != "Z":
                prefix_chars[i] = chr(ord(prefix_chars[i]) + 1)
                break
            else:
                prefix_chars[i] = "A"
        return "".join(prefix_chars)

    def __str__(self):
        return self.invoice_id


class Configurations(models.Model):
    principal_price = models.FloatField()
    no_of_units = models.IntegerField()
    per_unit_price = models.FloatField()
    invoice_id = models.OneToOneField(Invoices, on_delete=models.CASCADE, unique=True)
    user_id = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    remaining_units = models.IntegerField()


class FractionalUnits(models.Model):
    fractional_unit_id = models.CharField(max_length=20, unique=True, editable=False)
    invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    current_owner = models.ForeignKey(
        UserRole, on_delete=models.CASCADE, null=True, blank=True
    )
    posted_for_sale = models.BooleanField(default=False)
    configurationID = models.ForeignKey(
        Configurations, on_delete=models.CASCADE, null=True, blank=True
    )
    created_At = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.fractional_unit_id:
            with transaction.atomic():
                invoice_core = self.invoice.invoice_id[1:]

                fractional_prefix = f"F{invoice_core}"
                last_unit = (
                    FractionalUnits.objects.filter(invoice=self.invoice)
                    .order_by("id")
                    .last()
                )
                if last_unit:
                    last_unit_id_str = last_unit.fractional_unit_id.split("-")[-1]
                    last_unit_id = int(last_unit_id_str)
                    new_unit_id = last_unit_id + 1
                else:
                    new_unit_id = 1

                self.fractional_unit_id = f"{fractional_prefix}-{new_unit_id}"
            super(FractionalUnits, self).save(*args, **kwargs)

    def __str__(self):
        return self.fractional_unit_id


class AdminSettings(models.Model):
    interest_cut_off_time = models.TimeField(default=time(12, 0))

    def __str__(self):
        return f"Interest Cut Off Time: {self.interest_cut_off_time}"


class Post_for_sale(models.Model):
    TYPE_CHOICES = [
        ("Fixed", "Fixed"),
        ("Bidding", "Bid"),
    ]
    no_of_units = models.IntegerField()
    per_unit_price = models.FloatField()
    user_id = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    invoice_id = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    remaining_units = models.IntegerField()
    total_price = models.FloatField()
    withdrawn = models.BooleanField(default=False)
    post_time = models.TimeField(default=timezone.now)
    post_date = models.DateField(default=timezone.now)
    from_date = models.DateField()
    to_date = models.DateField()
    sold = models.BooleanField(default=False)

    type = models.CharField(
        max_length=50, choices=TYPE_CHOICES, default="fixed"
    )  # change to bid when user post with bidding
    no_of_bid = models.IntegerField(null=True, default=0)
    open_for_bid = models.BooleanField(null=True, default=False)

    post_dateTime = models.DateTimeField(default=timezone.now)
    configurationID = models.ForeignKey(
        Configurations, on_delete=models.CASCADE, null=True, blank=True
    )
    is_admin = models.BooleanField()


# one to one with wallet
class Buyers(models.Model):
    user_id = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    # invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    no_of_units = models.IntegerField()
    per_unit_price_invested = models.FloatField()
    # null=True,blank=True
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    purchase_date = models.DateField(default=timezone.now)
    purchase_time = models.TimeField(default=timezone.now)
    purchase_date_time = models.DateTimeField(default=timezone.now)


# One to one relation of all fields
class Buyer_UnitsTracker(models.Model):
    buyer_id = models.ForeignKey(Buyers, on_delete=models.CASCADE)
    unitID = models.ForeignKey(FractionalUnits, on_delete=models.CASCADE)
    post_for_saleID = models.ForeignKey(
        Post_for_sale, on_delete=models.CASCADE, null=True, default=None
    )


class Sales(models.Model):
    UserID = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    Invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    no_of_units = models.IntegerField()
    sell_date = models.DateField(default=timezone.now)
    sell_time = models.TimeField(default=timezone.now)
    sell_date_time = models.DateTimeField(default=timezone.now)


class Post_For_Sale_UnitTracker(models.Model):
    unitID = models.ForeignKey(FractionalUnits, on_delete=models.CASCADE)
    post_for_saleID = models.ForeignKey(Post_for_sale, on_delete=models.CASCADE)
    sellersID = models.ForeignKey(
        Sales, on_delete=models.CASCADE, null=True, default=None
    )


# unitID is one to one
class Sales_UnitTracker(models.Model):
    unitID = models.ForeignKey(FractionalUnits, on_delete=models.CASCADE)
    sellersID = models.ForeignKey(
        Sales, on_delete=models.CASCADE, null=True, default=None
    )


class User_Bid(models.Model):
    STATUS_CHOICES = [
        ("awaiting_acceptance", "Awaiting Acceptance"),
        ("closed", "Closed"),
        ("expired", "Expired"),
        ("Accepted", "Accepted"),
    ]
    posted_for_sale_id = models.ForeignKey(Post_for_sale, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="bid_open")
    user_id = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    per_unit_bid_price = models.FloatField()
    no_of_units = models.IntegerField()
    withdraw = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)
    datetime = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Bid {self.id}: User {self.user_id.user.mobile}, Status: {self.status}"


class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    type = models.CharField(max_length=50, null=True)  # buy / sell / fund / withdraw
    creditedAmount = models.FloatField(null=True)
    debitedAmount = models.FloatField(null=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("initiated", "Initiated"),
            ("processing", "Processing"),
            ("response", "Response"),
        ],
    )
    source = models.CharField(
        max_length=50,
        choices=[
            ("bank_to_wallet", "Bank to Wallet"),
            ("wallet_to_bank", "Wallet to Bank"),
            ("wallet_to_buy", "Wallet to Buy"),
            ("sell_to_wallet", "Sell to Wallet"),
        ],
    )
    purpose = models.CharField(max_length=255, null=True)
    # withdraw -> wallet to bank -> from wallet to bank
    # fund -> bank to wallet -> from bank Account to wallet

    # wallet to wallet ->
    # buy to wallet -> from wallet (wallet) to wallet (seller)
    # wallet to sell -> from wallet (buyer) to wallet (wallet)

    # from wallet --> potani / buyer
    # to wallet --> potani / seller
    # from bank -> fund
    # to bank -> withdraw
    from_bank_acc = models.ForeignKey(
        BankAccountDetails,
        on_delete=models.CASCADE,
        null=True,
        related_name="from_bank_transactions",
    )
    to_bank_acc = models.ForeignKey(
        BankAccountDetails,
        on_delete=models.CASCADE,
        null=True,
        related_name="to_bank_transactions",
    )
    from_wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, null=True, related_name="from_wallet"
    )
    to_wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, null=True, related_name="to_wallet"
    )
    invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE, null=True)
    time_date = models.DateTimeField()


class SalePurchaseReport(models.Model):
    invoiceID = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    unitID = models.ForeignKey(FractionalUnits, on_delete=models.CASCADE)
    seller_ID = models.ForeignKey(
        UserRole, on_delete=models.CASCADE, related_name="sellerID"
    )
    buyerID_ID = models.ForeignKey(
        UserRole, on_delete=models.CASCADE, related_name="buyerID"
    )
    Sale_Buy_Date = models.DateField(default=timezone.now)
    Sale_Buy_per_unit_price = models.FloatField()
    ListingDate = models.DateField(default=timezone.now)
    transfer_date = models.DateField(default=timezone.now)
    no_of_days_units_held = models.IntegerField()
    interest_due_to_seller = models.FloatField()
    TDS_deducted = models.FloatField()
    IRR = models.FloatField()


class BidReport(models.Model):
    unitID = models.ForeignKey(FractionalUnits, on_delete=models.CASCADE)
    user_BidID = models.ForeignKey(User_Bid, on_delete=models.CASCADE)
    ListingDate = models.DateField(default=timezone.now)
    post_for_saleID = models.ForeignKey(Post_for_sale, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)


# class TDSReport(models.Model):
#     PurchaserID = models.ForeignKey(UserRole,on_delete=models.CASCADE , related_name='buyerID')
#     Name_of_the_Co" : "None",
#                     "PAN_No_of_the_Co" : "None",
#                     "TAN_No_of_the_Co" : "None",
#                     "Value_of_Per_Unit": 10000,
#                     "Units_Purchased" : 2,
#                     "Date_of_Purchase" : "2024-08-01",
#                     "Interest_date " : "2024-08-01",
#                     "ROI" : 3.7 ,
#                     "Sale_price_per_unit" : 10000,
#                     "Sell_Date" : "2024-08-01",
#                     "Total_No_of_days_Units_were_held" : 84,
#                     "Total_Amount_credited" : 10000,
#                     "Expected_Interest" : 6.78,
#                     "Actual_Interest_credited": 6.73,
#                     "Date_of_Payment" : "2024-08-01",
#                     "Nature_of_Payment" : "MONTHLY",
#                     "Quarter" : "None",
#                     "TDS" : 20,
#                     "Reciept_No_of_TDS":21,
#                     "CIN details" : "None"
