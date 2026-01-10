"""
InferX-ML Streamlit Application
Dynamic model loading and prediction UI
"""
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import io
import joblib
import tempfile
import requests
from typing import Dict, Any, Optional

# Page configuration
st.set_page_config(
    page_title="InferX-ML Predictions",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API URL - internal Docker network
API_URL = os.environ.get('API_URL', 'http://backend:5000/api')
INTERNAL_SECRET = os.environ.get('INTERNAL_API_SECRET', 'inferx-internal-2024')

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #f97316;
        text-align: center;
        margin-bottom: 1rem;
    }
    .prediction-result {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        margin: 1rem 0;
    }
    .confidence-badge {
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-weight: bold;
        background-color: #f97316;
        color: white;
    }
    .stButton>button:hover {
        background-color: #ea580c;
    }
</style>
""", unsafe_allow_html=True)


def get_model_id_from_url():
    """Get model ID from URL query parameters"""
    # Use experimental API for compatibility with older Streamlit versions
    try:
        params = st.query_params
        return params.get('model', None)
    except AttributeError:
        # Fallback for older Streamlit versions
        params = st.experimental_get_query_params()
        model_list = params.get('model', [])
        return model_list[0] if model_list else None


def load_model_from_minio(model_id: int):
    """Load model and schema from MinIO via internal API"""
    try:
        # Use internal endpoint (no JWT required)
        headers = {'X-Internal-Secret': INTERNAL_SECRET}
        response = requests.get(
            f"{API_URL}/models/internal/{model_id}/download", 
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            return None, None, None, f"Failed to load model: {response.status_code}"
        
        # Extract ZIP in memory
        import zipfile
        zip_buffer = io.BytesIO(response.content)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Load model
            model_path = os.path.join(temp_dir, 'model.pkl')
            model = joblib.load(model_path) if os.path.exists(model_path) else None
            
            # Load preprocessor
            preprocessor_path = os.path.join(temp_dir, 'preprocessor.pkl')
            preprocessor = joblib.load(preprocessor_path) if os.path.exists(preprocessor_path) else None
            
            # Load UI schema
            schema_path = os.path.join(temp_dir, 'ui_schema.json')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    schema = json.load(f)
            else:
                schema = None
            
            # Load model info
            info_path = os.path.join(temp_dir, 'model_info.json')
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    model_info = json.load(f)
            else:
                model_info = {}
            
            return model, preprocessor, schema, model_info
            
    except Exception as e:
        return None, None, None, str(e)


def fetch_models_list():
    """Fetch available models from internal API"""
    try:
        headers = {'X-Internal-Secret': INTERNAL_SECRET}
        response = requests.get(f"{API_URL}/models/internal/list", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('models', [])
    except:
        pass
    return []


def generate_form_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Streamlit form elements from UI schema"""
    form_values = {}
    
    if not schema or 'fields' not in schema:
        return form_values
    
    fields = schema.get('fields', [])
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    for i, field in enumerate(fields):
        name = field['name']
        label = field.get('label', name.replace('_', ' ').title())
        input_type = field.get('input_type', 'text')
        
        # Alternate between columns
        with col1 if i % 2 == 0 else col2:
            if input_type == 'number':
                min_val = field.get('min', 0.0)
                max_val = field.get('max', 1000.0)
                default_val = field.get('default', min_val)
                
                # Ensure values are valid floats
                try:
                    min_val = float(min_val) if min_val is not None else 0.0
                    max_val = float(max_val) if max_val is not None else 1000.0
                    default_val = float(default_val) if default_val is not None else min_val
                    default_val = max(min_val, min(max_val, default_val))
                except:
                    min_val, max_val, default_val = 0.0, 1000.0, 0.0
                
                form_values[name] = st.number_input(
                    label,
                    min_value=min_val,
                    max_value=max_val,
                    value=default_val,
                    key=f"field_{name}"
                )
            
            elif input_type == 'dropdown':
                options = field.get('options', [])
                if options:
                    form_values[name] = st.selectbox(label, options, key=f"field_{name}")
                else:
                    form_values[name] = st.text_input(label, key=f"field_{name}")
            
            elif input_type == 'slider':
                min_val = field.get('min', 0)
                max_val = field.get('max', 100)
                default_val = field.get('default', 50)
                form_values[name] = st.slider(
                    label,
                    min_value=int(min_val),
                    max_value=int(max_val),
                    value=int(default_val),
                    key=f"field_{name}"
                )
            
            elif input_type == 'checkbox':
                form_values[name] = st.checkbox(label, value=field.get('default', False), key=f"field_{name}")
            
            else:  # text input
                form_values[name] = st.text_input(label, value=str(field.get('default', '')), key=f"field_{name}")
    
    return form_values


