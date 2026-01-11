"""
Demo Script - Add sample inventory data and test agents
Run this to see the AI agents in action!
"""
import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
from app import create_app, db
from app.models.inventory_models import InventoryItem, Vendor, PurchaseOrder
from app.services.inventory_agent_service import get_inventory_agent_service

def add_sample_data(user_id=1):
    """Add sample inventory items"""
    
    # Sample inventory items with various stock levels and expiry dates
    sample_items = [
        # Low stock items
        {'name': 'Milk 1L', 'category': 'Dairy', 'quantity': 5, 'min_stock_level': 20, 'selling_price': 60, 
         'expiry_date': datetime.utcnow() + timedelta(days=3)},
        {'name': 'Bread', 'category': 'Bakery', 'quantity': 3, 'min_stock_level': 15, 'selling_price': 40,
         'expiry_date': datetime.utcnow() + timedelta(days=2)},
        {'name': 'Eggs (12 pack)', 'category': 'Dairy', 'quantity': 8, 'min_stock_level': 25, 'selling_price': 90,
         'expiry_date': datetime.utcnow() + timedelta(days=10)},
         
        # Out of stock items
        {'name': 'Butter 500g', 'category': 'Dairy', 'quantity': 0, 'min_stock_level': 10, 'selling_price': 250,
         'expiry_date': datetime.utcnow() + timedelta(days=30)},
        {'name': 'Cheese Slice', 'category': 'Dairy', 'quantity': 0, 'min_stock_level': 15, 'selling_price': 150,
         'expiry_date': datetime.utcnow() + timedelta(days=20)},
         
        # Expiring soon items
        {'name': 'Yogurt Cup', 'category': 'Dairy', 'quantity': 50, 'min_stock_level': 20, 'selling_price': 30,
         'expiry_date': datetime.utcnow() + timedelta(days=1)},  # Expires tomorrow!
        {'name': 'Fresh Juice', 'category': 'Beverages', 'quantity': 25, 'min_stock_level': 10, 'selling_price': 80,
         'expiry_date': datetime.utcnow() + timedelta(days=4)},
         
        # Expired items
        {'name': 'Cream Cake', 'category': 'Bakery', 'quantity': 3, 'min_stock_level': 5, 'selling_price': 350,
         'expiry_date': datetime.utcnow() - timedelta(days=1)},  # Already expired!
         
        # Healthy stock items
        {'name': 'Rice 5kg', 'category': 'Groceries', 'quantity': 40, 'min_stock_level': 15, 'selling_price': 350},
        {'name': 'Cooking Oil 1L', 'category': 'Groceries', 'quantity': 30, 'min_stock_level': 10, 'selling_price': 180},
        {'name': 'Sugar 1kg', 'category': 'Groceries', 'quantity': 50, 'min_stock_level': 20, 'selling_price': 50},
        {'name': 'Chips Pack', 'category': 'Snacks', 'quantity': 100, 'min_stock_level': 30, 'selling_price': 30,
         'expiry_date': datetime.utcnow() + timedelta(days=60)},
        {'name': 'Soft Drinks', 'category': 'Beverages', 'quantity': 80, 'min_stock_level': 25, 'selling_price': 40,
         'expiry_date': datetime.utcnow() + timedelta(days=90)},
    ]
    
    print("\n📦 Adding sample inventory items...")
    for item_data in sample_items:
        item = InventoryItem(
            user_id=user_id,
            name=item_data['name'],
            category=item_data['category'],
            quantity=item_data['quantity'],
            min_stock_level=item_data['min_stock_level'],
            max_stock_level=item_data.get('max_stock_level', 100),
            selling_price=item_data['selling_price'],
            cost_price=item_data['selling_price'] * 0.7,  # 30% margin
            expiry_date=item_data.get('expiry_date'),
            unit='units'
        )
        db.session.add(item)
    
    # Add sample vendors
    vendors = [
        {'name': 'Fresh Foods Ltd', 'email': 'orders@freshfoods.com', 'categories': ['Dairy', 'Bakery'], 'delivery_days': 2, 'rating': 4.5},
        {'name': 'Grocery Wholesale', 'email': 'supply@grocerywholesale.com', 'categories': ['Groceries', 'Snacks'], 'delivery_days': 3, 'rating': 4.2},
        {'name': 'Beverage Distributors', 'email': 'sales@bevdist.com', 'categories': ['Beverages'], 'delivery_days': 1, 'rating': 4.8},
    ]
    
    print("🏪 Adding sample vendors...")
    for v in vendors:
        vendor = Vendor(
            user_id=user_id,
            name=v['name'],
            email=v['email'],
            categories=v['categories'],
            delivery_days=v['delivery_days'],
            rating=v['rating']
        )
        db.session.add(vendor)
    
    db.session.commit()
    print("✅ Sample data added!\n")


