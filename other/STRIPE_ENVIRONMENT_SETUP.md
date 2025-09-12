# =============================================================================
# STRIPE PAYMENT ENVIRONMENT VARIABLES
# =============================================================================
# Add these to your .env file

# Stripe Test Keys (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here

# Stripe Webhook Secret (get from https://dashboard.stripe.com/test/webhooks)
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Optional: Stripe Live Keys (only use in production)
# STRIPE_LIVE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key_here
# STRIPE_LIVE_SECRET_KEY=sk_live_your_live_secret_key_here

# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================

# 1. Create a Stripe account at https://stripe.com
# 2. Go to https://dashboard.stripe.com/test/apikeys
# 3. Copy your "Publishable key" and "Secret key"
# 4. Replace the values above with your actual keys
# 5. Set up webhooks at https://dashboard.stripe.com/test/webhooks
#    - Endpoint URL: https://yourdomain.com/api/payments/webhooks/stripe/
#    - Events to send:
#      * payment_intent.succeeded
#      * payment_intent.payment_failed
# 6. Copy the webhook signing secret and add it to STRIPE_WEBHOOK_SECRET

# =============================================================================
# SECURITY NOTES
# =============================================================================
# - Never commit these keys to version control
# - Use test keys for development
# - Use live keys only in production
# - Rotate keys regularly
# - Monitor your Stripe dashboard for unusual activity
