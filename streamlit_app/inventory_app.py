"""
Inventory Management Streamlit App
AI-powered inventory management with multiple agents
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json

# Configuration
API_URL = "http://backend:5000/api"

# Page config
st.set_page_config(
    page_title="Smart Inventory Manager",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .alert-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .alert-critical { background: #FEE2E2; border-left: 4px solid #EF4444; }
    .alert-warning { background: #FEF3C7; border-left: 4px solid #F59E0B; }
    .alert-success { background: #D1FAE5; border-left: 4px solid #10B981; }
    .agent-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)


def get_auth_headers():
    """Get authorization headers from session"""
    token = st.session_state.get('token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def api_request(method, endpoint, data=None, params=None):
    """Make API request with error handling"""
    try:
        url = f"{API_URL}{endpoint}"
        headers = get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return None, "Invalid method"
        
        if response.status_code in [200, 201]:
            return response.json(), None
        else:
            return None, response.json().get('error', 'Request failed')
    except Exception as e:
        return None, str(e)


def render_login_form():
    """Render login form for authentication"""
    st.markdown("### 🔐 Login to Continue")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                response = requests.post(
                    f"{API_URL}/auth/login",
                    json={'email': email, 'password': password},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['token'] = data.get('access_token')
                    st.session_state['user'] = data.get('user')
                    st.rerun()
                else:
                    st.error("Login failed. Check credentials.")
            except Exception as e:
                st.error(f"Connection error: {e}")


def render_inventory_dashboard():
    """Main inventory dashboard with AI insights"""
    st.markdown('<h1 class="main-header">📦 Smart Inventory Manager</h1>', unsafe_allow_html=True)
    
    # Fetch stock analysis
    analysis, error = api_request('GET', '/inventory/analysis/stock')
    
    if error:
        st.warning(f"Could not load analysis: {error}")
        analysis = {'health_score': 0, 'total_items': 0, 'low_stock': {'count': 0}, 'out_of_stock': {'count': 0}}
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Health Score", f"{analysis.get('health_score', 0):.0f}%")
    with col2:
        st.metric("📦 Total Items", analysis.get('total_items', 0))
    with col3:
        st.metric("⚠️ Low Stock", analysis.get('low_stock', {}).get('count', 0))
    with col4:
        st.metric("🚫 Out of Stock", analysis.get('out_of_stock', {}).get('count', 0))
    
    st.divider()
    
    # AI Insights
    if analysis.get('ai_insights'):
        with st.expander("🤖 AI Insights", expanded=True):
            st.info(analysis['ai_insights'])
    
    # Low stock alerts
    low_stock_items = analysis.get('low_stock', {}).get('items', [])
    if low_stock_items:
        st.subheader("⚠️ Low Stock Alerts")
        for item in low_stock_items[:5]:
            st.markdown(f"""
            <div class="alert-card alert-warning">
                <strong>{item['name']}</strong> - Only {item['quantity']} {item.get('unit', 'units')} left 
                (Min: {item.get('min_stock_level', 10)})
            </div>
            """, unsafe_allow_html=True)
    
    # Out of stock alerts
    oos_items = analysis.get('out_of_stock', {}).get('items', [])
    if oos_items:
        st.subheader("🚫 Out of Stock")
        for item in oos_items[:5]:
            st.markdown(f"""
            <div class="alert-card alert-critical">
                <strong>{item['name']}</strong> - OUT OF STOCK - Immediate reorder needed!
            </div>
            """, unsafe_allow_html=True)


def render_inventory_list():
    """Inventory items management"""
    st.subheader("📋 Inventory Items")
    
    # Fetch items
    data, error = api_request('GET', '/inventory/items')
    
    if error:
        st.error(f"Failed to load items: {error}")
        return
    
    items = data.get('items', [])
    
    # Add new item form
    with st.expander("➕ Add New Item"):
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Product Name*")
                category = st.selectbox("Category", ["Groceries", "Beverages", "Dairy", "Snacks", "Personal Care", "Household", "Other"])
                quantity = st.number_input("Quantity", min_value=0, value=0)
            with col2:
                cost_price = st.number_input("Cost Price", min_value=0.0, value=0.0)
                selling_price = st.number_input("Selling Price", min_value=0.0, value=0.0)
                expiry_date = st.date_input("Expiry Date (optional)", value=None)
            
            if st.form_submit_button("Add Item"):
                item_data = {
                    'name': name,
                    'category': category,
                    'quantity': quantity,
                    'cost_price': cost_price,
                    'selling_price': selling_price,
                    'expiry_date': expiry_date.isoformat() if expiry_date else None
                }
                result, err = api_request('POST', '/inventory/items', item_data)
                if err:
                    st.error(f"Failed: {err}")
                else:
                    st.success("Item added!")
                    st.rerun()
    
    # Display items table
    if items:
        df = pd.DataFrame(items)
        display_cols = ['name', 'category', 'quantity', 'unit', 'selling_price', 'is_low_stock', 'days_until_expiry']
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
    else:
        st.info("No inventory items yet. Add some items to get started!")


def render_expiry_management():
    """Expiry tracking and selling tips"""
    st.subheader("📅 Expiry Management")
    
    # Fetch expiry analysis
    data, error = api_request('GET', '/inventory/analysis/expiry')
    
    if error:
        st.error(f"Failed to load expiry data: {error}")
        return
    
    # Expiry metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        expired = data.get('expired', {}).get('count', 0)
        st.metric("🚨 Expired", expired, delta=None if expired == 0 else f"-{expired} remove")
    with col2:
        soon = data.get('expiring_soon', {}).get('count', 0)
        st.metric("⏰ Expiring Soon (7 days)", soon)
    with col3:
        month = data.get('expiring_month', {}).get('count', 0)
        st.metric("📆 Expiring This Month", month)
    
    # Expired items
    expired_items = data.get('expired', {}).get('items', [])
    if expired_items:
        st.error("🚨 EXPIRED ITEMS - Remove Immediately!")
        for item in expired_items:
            st.write(f"- **{item['name']}** - Expired {abs(item['days_until_expiry'])} days ago")
    
    # Expiring soon with selling tips
    expiring_soon = data.get('expiring_soon', {}).get('items', [])
    if expiring_soon:
        st.warning("⏰ Expiring Soon - Take Action!")
        for item in expiring_soon:
            st.write(f"- **{item['name']}** - {item['days_until_expiry']} days left")
    
    # AI Selling Tips
    tips = data.get('selling_tips', [])
    if tips:
        st.subheader("💡 AI Selling Tips")
        for tip in tips:
            if isinstance(tip, dict) and 'item_name' in tip:
                st.markdown(f"""
                <div class="agent-card">
                    <h4>📦 {tip.get('item_name', 'Product')}</h4>
                    <p>💰 <strong>Discount:</strong> {tip.get('discount_percent', 10)}% off</p>
                    <p>🎁 <strong>Bundle:</strong> {tip.get('bundle_suggestion', 'N/A')}</p>
                    <p>📢 <strong>Message:</strong> {tip.get('marketing_message', 'Limited time offer!')}</p>
                </div>
                """, unsafe_allow_html=True)


def render_order_management():
    """Purchase order management"""
    st.subheader("🛒 Purchase Orders")
    
    tab1, tab2, tab3 = st.tabs(["📝 Generate Order", "📋 Order List", "✅ Pending Approval"])
    
    with tab1:
        st.markdown("### AI Order Suggestions")
        if st.button("🤖 Generate Smart Order"):
            with st.spinner("Analyzing inventory..."):
                data, error = api_request('GET', '/inventory/orders/suggest')
            
            if error:
                st.error(f"Failed: {error}")
            else:
                st.success(f"Found {data.get('total_items', 0)} items to reorder")
                
                if data.get('ai_reasoning'):
                    st.info(f"🤖 AI Reasoning: {data['ai_reasoning']}")
                
                items = data.get('suggested_items', [])
                if items:
                    st.dataframe(pd.DataFrame(items), use_container_width=True)
                    
                    if st.button("📦 Create Purchase Order"):
                        order_data = {
                            'items': items,
                            'total': data.get('estimated_total_cost', 0),
                            'ai_reasoning': data.get('ai_reasoning')
                        }
                        result, err = api_request('POST', '/inventory/orders', order_data)
                        if err:
                            st.error(f"Failed: {err}")
                        else:
                            st.success("Order created!")
    
    with tab2:
        orders_data, err = api_request('GET', '/inventory/orders')
        if not err:
            orders = orders_data.get('orders', [])
            if orders:
                for order in orders:
                    with st.expander(f"Order #{order['order_number']} - {order['status'].upper()}"):
                        st.write(f"**Status:** {order['status']}")
                        st.write(f"**Total:** ${order.get('total', 0):.2f}")
                        st.write(f"**Created:** {order.get('created_at', 'N/A')}")
                        
                        if order['status'] == 'draft':
                            if st.button(f"Submit for Approval", key=f"submit_{order['id']}"):
                                api_request('POST', f"/inventory/orders/{order['id']}/submit")
                                st.rerun()
            else:
                st.info("No orders yet")
    
    with tab3:
        pending_data, err = api_request('GET', '/inventory/orders', params={'status': 'pending_approval'})
        if not err:
            pending = pending_data.get('orders', [])
            if pending:
                for order in pending:
                    with st.container():
                        st.markdown(f"### Order #{order['order_number']}")
                        st.write(f"**Total:** ${order.get('total', 0):.2f}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Approve", key=f"approve_{order['id']}"):
                                api_request('POST', f"/inventory/orders/{order['id']}/approve")
                                st.rerun()
                        with col2:
                            if st.button("❌ Reject", key=f"reject_{order['id']}"):
                                st.warning("Order rejected")
            else:
                st.success("No pending approvals")


def render_vendor_quotations():
    """Vendor quotation management"""
    st.subheader("🏪 Vendor Quotations")
    
    # Get approved orders
    orders_data, err = api_request('GET', '/inventory/orders', params={'status': 'approved'})
    
    if err:
        st.error(f"Failed to load: {err}")
        return
    
    orders = orders_data.get('orders', [])
    
    if not orders:
        st.info("No approved orders waiting for quotations")
        return
    
    for order in orders:
        with st.expander(f"Order #{order['order_number']} - ${order.get('total', 0):.2f}"):
            # Request quotations button
            if st.button(f"📨 Request Quotations", key=f"req_{order['id']}"):
                result, err = api_request('POST', f"/inventory/orders/{order['id']}/quotations/request")
                if err:
                    st.error(f"Failed: {err}")
                else:
                    st.success("Quotations requested from vendors!")
                    st.rerun()
            
            # Show existing quotations
            quotes_data, err = api_request('GET', f"/inventory/orders/{order['id']}/quotations")
            if not err:
                quotations = quotes_data.get('quotations', [])
                evaluation = quotes_data.get('evaluation', {})
                
                if quotations:
                    st.markdown("### 📊 Quotation Comparison")
                    
                    # Show AI recommendation
                    if evaluation.get('ai_recommendation'):
                        st.info(f"🤖 AI Recommendation: {evaluation['ai_recommendation']}")
                    
                    # Quotations table
                    for q in quotations:
                        vendor = q.get('vendor', {})
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                            with col1:
                                st.write(f"**{vendor.get('name', 'Unknown Vendor')}**")
                            with col2:
                                st.write(f"${q.get('total_price', 0):.2f}")
                            with col3:
                                st.write(f"{q.get('delivery_days', 'N/A')} days")
                            with col4:
                                if q.get('status') == 'pending':
                                    if st.button("Select", key=f"select_{q['id']}"):
                                        api_request('POST', f"/inventory/quotations/{q['id']}/select")
                                        st.rerun()


def render_local_trends():
    """Local trends and event analysis"""
    st.subheader("📈 Local Trends & Events")
    
    location = st.text_input("Store Location", value="Mumbai, India")
    
    if st.button("🔍 Analyze Local Trends"):
        with st.spinner("Analyzing local events and trends..."):
            data, error = api_request('GET', '/inventory/analysis/trends', params={'location': location, 'days': 30})
        
        if error:
            st.error(f"Failed: {error}")
        else:
            events = data.get('events', [])
            forecast = data.get('demand_forecast', {})
            
            st.markdown("### 📅 Upcoming Events")
            for event in events:
                impact_color = {'high': '🔴', 'very_high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(event.get('impact', 'low'), '⚪')
                st.markdown(f"""
                <div class="agent-card">
                    <h4>{impact_color} {event['name']}</h4>
                    <p><strong>Type:</strong> {event.get('type', 'General')}</p>
                    <p><strong>Expected Demand Change:</strong> +{event.get('expected_demand_change', 0)}%</p>
                    <p><strong>Affected Categories:</strong> {', '.join(event.get('affected_categories', []))}</p>
                </div>
                """, unsafe_allow_html=True)
            
            if forecast:
                st.markdown("### 🔮 Demand Forecast")
                if 'overall_change_percent' in forecast:
                    st.metric("Expected Demand Change", f"+{forecast['overall_change_percent']}%")
                if 'top_categories' in forecast:
                    st.write("**Top Categories to Stock:**", ', '.join(forecast['top_categories']))
                if 'recommendations' in forecast:
                    st.write("**Recommendations:**")
                    for rec in forecast['recommendations']:
                        st.write(f"- {rec}")


def main():
    """Main app entry point"""
    # Check authentication
    if not st.session_state.get('token'):
        render_login_form()
        return
    
    # Sidebar navigation
    st.sidebar.title("🏪 Inventory Manager")
    st.sidebar.markdown(f"Welcome, **{st.session_state.get('user', {}).get('name', 'User')}**")
    
    page = st.sidebar.radio(
        "Navigate",
        ["📊 Dashboard", "📦 Inventory", "📅 Expiry Management", "🛒 Orders", "🏪 Vendor Quotes", "📈 Local Trends"]
    )
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.caption("Powered by AI Agents")
    
    # Render selected page
    if page == "📊 Dashboard":
        render_inventory_dashboard()
    elif page == "📦 Inventory":
        render_inventory_list()
    elif page == "📅 Expiry Management":
        render_expiry_management()
    elif page == "🛒 Orders":
        render_order_management()
    elif page == "🏪 Vendor Quotes":
        render_vendor_quotations()
    elif page == "📈 Local Trends":
        render_local_trends()


if __name__ == "__main__":
    main()