def demo_agents():
    """Demonstrate all AI agents"""
    
    # Get all items
    items = InventoryItem.query.all()
    items_data = [item.to_dict() for item in items]
    
    if not items_data:
        print("❌ No inventory items found. Run add_sample_data() first.")
        return
    
    agent = get_inventory_agent_service()
    
    print("=" * 60)
    print("🤖 AI INVENTORY AGENTS DEMO")
    print("=" * 60)
    
    # Agent 1: Stock Analysis
    print("\n" + "─" * 60)
    print("🔍 AGENT 1: STOCK ANALYSIS")
    print("─" * 60)
    stock_analysis = agent.analyze_stock(items_data)
    print(f"📊 Health Score: {stock_analysis['health_score']}%")
    print(f"📦 Total Items: {stock_analysis['total_items']}")
    print(f"⚠️ Low Stock: {stock_analysis['low_stock']['count']} items")
    print(f"🚫 Out of Stock: {stock_analysis['out_of_stock']['count']} items")
    
    if stock_analysis['low_stock']['items']:
        print("\n⚠️ Low Stock Items:")
        for item in stock_analysis['low_stock']['items']:
            print(f"   - {item['name']}: {item['quantity']} left (min: {item['min_stock_level']})")
    
    if stock_analysis['out_of_stock']['items']:
        print("\n🚫 Out of Stock Items:")
        for item in stock_analysis['out_of_stock']['items']:
            print(f"   - {item['name']}: NEEDS IMMEDIATE RESTOCK!")
    
    if stock_analysis.get('ai_insights'):
        print(f"\n🤖 AI Insights:\n{stock_analysis['ai_insights']}")
    
    # Agent 2: Expiry Analysis
    print("\n" + "─" * 60)
    print("📅 AGENT 2: EXPIRY PREDICTION")
    print("─" * 60)
    expiry_analysis = agent.analyze_expiry(items_data)
    print(f"🚨 Expired: {expiry_analysis['expired']['count']} items")
    print(f"⏰ Expiring Soon (7 days): {expiry_analysis['expiring_soon']['count']} items")
    print(f"📆 Expiring This Month: {expiry_analysis['expiring_month']['count']} items")
    
    if expiry_analysis['expired']['items']:
        print("\n🚨 EXPIRED - Remove Immediately:")
        for item in expiry_analysis['expired']['items']:
            print(f"   - {item['name']}: Expired {abs(item['days_until_expiry'])} days ago!")
    
    if expiry_analysis['expiring_soon']['items']:
        print("\n⏰ Expiring Soon - Take Action:")
        for item in expiry_analysis['expiring_soon']['items']:
            print(f"   - {item['name']}: {item['days_until_expiry']} days left")
    
    if expiry_analysis.get('selling_tips'):
        print("\n💡 AI Selling Tips:")
        for tip in expiry_analysis['selling_tips'][:3]:
            if isinstance(tip, dict) and 'item_name' in tip:
                print(f"   📦 {tip.get('item_name', 'Product')}")
                print(f"      💰 Discount: {tip.get('discount_percent', 10)}%")
                print(f"      📢 Message: {tip.get('marketing_message', 'Special offer!')}")
    
    # Agent 3: Order Generation
    print("\n" + "─" * 60)
    print("🛒 AGENT 3: ORDER GENERATION")
    print("─" * 60)
    order_suggestion = agent.generate_order_suggestions(items_data)
    print(f"📝 Items to Order: {order_suggestion['total_items']}")
    print(f"🔴 Critical: {order_suggestion['critical_count']}")
    print(f"🟠 High Priority: {order_suggestion['high_priority_count']}")
    print(f"💰 Estimated Cost: ₹{order_suggestion['estimated_total_cost']:.2f}")
    
    if order_suggestion['suggested_items']:
        print("\n📋 Suggested Order:")
        for item in order_suggestion['suggested_items'][:5]:
            urgency_emoji = {'critical': '🔴', 'high': '🟠', 'normal': '🟢'}.get(item['urgency'], '⚪')
            print(f"   {urgency_emoji} {item['item_name']}: Order {item['order_quantity']} {item['unit']}")
    
    if order_suggestion.get('ai_reasoning'):
        print(f"\n🤖 AI Reasoning:\n{order_suggestion['ai_reasoning']}")
    
    # Agent 5: Local Trends
    print("\n" + "─" * 60)
    print("📈 AGENT 5: LOCAL TRENDS")
    print("─" * 60)
    trends = agent.analyze_local_trends("Mumbai, India", 30)
    print(f"📍 Location: {trends['location']}")
    print(f"📅 Looking ahead: {trends['date_range_days']} days")
    print(f"🎉 Upcoming Events: {trends['total_events']}")
    
    for event in trends.get('events', [])[:3]:
        impact_emoji = {'high': '🔴', 'very_high': '🔴', 'medium': '🟡'}.get(event.get('impact', ''), '🟢')
        print(f"\n   {impact_emoji} {event['name']}")
        print(f"      Type: {event.get('type', 'N/A')}")
        print(f"      Demand Change: +{event.get('expected_demand_change', 0)}%")
        print(f"      Affected: {', '.join(event.get('affected_categories', []))}")
    
    print("\n" + "=" * 60)
    print("✅ AGENT DEMO COMPLETE!")
    print("=" * 60)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Check if we need to add sample data
        existing = InventoryItem.query.count()
        if existing == 0:
            add_sample_data(user_id=1)
        else:
            print(f"📦 Found {existing} existing items")
        
        # Run agent demo
        demo_agents()
