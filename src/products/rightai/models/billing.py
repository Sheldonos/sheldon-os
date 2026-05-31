"""
Billing Data Models

Models for billing, invoicing, and payment processing.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BillingStatus(str, Enum):
    """Billing status enumeration."""

    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethodType(str, Enum):
    """Payment method type enumeration."""

    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    CREDITS = "credits"


class BillingRecord(BaseModel):
    """
    Billing record model.

    Represents a billing period for a user.
    """

    # Identity
    id: str = Field(..., description="Unique billing record ID")
    user_id: str = Field(..., description="User ID")

    # Period
    period_start: datetime = Field(..., description="Billing period start")
    period_end: datetime = Field(..., description="Billing period end")

    # Usage summary
    total_calls: int = Field(default=0, description="Total API calls", ge=0)
    total_tokens: int = Field(default=0, description="Total tokens used", ge=0)
    total_minutes: float = Field(
        default=0.0,
        description="Total minutes used",
        ge=0,
    )
    total_mb: float = Field(
        default=0.0,
        description="Total MB processed",
        ge=0,
    )

    # Cost breakdown
    usage_cost: float = Field(default=0.0, description="Cost from usage", ge=0)
    subscription_cost: float = Field(
        default=0.0,
        description="Subscription cost",
        ge=0,
    )
    platform_fee: float = Field(
        default=0.0,
        description="Platform fee",
        ge=0,
    )
    tax: float = Field(default=0.0, description="Tax amount", ge=0)
    discounts: float = Field(
        default=0.0,
        description="Discounts applied",
        ge=0,
    )

    # Totals
    subtotal: float = Field(
        default=0.0,
        description="Subtotal before tax",
        ge=0,
    )
    total_cost: float = Field(
        default=0.0,
        description="Total cost",
        ge=0,
    )
    net_amount: float = Field(
        default=0.0,
        description="Net amount after fees",
        ge=0,
    )

    # Credits
    credits_used: float = Field(
        default=0.0,
        description="Credits used",
        ge=0,
    )
    credits_remaining: float = Field(
        default=0.0,
        description="Credits remaining",
        ge=0,
    )

    # Status
    status: BillingStatus = Field(
        default=BillingStatus.PENDING, description="Billing status"
    )

    # Payment
    payment_method_id: Optional[str] = Field(
        None,
        description="Payment method used",
    )
    payment_intent_id: Optional[str] = Field(
        None, description="Payment intent ID (Stripe)"
    )

    # Invoice
    invoice_id: Optional[str] = Field(None, description="Invoice ID")
    invoice_url: Optional[str] = Field(None, description="Invoice URL")
    invoice_pdf_url: Optional[str] = Field(None, description="Invoice PDF URL")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    due_date: Optional[datetime] = Field(None, description="Payment due date")

    # Tool breakdown
    tool_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list, description="Cost by tool"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def calculate_totals(self):
        """Calculate total amounts."""
        self.subtotal = (
            self.usage_cost + self.subscription_cost - self.discounts
        )
        self.total_cost = self.subtotal + self.tax
        self.net_amount = self.total_cost - self.platform_fee

    def is_overdue(self) -> bool:
        """Check if billing is overdue."""
        if self.status == BillingStatus.PAID:
            return False
        if self.due_date and datetime.utcnow() > self.due_date:
            return True
        return False

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for BillingRecord."""

        json_schema_extra = {
            "example": {
                "id": "bill_abc123",
                "user_id": "user_456",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z",
                "total_calls": 1000,
                "total_tokens": 150000,
                "usage_cost": 150.00,
                "subscription_cost": 49.00,
                "platform_fee": 49.75,
                "tax": 19.90,
                "subtotal": 199.00,
                "total_cost": 218.90,
                "status": "paid",
                "paid_at": "2024-02-01T10:00:00Z",
            }
        }


