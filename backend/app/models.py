import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .models import PackageItem  # For type hints only


# Enums for status and types
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    BANK_TRANSFER = "bank_transfer"


class VehicleType(str, Enum):
    BIKE = "bike"
    CAR = "car"
    TRUCK = "truck"
    AIRPLANE = "airplane"
    SHIP = "ship"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", sa_relationship_kwargs={"cascade": "delete"})


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Address model
class Address(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    street: str = Field(max_length=255)
    city: str = Field(max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str = Field(max_length=20)
    country: str = Field(max_length=100)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)


# Delivery Company model
class DeliveryCompany(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    phone_number: str = Field(max_length=20)
    headquarters_address_id: uuid.UUID = Field(foreign_key="address.id")
    headquarters_address: Address = Relationship()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


# Package Item model
class PackageItem(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="order.id")
    order: "Order" = Relationship(back_populates="package_items", sa_relationship_kwargs={"cascade": "delete"})
    description: str = Field(max_length=255)
    weight: float
    dimensions: str = Field(max_length=50)
    quantity: int


# Order model
class Order(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_name: str = Field(max_length=255)
    customer_email: EmailStr = Field(max_length=255)
    sender_address_id: uuid.UUID = Field(foreign_key="address.id")
    recipient_address_id: uuid.UUID = Field(foreign_key="address.id")
    sender_address: Address = Relationship(sa_relationship_kwargs={"foreign_keys": "[Order.sender_address_id]"})
    recipient_address: Address = Relationship(sa_relationship_kwargs={"foreign_keys": "[Order.recipient_address_id]"})
    status: OrderStatus
    total_weight: float | None = Field(default=None)
    total_price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    package_items: list[PackageItem] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "delete"})


# Vehicle model
class Vehicle(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    type: VehicleType
    registration_number: str = Field(max_length=50)
    capacity: float
    current_location: str | None = Field(default=None, max_length=255)
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


# Driver model
class Driver(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    phone_number: str = Field(max_length=20)
    license_number: str = Field(max_length=50)
    assigned_vehicle_id: uuid.UUID | None = Field(default=None, foreign_key="vehicle.id")
    assigned_vehicle: Vehicle | None = Relationship()
    availability: bool = Field(default=True)
    current_location: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


# Delivery model
class Delivery(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="order.id")
    driver_id: uuid.UUID | None = Field(default=None, foreign_key="driver.id")
    vehicle_id: uuid.UUID | None = Field(default=None, foreign_key="vehicle.id")
    company_id: uuid.UUID = Field(foreign_key="deliverycompany.id")
    pickup_address_id: uuid.UUID = Field(foreign_key="address.id")
    delivery_address_id: uuid.UUID = Field(foreign_key="address.id")
    order: Order = Relationship()
    driver: Driver | None = Relationship()
    vehicle: Vehicle | None = Relationship()
    company: DeliveryCompany = Relationship()
    pickup_address: Address = Relationship(sa_relationship_kwargs={"foreign_keys": "[Delivery.pickup_address_id]"})
    delivery_address: Address = Relationship(sa_relationship_kwargs={"foreign_keys": "[Delivery.delivery_address_id]"})
    status: DeliveryStatus
    started_at: datetime | None = None
    delivered_at: datetime | None = None


# Payment model
class Payment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="order.id")
    order: Order = Relationship()
    amount: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Feedback model
class Feedback(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="order.id")
    order: Order = Relationship()
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Promotion model
class Promotion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(max_length=50)
    discount_percentage: float = Field(ge=0, le=100)
    expiry_date: datetime
    applicable_countries: str | None = Field(default=None, max_length=1000)  # Comma-separated list of countries
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