def main():
    """Main application entry point"""
    
    # Get model ID from URL or show selector
    model_id = get_model_id_from_url()
    
    st.markdown('<h1 class="main-header">🤖 Make Predictions</h1>', unsafe_allow_html=True)
    
    # If no model ID in URL, show model selector
    if not model_id:
        st.info("Select a model to make predictions")
        models = fetch_models_list()
        
        if models:
            model_names = {str(m['id']): m['name'] for m in models if m.get('has_package')}
            if model_names:
                selected = st.selectbox(
                    "Choose Model",
                    options=list(model_names.keys()),
                    format_func=lambda x: model_names[x]
                )
                if st.button("Load Model"):
                    try:
                        st.query_params['model'] = selected
                    except AttributeError:
                        st.experimental_set_query_params(model=selected)
                    st.rerun()
            else:
                st.warning("No models with prediction packages available. Train a new model first.")
        else:
            st.warning("No models available. Train your first model to get started!")
        return
    
    # Load model
    with st.spinner("Loading model..."):
        result = load_model_from_minio(model_id)
        
        if isinstance(result[-1], str) and 'Failed' in result[-1]:
            st.error(result[-1])
            if st.button("Back to Model Selection"):
                try:
                    st.query_params.clear()
                except AttributeError:
                    st.experimental_set_query_params()
                st.rerun()
            return
        
        model, preprocessor, schema, model_info = result
    
    if model is None:
        st.error("Failed to load model. The model package may not be available.")
        if st.button("Back to Model Selection"):
            try:
                st.query_params.clear()
            except AttributeError:
                st.experimental_set_query_params()
            st.rerun()
        return
    
    # Model info in sidebar
    with st.sidebar:
        st.header("📊 Model Info")
        if model_info:
            st.metric("Algorithm", model_info.get('best_algorithm', 'Unknown'))
            st.metric("Score", f"{model_info.get('best_score', 0):.2%}")
            st.metric("Target", model_info.get('target_column', 'Unknown'))
            st.metric("Features", model_info.get('num_features', 0))
        
        st.divider()
        if st.button("🔄 Choose Different Model"):
            try:
                st.query_params.clear()
            except AttributeError:
                st.experimental_set_query_params()
            st.rerun()
    
    # Generate form from schema
    st.subheader("📝 Enter Feature Values")
    
    if schema:
        form_values = generate_form_from_schema(schema)
    else:
        st.warning("No schema available. Cannot generate form.")
        return
    
    st.divider()
    
    # Predict button
    if st.button("🚀 Make Prediction", use_container_width=True):
        try:
            # Prepare input data
            input_df = pd.DataFrame([form_values])
            
            # Handle categorical encoding for older models that don't have CombinedPreprocessor
            def encode_categorical(df):
                """Encode categorical columns as numeric for models without proper preprocessor"""
                from sklearn.preprocessing import LabelEncoder
                df_encoded = df.copy()
                for col in df_encoded.columns:
                    if df_encoded[col].dtype == 'object' or isinstance(df_encoded[col].iloc[0], str):
                        # Simple encoding: convert to category codes
                        try:
                            df_encoded[col] = pd.Categorical(df_encoded[col]).codes
                        except:
                            df_encoded[col] = 0
                return df_encoded
            
            # Apply preprocessor if available
            if preprocessor is not None:
                try:
                    # Try using preprocessor directly
                    input_processed = preprocessor.transform(input_df)
                except (ValueError, TypeError) as e:
                    # Fallback: encode categorical columns first, then apply scaler
                    st.info("Using fallback encoding for categorical features...")
                    input_encoded = encode_categorical(input_df)
                    try:
                        input_processed = preprocessor.transform(input_encoded)
                    except:
                        # Last resort: just use encoded values
                        input_processed = input_encoded.values
            else:
                # No preprocessor - try to encode categoricals
                input_processed = encode_categorical(input_df).values
            
            # Make prediction
            prediction = model.predict(input_processed)[0]
            
            # Get probability if available
            probability = None
            if hasattr(model, 'predict_proba'):
                try:
                    proba = model.predict_proba(input_processed)[0]
                    probability = max(proba)
                except:
                    pass
            
            # Display result
            st.markdown(f'''
                <div class="prediction-result">
                    <div>Predicted: <strong>{prediction}</strong></div>
                    {f'<div class="confidence-badge">Confidence: {probability:.1%}</div>' if probability else ''}
                </div>
            ''', unsafe_allow_html=True)
            
            # Show input summary
            with st.expander("📋 Input Summary"):
                st.json(form_values)
            
        except Exception as e:
            st.error(f"Prediction failed: {str(e)}")

    # Footer
    st.divider()
    st.caption("Powered by InferX-ML")


if __name__ == "__main__":
    main()