class Invoice(BaseModel):
    """
    Invoice model.

    Detailed invoice for a billing period.
    """

    # Identity
    id: str = Field(..., description="Unique invoice ID")
    invoice_number: str = Field(
        ...,
        description="Human-readable invoice number",
    )
    billing_record_id: str = Field(
        ...,
        description="Associated billing record",
    )

    # Customer info
    user_id: str = Field(..., description="User ID")
    customer_name: str = Field(..., description="Customer name")
    customer_email: str = Field(..., description="Customer email")
    billing_address: Optional[Dict[str, str]] = Field(
        None, description="Billing address"
    )
    tax_id: Optional[str] = Field(None, description="Tax ID / VAT number")

    # Invoice details
    issue_date: datetime = Field(
        default_factory=datetime.utcnow, description="Issue date"
    )
    due_date: datetime = Field(..., description="Due date")
    period_start: datetime = Field(..., description="Billing period start")
    period_end: datetime = Field(..., description="Billing period end")

    # Line items
    line_items: List[Dict[str, Any]] = Field(
        ...,
        description="Invoice line items",
    )

    # Amounts
    subtotal: float = Field(..., description="Subtotal", ge=0)
    tax_rate: float = Field(default=0.0, description="Tax rate", ge=0, le=1)
    tax_amount: float = Field(default=0.0, description="Tax amount", ge=0)
    discount_amount: float = Field(
        default=0.0,
        description="Discount amount",
        ge=0,
    )
    total_amount: float = Field(..., description="Total amount", ge=0)
    amount_paid: float = Field(default=0.0, description="Amount paid", ge=0)
    amount_due: float = Field(..., description="Amount due", ge=0)

    # Currency
    currency: str = Field(default="USD", description="Currency code")

    # Status
    status: BillingStatus = Field(
        default=BillingStatus.PENDING, description="Invoice status"
    )

    # Payment
    payment_terms: str = Field(
        default="Due on receipt",
        description="Payment terms",
    )
    payment_method: Optional[str] = Field(None, description="Payment method")

    # URLs
    pdf_url: Optional[str] = Field(None, description="PDF URL")
    hosted_url: Optional[str] = Field(None, description="Hosted invoice URL")

    # Notes
    notes: Optional[str] = Field(None, description="Invoice notes")
    footer: Optional[str] = Field(None, description="Invoice footer")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = Field(None)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_line_item(
        self,
        description: str,
        quantity: float,
        unit_price: float,
        amount: float,
    ):
        """Add a line item to the invoice."""
        self.line_items.append(
            {
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            }
        )

    def calculate_total(self):
        """Calculate invoice total."""
        self.subtotal = sum(item["amount"] for item in self.line_items)
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = (
            self.subtotal + self.tax_amount - self.discount_amount
        )
        self.amount_due = self.total_amount - self.amount_paid

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Invoice."""

        json_schema_extra = {
            "example": {
                "id": "inv_abc123",
                "invoice_number": "INV-2024-001",
                "billing_record_id": "bill_abc123",
                "user_id": "user_456",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "issue_date": "2024-02-01T00:00:00Z",
                "due_date": "2024-02-15T00:00:00Z",
                "line_items": [
                    {
                        "description": "GPT-4 Turbo API Usage",
                        "quantity": 150000,
                        "unit_price": 0.001,
                        "amount": 150.00,
                    }
                ],
                "subtotal": 150.00,
                "tax_rate": 0.1,
                "tax_amount": 15.00,
                "total_amount": 165.00,
                "status": "paid",
            }
        }


class PaymentMethod(BaseModel):
    """
    Payment method model.

    Stored payment method for a user.
    """

    # Identity
    id: str = Field(..., description="Payment method ID")
    user_id: str = Field(..., description="User ID")

    # Type
    type: PaymentMethodType = Field(..., description="Payment method type")

    # Card details (if type is card)
    card_brand: Optional[str] = Field(
        None, description="Card brand (Visa, Mastercard, etc.)"
    )
    card_last4: Optional[str] = Field(None, description="Last 4 digits")
    card_exp_month: Optional[int] = Field(
        None, description="Expiration month", ge=1, le=12
    )
    card_exp_year: Optional[int] = Field(None, description="Expiration year")

    # Bank account details (if type is bank_account)
    bank_name: Optional[str] = Field(None, description="Bank name")
    account_last4: Optional[str] = Field(
        None,
        description="Last 4 digits of account",
    )

    # PayPal details (if type is paypal)
    paypal_email: Optional[str] = Field(None, description="PayPal email")

    # Crypto details (if type is crypto)
    crypto_address: Optional[str] = Field(
        None,
        description="Crypto wallet address",
    )
    crypto_network: Optional[str] = Field(None, description="Crypto network")

    # Status
    is_default: bool = Field(
        default=False,
        description="Is default payment method",
    )
    is_verified: bool = Field(
        default=False,
        description="Is verified",
    )

    # External IDs
    stripe_payment_method_id: Optional[str] = Field(
        None, description="Stripe payment method ID"
    )

    # Billing details
    billing_name: Optional[str] = Field(None, description="Billing name")
    billing_email: Optional[str] = Field(None, description="Billing email")
    billing_address: Optional[Dict[str, str]] = Field(
        None, description="Billing address"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(None)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if card is expired."""
        if self.type != PaymentMethodType.CARD:
            return False
        if not self.card_exp_month or not self.card_exp_year:
            return False

        now = datetime.utcnow()
        if self.card_exp_year < now.year:
            return True
        if self.card_exp_year == now.year and self.card_exp_month < now.month:
            return True
        return False

    def get_display_name(self) -> str:
        """Get display name for payment method."""
        if self.type == PaymentMethodType.CARD:
            return f"{self.card_brand} •••• {self.card_last4}"
        if self.type == PaymentMethodType.BANK_ACCOUNT:
            return f"{self.bank_name} •••• {self.account_last4}"
        if self.type == PaymentMethodType.PAYPAL:
            return f"PayPal ({self.paypal_email})"
        if self.type == PaymentMethodType.CRYPTO:
            return f"Crypto ({self.crypto_network})"
        return "Credits"

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for PaymentMethod."""

        json_schema_extra = {
            "example": {
                "id": "pm_abc123",
                "user_id": "user_456",
                "type": "card",
                "card_brand": "Visa",
                "card_last4": "4242",
                "card_exp_month": 12,
                "card_exp_year": 2025,
                "is_default": True,
                "is_verified": True,
            }
        }


class Payment(BaseModel):
    """
    Payment transaction model.

    Records individual payment transactions.
    """

    # Identity
    id: str = Field(..., description="Payment ID")
    user_id: str = Field(..., description="User ID")
    billing_record_id: Optional[str] = Field(
        None, description="Associated billing record"
    )
    invoice_id: Optional[str] = Field(None, description="Associated invoice")

    # Amount
    amount: float = Field(..., description="Payment amount", ge=0)
    currency: str = Field(default="USD", description="Currency code")

    # Payment method
    payment_method_id: str = Field(..., description="Payment method used")
    payment_method_type: PaymentMethodType = Field(
        ..., description="Payment method type"
    )

    # Status
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, description="Payment status"
    )

    # External IDs
    stripe_payment_intent_id: Optional[str] = Field(
        None, description="Stripe payment intent ID"
    )
    stripe_charge_id: Optional[str] = Field(
        None,
        description="Stripe charge ID",
    )

    # Details
    description: Optional[str] = Field(None, description="Payment description")
    receipt_url: Optional[str] = Field(None, description="Receipt URL")

    # Error handling
    failure_code: Optional[str] = Field(
        None,
        description="Failure code if failed",
    )
    failure_message: Optional[str] = Field(
        None, description="Failure message if failed"
    )

    # Refund
    refunded: bool = Field(default=False, description="Has been refunded")
    refund_amount: float = Field(
        default=0.0,
        description="Refund amount",
        ge=0,
    )
    refund_reason: Optional[str] = Field(None, description="Refund reason")
    refunded_at: Optional[datetime] = Field(
        None,
        description="Refund timestamp",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    succeeded_at: Optional[datetime] = Field(None)
    failed_at: Optional[datetime] = Field(None)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.SUCCEEDED

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Payment."""

        json_schema_extra = {
            "example": {
                "id": "pay_abc123",
                "user_id": "user_456",
                "billing_record_id": "bill_abc123",
                "amount": 218.90,
                "currency": "USD",
                "payment_method_id": "pm_abc123",
                "payment_method_type": "card",
                "status": "succeeded",
                "description": "Payment for January 2024",
                "succeeded_at": "2024-02-01T10:00:00Z",
            }
        }


class Refund(BaseModel):
    """
    Refund model.

    Records refund transactions.
    """

    id: str = Field(..., description="Refund ID")
    payment_id: str = Field(..., description="Original payment ID")
    user_id: str = Field(..., description="User ID")

    # Amount
    amount: float = Field(..., description="Refund amount", ge=0)
    currency: str = Field(default="USD", description="Currency code")

    # Reason
    reason: str = Field(..., description="Refund reason")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Status
    status: str = Field(default="pending", description="Refund status")

    # External IDs
    stripe_refund_id: Optional[str] = Field(
        None,
        description="Stripe refund ID",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(None)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic schema configuration for Refund."""

        json_schema_extra = {
            "example": {
                "id": "ref_abc123",
                "payment_id": "pay_abc123",
                "user_id": "user_456",
                "amount": 50.00,
                "reason": "Service issue",
                "status": "succeeded",
                "processed_at": "2024-02-05T14:30:00Z",
            }
        }


# Made with Bob
