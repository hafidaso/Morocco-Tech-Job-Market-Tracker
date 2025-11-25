#!/usr/bin/env python3
"""
Test script to verify Resend email configuration.
Run this to check if your RESEND_API_KEY is working.
"""
import os
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}. Continuing with existing environment.")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
# Use onboarding@resend.dev for testing (Resend's verified test domain)
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

if not RESEND_API_KEY:
    print("❌ RESEND_API_KEY is not set in your .env file!")
    print("\n📝 To set it up:")
    print("   1. Go to https://resend.com and sign up (free tier available)")
    print("   2. Get your API key from the dashboard")
    print("   3. Add to .env: RESEND_API_KEY=re_xxxxxxxxxxxxx")
    print("   4. Verify your domain or use the test domain: onboarding@resend.dev")
    exit(1)

try:
    import resend
    resend.api_key = RESEND_API_KEY
    
    # Test email
    test_email = input("Enter your email address to test: ").strip()
    if not test_email:
        print("❌ No email provided")
        exit(1)
    
    print(f"\n📧 Sending test email from {RESEND_FROM_EMAIL} to {test_email}...")
    print(f"   Using FROM: {RESEND_FROM_EMAIL}")
    if "onboarding@resend.dev" not in RESEND_FROM_EMAIL:
        print("   ⚠️  Note: For testing, use 'onboarding@resend.dev' as FROM address")
        print("   ⚠️  Update your .env: RESEND_FROM_EMAIL=onboarding@resend.dev")
    
    params = {
        "from": RESEND_FROM_EMAIL,
        "to": [test_email],
        "subject": "🧪 Test Email from Morocco Tech Monitor",
        "html": """
        <h2>✅ Email Configuration Test</h2>
        <p>If you're reading this, your Resend integration is working correctly!</p>
        <p>Your Morocco Tech Monitor job alerts will be sent from this address.</p>
        <hr>
        <small>This is a test email. You can safely ignore it.</small>
        """,
    }
    
    email = resend.Emails.send(params)
    print(f"✅ Test email sent successfully!")
    print(f"   Email ID: {email.get('id', 'N/A')}")
    print(f"\n📬 Check your inbox at {test_email}")
    print("   (It may take a few seconds to arrive)")
    
except ImportError:
    print("❌ Resend module not installed!")
    print("   Run: pip install resend")
except Exception as e:
    error_msg = str(e)
    print(f"❌ Failed to send test email: {error_msg}")
    print("\n💡 Common issues and fixes:")
    print("   1. Unverified domain:")
    print("      → Set RESEND_FROM_EMAIL=onboarding@resend.dev in .env")
    print("      → This is Resend's verified test domain (no setup needed)")
    print("   2. Invalid API key:")
    print("      → Check your .env file has RESEND_API_KEY=re_...")
    print("      → Get your key from: https://resend.com/api-keys")
    print("   3. Network connectivity:")
    print("      → Check your internet connection")
    print("\n🔧 Quick fix:")
    print("   Add to .env: RESEND_FROM_EMAIL=onboarding@resend.dev")
    print("   Then run this script again.")

