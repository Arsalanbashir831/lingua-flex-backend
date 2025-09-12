#!/usr/bin/env python3
"""
Direct test of Stripe Token API functionality (bypassing Django auth)
"""

import stripe
import os
from dotenv import load_dotenv

load_dotenv()

def test_stripe_token_approach():
    """Test if Stripe Token API works for our use case"""
    
    # Set up Stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        return
    
    print(f"🔧 Using Stripe key: {stripe.api_key[:20]}...")
    
    # Test card data
    test_card = {
        'number': '4242424242424242',
        'exp_month': 12,
        'exp_year': 2025,
        'cvc': '123',
        'name': 'John Doe Test',
    }
    
    print("\n🧪 Testing Stripe Token Creation...")
    print(f"Card: {test_card['number']}")
    
    try:
        # Step 1: Create token (this should work for test cards)
        print("\n📝 Step 1: Creating Stripe Token...")
        card_token = stripe.Token.create(card=test_card)
        print(f"✅ Token created successfully: {card_token.id}")
        print(f"   Card Last4: {card_token.card.last4}")
        print(f"   Card Brand: {card_token.card.brand}")
        
        # Step 2: Create payment method from token
        print("\n💳 Step 2: Creating PaymentMethod from Token...")
        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={'token': card_token.id},
            billing_details={'name': test_card['name']}
        )
        print(f"✅ PaymentMethod created successfully: {payment_method.id}")
        print(f"   Card Last4: {payment_method.card.last4}")
        print(f"   Card Brand: {payment_method.card.brand}")
        
        # Step 3: Test creating customer and attaching
        print("\n👤 Step 3: Creating test customer...")
        customer = stripe.Customer.create(
            email='test@stripe.example.com',
            name='Test User'
        )
        print(f"✅ Customer created: {customer.id}")
        
        # Step 4: Attach payment method to customer
        print("\n🔗 Step 4: Attaching PaymentMethod to Customer...")
        payment_method.attach(customer=customer.id)
        print(f"✅ PaymentMethod attached successfully")
        
        print("\n🎉 SUCCESS! The Token approach works perfectly!")
        print("This means our backend implementation should resolve the raw card issue.")
        
        # Clean up test resources
        print("\n🧹 Cleaning up test resources...")
        try:
            payment_method.detach()
            customer.delete()
            print("✅ Cleanup completed")
        except:
            print("ℹ️  Cleanup skipped (test mode)")
        
        return True
        
    except stripe.error.CardError as e:
        print(f"❌ Card Error: {e.user_message}")
        print(f"   Code: {e.code}")
        print(f"   Decline Code: {e.decline_code}")
        return False
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe Error: {str(e)}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return False

def test_different_cards():
    """Test multiple card scenarios"""
    
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    
    test_cards = [
        {'number': '4242424242424242', 'name': 'Visa Success'},
        {'number': '4000000000000002', 'name': 'Visa Declined'},
        {'number': '5555555555554444', 'name': 'Mastercard Success'},
        {'number': '378282246310005', 'name': 'Amex Success'},
    ]
    
    print("\n🧪 Testing Multiple Card Types...")
    
    for card_info in test_cards:
        print(f"\n📋 Testing {card_info['name']}: {card_info['number']}")
        
        try:
            token = stripe.Token.create(card={
                'number': card_info['number'],
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123',
            })
            print(f"   ✅ Token: {token.id}")
            
        except stripe.error.CardError as e:
            print(f"   ❌ Expected card error: {e.user_message}")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Stripe Token API Test")
    print("=" * 50)
    
    success = test_stripe_token_approach()
    
    if success:
        test_different_cards()
        
        print("\n" + "=" * 50)
        print("✅ CONCLUSION: The Stripe Token approach works!")
        print("Your backend payment endpoint should now work correctly.")
        print("\nNext steps:")
        print("1. Use the updated backend_views.py")
        print("2. Test with proper authentication")
        print("3. The raw card data issue should be resolved!")
    else:
        print("\n❌ Token approach failed. Check your Stripe configuration.")
