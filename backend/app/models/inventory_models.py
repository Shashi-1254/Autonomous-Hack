"""
Inventory Management Models
Database models for AI-powered inventory management system
"""
from datetime import datetime, timedelta
from app import db
from sqlalchemy import JSON


class InventoryItem(db.Model):
    """Individual inventory item/product"""
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Product info
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Stock info
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(50), default='units')  # units, kg, liters, etc.
    min_stock_level = db.Column(db.Integer, default=10)
    max_stock_level = db.Column(db.Integer, default=100)
    
    # Pricing
    cost_price = db.Column(db.Float, default=0)
    selling_price = db.Column(db.Float, default=0)
    
    # Expiry tracking
    expiry_date = db.Column(db.DateTime, nullable=True)
    batch_number = db.Column(db.String(100))
    
    # Location
    warehouse_location = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_restocked_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('inventory_items', lazy='dynamic'))
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level
    
    @property
    def is_out_of_stock(self):
        return self.quantity == 0
    
    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        days_until_expiry = (self.expiry_date - datetime.utcnow()).days
        return 0 < days_until_expiry <= 7
    
    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < datetime.utcnow()
    
    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - datetime.utcnow()).days
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'description': self.description,
            'quantity': self.quantity,
            'unit': self.unit,
            'min_stock_level': self.min_stock_level,
            'max_stock_level': self.max_stock_level,
            'cost_price': self.cost_price,
            'selling_price': self.selling_price,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'days_until_expiry': self.days_until_expiry,
            'batch_number': self.batch_number,
            'warehouse_location': self.warehouse_location,
            'is_low_stock': self.is_low_stock,
            'is_out_of_stock': self.is_out_of_stock,
            'is_expiring_soon': self.is_expiring_soon,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Vendor(db.Model):
    """Vendor/Supplier information"""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    
    # Business info
    contact_person = db.Column(db.String(255))
    payment_terms = db.Column(db.String(100))  # Net 30, COD, etc.
    delivery_days = db.Column(db.Integer, default=3)  # Typical delivery time
    
    # Rating
    rating = db.Column(db.Float, default=5.0)
    total_orders = db.Column(db.Integer, default=0)
    
    # Categories they supply
    categories = db.Column(JSON, default=list)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('vendors', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'contact_person': self.contact_person,
            'payment_terms': self.payment_terms,
            'delivery_days': self.delivery_days,
            'rating': self.rating,
            'total_orders': self.total_orders,
            'categories': self.categories,
            'is_active': self.is_active
        }


class PurchaseOrder(db.Model):
    """Purchase orders for inventory restocking"""
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    
    # Order details
    order_number = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(50), default='draft')  # draft, pending_approval, approved, ordered, delivered, cancelled
    
    # Items in order (JSON array of items)
    items = db.Column(JSON, default=list)
    
    # Totals
    subtotal = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    
    # Notes
    notes = db.Column(db.Text)
    manager_notes = db.Column(db.Text)
    
    # AI-generated insights
    ai_reasoning = db.Column(db.Text)  # Why this order was suggested
    urgency_level = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    ordered_at = db.Column(db.DateTime)
    expected_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('purchase_orders', lazy='dynamic'))
    vendor = db.relationship('Vendor', backref=db.backref('orders', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'vendor': self.vendor.to_dict() if self.vendor else None,
            'items': self.items,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'total': self.total,
            'notes': self.notes,
            'manager_notes': self.manager_notes,
            'ai_reasoning': self.ai_reasoning,
            'urgency_level': self.urgency_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'expected_delivery': self.expected_delivery.isoformat() if self.expected_delivery else None
        }


class VendorQuotation(db.Model):
    """Quotations from vendors for purchase orders"""
    __tablename__ = 'vendor_quotations'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    # Quotation details
    quoted_items = db.Column(JSON, default=list)  # Items with vendor pricing
    total_price = db.Column(db.Float, default=0)
    delivery_days = db.Column(db.Integer)
    valid_until = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, selected, rejected
    
    # AI recommendation
    ai_score = db.Column(db.Float)  # AI-calculated score (0-100)
    ai_recommendation = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchase_order = db.relationship('PurchaseOrder', backref=db.backref('quotations', lazy='dynamic'))
    vendor = db.relationship('Vendor', backref=db.backref('quotations', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor.to_dict() if self.vendor else None,
            'quoted_items': self.quoted_items,
            'total_price': self.total_price,
            'delivery_days': self.delivery_days,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'status': self.status,
            'ai_score': self.ai_score,
            'ai_recommendation': self.ai_recommendation
        }


class LocalEvent(db.Model):
    """Local events and trends for demand forecasting"""
    __tablename__ = 'local_events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Event info
    name = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(100))  # festival, sports, weather, holiday, etc.
    description = db.Column(db.Text)
    
    # Location
    location = db.Column(db.String(255))
    radius_km = db.Column(db.Float, default=10)
    
    # Timing
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # Impact prediction
    expected_demand_change = db.Column(db.Float, default=0)  # Percentage change
    affected_categories = db.Column(JSON, default=list)
    
    # AI insights
    ai_insights = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'event_type': self.event_type,
            'description': self.description,
            'location': self.location,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'expected_demand_change': self.expected_demand_change,
            'affected_categories': self.affected_categories,
            'ai_insights': self.ai_insights
        }


class InventoryReport(db.Model):
    """AI-generated inventory reports"""
    __tablename__ = 'inventory_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    report_type = db.Column(db.String(50))  # stock_analysis, expiry_alert, selling_tips, trend_forecast
    title = db.Column(db.String(255))
    content = db.Column(db.Text)  # AI-generated report content
    data = db.Column(JSON)  # Structured data
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'title': self.title,
            'content': self.content,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
