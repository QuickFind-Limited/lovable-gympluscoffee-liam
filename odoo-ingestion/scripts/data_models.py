#!/usr/bin/env python3
"""
Odoo Data Models
===============

Defines data structures for Odoo models including products,
partners, sales orders, and inventory management.

Agent: Data Structure Specialist
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class ProductType(Enum):
    """Product types supported by Odoo"""
    STOCKABLE = 'product'
    CONSUMABLE = 'consu'
    SERVICE = 'service'


class OrderState(Enum):
    """Sales order states"""
    DRAFT = 'draft'
    SENT = 'sent'
    SALE = 'sale'
    DONE = 'done'
    CANCEL = 'cancel'


class PartnerType(Enum):
    """Partner types"""
    PERSON = 'person'
    COMPANY = 'company'


@dataclass
class ProductCategory:
    """Product category data structure"""
    name: str
    parent_id: Optional[int] = None
    parent_path: Optional[str] = None
    complete_name: Optional[str] = None
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'name': self.name,
        }
        
        if self.parent_id:
            vals['parent_id'] = self.parent_id
            
        return vals


@dataclass
class ProductAttribute:
    """Product attribute (color, size, etc.)"""
    name: str
    display_type: str = 'select'  # select, radio, color
    create_variant: bool = True
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'display_type': self.display_type,
            'create_variant': self.create_variant
        }


@dataclass
class ProductAttributeValue:
    """Product attribute value"""
    name: str
    attribute_id: int
    sequence: int = 10
    color: int = 0  # Color index for color attributes
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'attribute_id': self.attribute_id,
            'sequence': self.sequence,
            'color': self.color
        }


@dataclass
class ProductTemplate:
    """
    Product Template (parent of variants)
    ===================================
    
    Represents the main product with common attributes
    shared across all variants.
    """
    name: str
    categ_id: int
    type: ProductType = ProductType.STOCKABLE
    list_price: float = 0.0
    standard_price: float = 0.0
    sale_ok: bool = True
    purchase_ok: bool = True
    active: bool = True
    default_code: Optional[str] = None
    description: Optional[str] = None
    description_purchase: Optional[str] = None
    description_sale: Optional[str] = None
    weight: float = 0.0
    volume: float = 0.0
    warranty: float = 0.0
    sale_line_warn: str = 'no-message'
    purchase_line_warn: str = 'no-message'
    invoice_policy: str = 'order'  # order or delivery
    purchase_method: str = 'purchase'  # purchase or receive
    
    # Inventory settings
    tracking: str = 'none'  # none, lot, serial
    
    # Attributes for variants
    attribute_line_ids: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'name': self.name,
            'categ_id': self.categ_id,
            'type': self.type.value,
            'list_price': self.list_price,
            'standard_price': self.standard_price,
            'sale_ok': self.sale_ok,
            'purchase_ok': self.purchase_ok,
            'active': self.active,
            'weight': self.weight,
            'volume': self.volume,
            'warranty': self.warranty,
            'sale_line_warn': self.sale_line_warn,
            'purchase_line_warn': self.purchase_line_warn,
            'invoice_policy': self.invoice_policy,
            'purchase_method': self.purchase_method,
            'tracking': self.tracking,
        }
        
        # Add optional fields
        if self.default_code:
            vals['default_code'] = self.default_code
        if self.description:
            vals['description'] = self.description
        if self.description_purchase:
            vals['description_purchase'] = self.description_purchase
        if self.description_sale:
            vals['description_sale'] = self.description_sale
        
        # Add attribute lines for variants
        if self.attribute_line_ids:
            vals['attribute_line_ids'] = self.attribute_line_ids
            
        return vals
    
    @classmethod
    def from_json_data(cls, data: Dict[str, Any], category_id: int) -> 'ProductTemplate':
        """Create ProductTemplate from JSON product data"""
        return cls(
            name=data['name'],
            categ_id=category_id,
            type=ProductType.STOCKABLE,
            list_price=float(data.get('list_price', 0.0)),
            standard_price=float(data.get('standard_cost', 0.0)),
            default_code=data.get('sku', ''),
            description=data.get('description', ''),
            active=data.get('status', 'active') == 'active'
        )


@dataclass
class ProductVariant:
    """
    Product Variant (specific combination)
    ====================================
    
    Represents a specific variant of a product template
    with unique attributes (color, size, etc.).
    """
    product_tmpl_id: int
    default_code: str  # SKU
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    active: bool = True
    
    # Variant-specific attributes
    product_template_attribute_value_ids: List[int] = field(default_factory=list)
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'product_tmpl_id': self.product_tmpl_id,
            'default_code': self.default_code,
            'active': self.active,
        }
        
        # Add optional fields
        if self.list_price is not None:
            vals['list_price'] = self.list_price
        if self.standard_price is not None:
            vals['standard_price'] = self.standard_price
        if self.weight is not None:
            vals['weight'] = self.weight
        if self.volume is not None:
            vals['volume'] = self.volume
            
        # Add attribute values
        if self.product_template_attribute_value_ids:
            vals['product_template_attribute_value_ids'] = [
                (6, 0, self.product_template_attribute_value_ids)
            ]
            
        return vals


@dataclass
class Partner:
    """
    Partner (Customer/Supplier)
    ==========================
    
    Represents business partners including customers,
    suppliers, and general contacts.
    """
    name: str
    is_company: bool = False
    partner_type: PartnerType = PartnerType.PERSON
    customer_rank: int = 0
    supplier_rank: int = 0
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    website: Optional[str] = None
    
    # Address information
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = None
    zip: Optional[str] = None
    country_id: Optional[int] = None
    
    # Business information
    vat: Optional[str] = None  # Tax ID
    ref: Optional[str] = None  # Internal reference
    category_id: List[int] = field(default_factory=list)
    
    # Settings
    active: bool = True
    lang: str = 'en_US'
    tz: Optional[str] = None
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'name': self.name,
            'is_company': self.is_company,
            'customer_rank': self.customer_rank,
            'supplier_rank': self.supplier_rank,
            'active': self.active,
            'lang': self.lang,
        }
        
        # Add contact information
        for field_name in ['email', 'phone', 'mobile', 'website']:
            value = getattr(self, field_name)
            if value:
                vals[field_name] = value
        
        # Add address information  
        for field_name in ['street', 'street2', 'city', 'state_id', 'zip', 'country_id']:
            value = getattr(self, field_name)
            if value:
                vals[field_name] = value
        
        # Add business information
        for field_name in ['vat', 'ref', 'tz']:
            value = getattr(self, field_name)
            if value:
                vals[field_name] = value
                
        # Add categories
        if self.category_id:
            vals['category_id'] = [(6, 0, self.category_id)]
            
        return vals
    
    @classmethod
    def from_json_data(cls, data: Dict[str, Any]) -> 'Partner':
        """Create Partner from JSON data"""
        return cls(
            name=data['name'],
            is_company=data.get('is_company', False),
            customer_rank=1 if data.get('is_customer', True) else 0,
            supplier_rank=1 if data.get('is_supplier', False) else 0,
            email=data.get('email'),
            phone=data.get('phone'),
            street=data.get('street'),
            city=data.get('city'),
            zip=data.get('zip'),
            country_id=data.get('country_id')
        )


@dataclass
class SaleOrderLine:
    """Sales order line item"""
    product_id: int
    name: str
    product_uom_qty: float = 1.0
    price_unit: float = 0.0
    discount: float = 0.0
    tax_id: List[int] = field(default_factory=list)
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'product_id': self.product_id,
            'name': self.name,
            'product_uom_qty': self.product_uom_qty,
            'price_unit': self.price_unit,
            'discount': self.discount,
        }
        
        if self.tax_id:
            vals['tax_id'] = [(6, 0, self.tax_id)]
            
        return vals


@dataclass
class SaleOrder:
    """
    Sales Order
    ==========
    
    Represents customer orders with line items
    and delivery information.
    """
    partner_id: int
    date_order: datetime
    state: OrderState = OrderState.DRAFT
    
    # Order information
    client_order_ref: Optional[str] = None  # Customer reference
    validity_date: Optional[datetime] = None
    
    # Delivery information
    partner_invoice_id: Optional[int] = None
    partner_shipping_id: Optional[int] = None
    
    # Financial information
    pricelist_id: Optional[int] = None
    currency_id: Optional[int] = None
    payment_term_id: Optional[int] = None
    
    # Order lines
    order_line: List[SaleOrderLine] = field(default_factory=list)
    
    # Notes
    note: Optional[str] = None
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'partner_id': self.partner_id,
            'date_order': self.date_order.strftime('%Y-%m-%d %H:%M:%S'),
            'state': self.state.value,
        }
        
        # Add optional fields
        optional_fields = [
            'client_order_ref', 'partner_invoice_id', 'partner_shipping_id',
            'pricelist_id', 'currency_id', 'payment_term_id', 'note'
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value:
                vals[field_name] = value
        
        # Add validity date
        if self.validity_date:
            vals['validity_date'] = self.validity_date.strftime('%Y-%m-%d')
        
        # Add order lines
        if self.order_line:
            vals['order_line'] = [
                (0, 0, line.to_odoo_vals()) for line in self.order_line
            ]
            
        return vals
    
    @classmethod
    def from_json_data(cls, data: Dict[str, Any], partner_id: int) -> 'SaleOrder':
        """Create SaleOrder from JSON data"""
        order = cls(
            partner_id=partner_id,
            date_order=datetime.fromisoformat(data.get('date_order', datetime.now().isoformat())),
            client_order_ref=data.get('order_reference'),
            note=data.get('notes')
        )
        
        # Add order lines
        for line_data in data.get('order_lines', []):
            line = SaleOrderLine(
                product_id=line_data['product_id'],
                name=line_data.get('description', ''),
                product_uom_qty=float(line_data.get('quantity', 1)),
                price_unit=float(line_data.get('price_unit', 0)),
                discount=float(line_data.get('discount', 0))
            )
            order.order_line.append(line)
            
        return order


@dataclass
class StockMove:
    """
    Stock Movement
    =============
    
    Represents inventory movements for stock management.
    """
    name: str
    product_id: int
    product_uom_qty: float
    location_id: int
    location_dest_id: int
    picking_id: Optional[int] = None
    origin: Optional[str] = None
    date: Optional[datetime] = None
    
    def to_odoo_vals(self) -> Dict[str, Any]:
        """Convert to Odoo values dictionary"""
        vals = {
            'name': self.name,
            'product_id': self.product_id,
            'product_uom_qty': self.product_uom_qty,
            'location_id': self.location_id,
            'location_dest_id': self.location_dest_id,
        }
        
        if self.picking_id:
            vals['picking_id'] = self.picking_id
        if self.origin:
            vals['origin'] = self.origin
        if self.date:
            vals['date'] = self.date.strftime('%Y-%m-%d %H:%M:%S')
            
        return vals


@dataclass
class ImportProgress:
    """
    Import Progress Tracking
    =======================
    
    Tracks the progress of data import operations.
    """
    operation_id: str
    operation_type: str  # 'products', 'partners', 'orders'
    start_time: datetime
    end_time: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    error_records: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def is_completed(self) -> bool:
        """Check if import is completed"""
        return self.end_time is not None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_records == 0:
            return 0.0
        return (self.successful_records / self.processed_records) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'progress_percentage': self.progress_percentage,
            'success_rate': self.success_rate,
            'error_records': self.error_records
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImportProgress':
        """Create ImportProgress from dictionary"""
        return cls(
            operation_id=data['operation_id'],
            operation_type=data['operation_type'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            total_records=data.get('total_records', 0),
            processed_records=data.get('processed_records', 0),
            successful_records=data.get('successful_records', 0),
            failed_records=data.get('failed_records', 0),
            error_records=data.get('error_records', [])
        )