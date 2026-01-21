"""
Validate that required configuration is present.
Run this at startup or in CI/CD to catch missing env vars early.
"""
import os
import sys

def check_config():
    """Check for required configuration (Replit env vars or Streamlit secrets)."""
    replit_vars = [
        'PGHOST',
        'PGPORT',
        'PGDATABASE',
        'PGUSER',
        'PGPASSWORD'
    ]
    
    has_replit = all(os.environ.get(var) for var in replit_vars)
    
    if has_replit:
        print("✅ Replit PostgreSQL configuration found")
        return True
    
    # Check for Streamlit secrets (can't fully validate without importing streamlit)
    try:
        import streamlit as st
        try:
            secrets = st.secrets["connections"]["postgresql"]
            required_keys = ['host', 'port', 'database', 'username', 'password']
            if all(key in secrets for key in required_keys):
                print("✅ Streamlit secrets configuration found")
                return True
        except (KeyError, AttributeError):
            pass
    except ImportError:
        pass
    
    print("❌ ERROR: No valid database configuration found")
    print("   Required: Either Replit PostgreSQL env vars or Streamlit secrets")
    return False

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
