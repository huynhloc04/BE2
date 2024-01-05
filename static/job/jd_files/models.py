from datetime import datetime
from sqlalchemy import text, UniqueConstraint,  Column, TIMESTAMP, UniqueConstraint
from sqlmodel import Field, SQLModel, Relationship, JSON
from typing import List, Optional, Set
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.dialects import postgresql
from enum import Enum
from sqlalchemy.types import Integer, String


class StatusEnum(str, Enum):
    active = "active"
    unactive = "unactive"

class Currency(str, Enum):
    vnd = "vnd"
    usd = "usd"

class GiftStatus(str, Enum):
    in_stock = "in_stock"
    out_stock = "out_stock"


class TableBase(SQLModel):
    """
    A base class for SQLModel tables.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=datetime.utcnow,
        )
    )
    

class User(TableBase, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    first_name: str = Field(nullable=True)
    last_name: str = Field(nullable=True)
    phone: str = Field(nullable=True, index=True)
    address: str = Field(nullable=True)
    age: int = Field(nullable=True, default=None)
    sex: str = Field(nullable=True, default=None)
    hashed_password: str = Field(nullable=True)
    role: str = Field(nullable=False)
    blog: List["Blog"] = Relationship(back_populates="author")
    order: List["Order"] = Relationship(back_populates="user")
    refresh_token: str = Field(max_length=255, nullable=True)
    is_active: bool = Field(default=True)
    is_verify: bool = Field(default=False)
    is_verify_reset_password: bool = Field(default=False)
    

class JWTModel(TableBase, table=True): # BlacklistToken
    __tablename__ = "blacklisted_jwt"
    
    token: str = Field(unique=True, nullable=False)


class OTPModel(TableBase, table=True):
    __tablename__ = "otps"

    user_id: int = Field(foreign_key="users.id")
    otp: Optional[str] = Field(nullable=True)
    
    
class Tag(TableBase, table=True):
    """
    A tag for a blog.
    """    
    __tablename__ = "tags"
    name: str = Field(nullable=True, default=None)
    

class Category(TableBase, table=True):
    __tablename__ = "categories"

    name: str = Field(nullable=False, unique=True)
    parent_id: Optional[int] = Field(nullable=True, default=None, foreign_key="categories.id")


class Blog(TableBase, table=True):
    __tablename__ = "blogs"

    title: Optional[str] = Field(default=None)
    author_id: Optional[int] = Field(default=None, foreign_key="users.id")
    author_name: Optional[str] = Field(default=None, nullable=True)
    author: Optional[User] = Relationship(back_populates="blog")
    content: Optional[str] = Field(sa_column=Column(TEXT)) 
    image_link: Optional[str] = Field(default=None)
    tag_ids: Optional[List[int]] = Field(default=None, sa_column=Column(postgresql.ARRAY(Integer())))
    category_id: Optional[int] = Field(foreign_key="categories.id")
    status: Optional[bool] = Field(default=None)
    
    
class Image(TableBase, table=True):
    __tablename__ = "images"

    img_link: str = Field(index=True)

class Product(TableBase, table=True):
    __tablename__ = "products"
    
    name: Optional[str] = Field(unique=True, index=True)
    image_link: Optional[str] = Field(default=None)
    is_feature: Optional[bool] = Field(default=False)
    description: Optional[str] = Field(default=None) 
    brand_id: Optional[int] = Field(foreign_key="brands.id") 
    category_id: Optional[int] = Field(foreign_key="categories.id")
    tag_ids: Optional[List[int]] = Field(default=None, sa_column=Column(postgresql.ARRAY(Integer())))
    sale_count: Optional[int] = Field(default=0, nullable=True)
    vote_average_rating: Optional[float] = Field(default=0.0, nullable=True)
    variant: List["Variant"] = Relationship(back_populates="product")
    

class Brand(TableBase, table=True):
    __tablename__ = "brands"

    name: str = Field(default=None)
    description: Optional[str] = Field(sa_column=Column(TEXT)) 
    
    
class Variant_VariantTag_Join(SQLModel, table=True):
    """
    A link between a blog post and a tag.
    """
    
    __tablename__ = "variant_tag_join"
    variant_id: Optional[int] = Field(
        default=None,
        foreign_key="variants.id",
        primary_key=True,
    )
    variant_tag_id: Optional[int] = Field(
        default=None,
        foreign_key="variant_tags.id",
        primary_key=True,
    )
    tag_value: float = Field(default=None)


class Variant(TableBase, table=True):
    __tablename__ = "variants"

    product_id: int = Field(foreign_key="products.id")
    sku: str = Field(unique=True, nullable=False)
    image_link: Optional[str] = Field(default=None)
    price: float = Field(default=0.0)
    price_sale: Optional[float] = Field(default=0.0)
    currency: str = Field(default="vnd")
    stock: Optional[int] = Field(default=None)
    status: Optional[str] = Field(default=None)     #   Còn hàng / Hết hàng
    product: Product = Relationship(back_populates="variant")
    variant_tags: List["VariantTag"] = Relationship(back_populates="variants", 
                                                    link_model=Variant_VariantTag_Join)
    
    
class VariantTag(TableBase, table=True):
    __tablename__ = "variant_tags"

    name: str = Field(default=None)
    variants: List[Variant] = Relationship(back_populates="variant_tags", 
                                           link_model=Variant_VariantTag_Join)


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=datetime.utcnow,
        ))
    order_code: str = Field(default=None, primary_key=True)
    fullname: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    email_address: Optional[str] = Field(default=None)
    address_delivery: Optional[str] = Field(default=None)
    product_count: Optional[int] = Field(default=None)
    # end_delivery: Optional[str] = Field(default=None, nullable=True)
    total_money: Optional[float] = Field(default=None)
    total_money_sale: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default="pending")   #   Pending, Giao thanh cong, Da huy
    user_id: Optional[int] = Field(default=None, nullable=True, foreign_key='users.id')
    note: Optional[str] = Field(default=None, nullable=True)
    cancel_reason: Optional[str] = Field(default=None, nullable=True)
    user: "User" = Relationship(back_populates="order")
    order_details: "OrderDetail" = Relationship(back_populates="orders")


class OrderDetail(TableBase, table=True):
    __tablename__ = "order_details"

    order_code: str = Field(default=None, foreign_key='orders.order_code')
    name: str = Field(default=None)
    image: str = Field(default=None)
    price: float = Field(default=None)
    price_sale: float = Field(default=None)
    currency: str = Field(default=None)
    quantity: int = Field(default=None)
    orders: List[Order] = Relationship(back_populates="order_details")


class PromotionOrderJoin(TableBase, table=True):
    """
    A link between a blog post and a tag.
    """
    
    __tablename__ = "promotion_order_joins"

    order_code: str = Field(foreign_key="orders.order_code")
    promotion_discount_code: Optional[str] = Field(default=None)
    promotion_service_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    promotion_gift_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))


class CouponOrderJoin(TableBase, table=True):
    """
    A link between a blog post and a tag.
    """
    
    __tablename__ = "coupon_order_joins"

    order_code: str = Field(foreign_key="orders.order_code")
    coupon_discount_code: Optional[str] = Field(default=None)
    coupon_service_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    coupon_gift_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))


#   =======================================================
#                       Promotion
#   =======================================================

class PromotionProductJoin(TableBase, table=True):
    """
    A link between a blog post and a tag.
    """
    
    __tablename__ = "promotion_product_joins"

    product_id: Optional[int] = Field(foreign_key="products.id")
    promotion_info_code: Optional[str] = Field(default=None)  
    promotion_discount_code: Optional[str] = Field(default=None)  
    promotion_service_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    promotion_gift_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    promotion_variant_ids: Optional[List[int]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))


class PromotionUserJoin(TableBase, table=True):
    """
    A link between a blog post and a tag.
    """
    
    __tablename__ = "promotion_user_joins"

    user_id: Optional[int] = Field(foreign_key="users.id")
    promotion_info_code: Optional[int] = Field(default=None)  
    promotion_discount_code: Optional[str] = Field(default=None)  
    promotion_service_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    promotion_gift_codes: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    promotion_variant_ids: Optional[List[int]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))


class PromotionInfo(TableBase, table=True):
    __tablename__ = "promotion_infos"

    code: Optional[str] = Field(unique=True, default=None)
    title: Optional[str] = Field(default=None)
    start_time: Optional[str] = Field(default=None)
    end_time: Optional[str] = Field(default=None)
    num_util: Optional[int] = Field(default=None)     #   So lan su dung
    amount: Optional[int] = Field(default=None)   #   So luong ma giam gia
    description: Optional[str] = Field(default=None)
    status: Optional[StatusEnum] = Field(default=False)


class PromotionDiscount(TableBase, table=True): 
    __tablename__ = "promotion_discounts"

    #   Tab giam gia
    code: Optional[str] = Field(unique=True, default=None)
    title: Optional[str] = Field(default=None)
    price: Optional[float] = Field(default=None)
    currency: Optional[Currency] = Field(default='vnd')


class PromotionService(TableBase, table=True):
    __tablename__ = "promotion_services"

    #   Tab khuyen mai dich vu
    code: Optional[str] = Field(unique=True, default=None)
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
        
    
class PromotionGiftBrand(TableBase, table=True):
    __tablename__ = "promotion_gift_brands"

    name: str = Field(default=None)
    description: Optional[str] = Field(sa_column=Column(TEXT)) 
    

class PromotionGiftCategory(TableBase, table=True):
    __tablename__ = "promotion_gift_categories"

    name: str = Field(nullable=False, unique=True)
    # quantity: Optional[int] = Field(default=None)
    image: Optional[str] = Field(default=None)
    parent_id: Optional[int] = Field(nullable=True, default=None, foreign_key="promotion_gift_categories.id")
    

class PromotionGiftBase(TableBase, table=True):
    __tablename__ = "promotion_gifts"

    code: Optional[str] = Field(unique=True, default=None)
    name: Optional[str] = Field(default=None)
    status: Optional[GiftStatus] = Field(default=None)
    gift_category_id: Optional[int] = Field(foreign_key="promotion_gift_categories.id")
    gift_brand_id: Optional[int] = Field(foreign_key="promotion_gift_brands.id")
    price: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default='vnd')
    quantity: Optional[int] = Field(default=None)
    image: Optional[str] = Field(default=None)


#   =======================================================
#                           Coupon
#   =======================================================


class CouponDiscount(TableBase, table=True):
    __tablename__ = "coupon_discounts"

    #   Tab giam gia
    price: Optional[float] = Field(default=None)
    currency: Optional[Currency] = Field(default='vnd')
    product_id: Optional[int] = Field(foreign_key="products.id")  #  Chon giam gia ap dung bang cach lien ket


class CouponService(TableBase, table=True):
    __tablename__ = "coupon_services"

    #   Tab khuyen mai dich vu
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    product_id: Optional[int] = Field(foreign_key="products.id") #  Chon dich vu ap dung bang cach lien ket
    

class CouponInfo(TableBase, table=True):
    __tablename__ = "coupon_infos"

    title: Optional[str] = Field(default=None)
    code: Optional[str] = Field(unique=True, default=None)
    start_time: Optional[str] = Field(default=None)
    end_time: Optional[str] = Field(default=None)
    num_util: Optional[int] = Field(default=None)     #   So lan su dung
    amount: Optional[int] = Field(default=None)   #   So luong ma giam gia
    description: Optional[str] = Field(default=None)
    status: Optional[StatusEnum] = Field(default=False)
    product_id: Optional[int] = Field(foreign_key="products.id") #  Chon san pham ap dung bang cach lien ket

    
class CouponGiftBrand(TableBase, table=True):
    __tablename__ = "coupon_gift_brands"

    name: str = Field(default=None)
    description: Optional[str] = Field(sa_column=Column(TEXT)) 
    

class CouponGiftCategory(TableBase, table=True):
    __tablename__ = "coupon_gift_categories"

    name: str = Field(nullable=False, unique=True)
    quantity: Optional[int] = Field(default=None)
    image: Optional[str] = Field(default=None)
    parent_id: Optional[int] = Field(nullable=True, default=None, foreign_key="coupon_gift_categories.id")
    

class CouponGiftBase(TableBase, table=True):
    __tablename__ = "coupon_gifts"

    name: Optional[str] = Field(default=None)
    status: Optional[GiftStatus] = Field(default=None)
    gift_category_id: Optional[int] = Field(foreign_key="promotion_gift_categories.id")
    gift_brand_id: Optional[int] = Field(foreign_key="promotion_gift_brands.id")
    product_id: Optional[int] = Field(foreign_key="products.id")    #   San pham thuoc cua hang
    price: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default='vnd')
    quantity: Optional[int] = Field(default=None)
    image: Optional[str] = Field(default=None)


#   =======================================================
#                           Banner
#   =======================================================    

class Banner(TableBase, table=True):
    __tablename__ = "banners"

    title: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    page: str = Field(default=None)
    position: str = Field(default=None)
    image: str = Field(default=None)
    status: bool = Field(default=None)


#   =======================================================
#                           Company
#   =======================================================    

class Company(TableBase, table=True):
    __tablename__ = "companies"

    name: str = Field(default=None)
    address: str = Field(default=None)
    phone: str = Field(default=None)
    email: str = Field(unique=True, index=True)

class SocialMedia(TableBase, table=True):
    __tablename__ = "social_medias"

    company_id: int = Field(default=None, foreign_key="companies.id")
    name: str = Field(default=None)
    link: str = Field(sa_column=Column(TEXT)) 