# 📧 Email Alerts Setup Guide

This guide will help you set up the Smart Alerts feature for your Job Market Tracker.

## Overview

The Smart Alerts feature allows users to subscribe to email notifications for specific keywords (e.g., "React", "Python", "Data Scientist"). When new jobs matching their keyword are scraped, they automatically receive an email digest.

## Prerequisites

1. ✅ **Supabase Database** - Already set up
2. ✅ **Resend SDK** - Already installed (`pip install resend`)
3. ⚠️ **Resend Account** - Need to set up (free tier available)

## Step 1: Create Subscriptions Table

Run this SQL in your Supabase SQL Editor:

```sql
-- Run the contents of supabase_subscriptions_setup.sql
-- Or copy-paste from that file
```

Or run the SQL directly:

```sql
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  keyword TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(email, keyword)
);

CREATE INDEX IF NOT EXISTS subscriptions_email_idx ON public.subscriptions (email);
CREATE INDEX IF NOT EXISTS subscriptions_keyword_idx ON public.subscriptions (keyword);

ALTER TABLE public.subscriptions DISABLE ROW LEVEL SECURITY;
```

## Step 2: Set Up Resend Account

1. **Sign up for Resend** (free tier):
   - Go to https://resend.com
   - Sign up for a free account
   - Free tier includes: 3,000 emails/month, 100 emails/day

2. **Get your API Key**:
   - Go to Resend Dashboard → API Keys
   - Click "Create API Key"
   - Copy the key (starts with `re_`)

3. **Verify Domain** (optional for production):
   - For testing, you can use Resend's test domain: `onboarding@resend.dev`
   - For production, add your own domain in Resend Dashboard → Domains

## Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Resend Email Configuration
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev  # Use your verified domain for production
```

**Important**: 
- For testing: Use `onboarding@resend.dev` (Resend's test domain)
- For production: Use your verified domain (e.g., `jobs@yourdomain.com`)

## Step 4: Test Email Configuration

Run the test script to verify your setup:

```bash
python3 test_email.py
```

This will:
1. Check if `RESEND_API_KEY` is set
2. Send a test email to your address
3. Confirm the integration is working

## Step 5: Test the Full Flow

1. **Start your backend**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Start your frontend**:
   ```bash
   cd client
   npm run dev
   ```

3. **Subscribe via Dashboard**:
   - Open http://localhost:3000
   - Fill in the subscription form:
     - Email: your-email@example.com
     - Keyword: "React" (or any skill you want to track)
   - Click "Subscribe"
   - You should see: "Subscription saved. We'll email new 'React' roles automatically."

4. **Verify Subscription in Supabase**:
   - Go to Supabase Dashboard → Table Editor → `subscriptions`
   - You should see your subscription record

5. **Trigger Email Alert** (when new jobs are scraped):
   - The scraper runs automatically every 6 hours
   - Or manually trigger: The next time `run_pipeline()` executes and finds new jobs matching your keyword, you'll receive an email

## How It Works

1. **User Subscribes**: Frontend sends POST to `/subscribe` with email + keyword
2. **Backend Stores**: Subscription saved to Supabase `subscriptions` table
3. **Scraper Runs**: Every 6 hours (or manually), `run_pipeline()` executes:
   - Scrapes new jobs
   - Analyzes skills
   - Syncs to Supabase
   - Detects new jobs (not in `LAST_JOB_IDS`)
4. **Email Matching**: For each new job, checks all subscriptions:
   - Matches keyword against job title, company, role, or skills
   - If match found, adds job to subscriber's digest
5. **Email Sent**: Sends HTML email via Resend with:
   - Subject: "X new React roles in Morocco"
   - Body: List of matching jobs with details
   - Max 10 jobs per email (to avoid spam)

## Email Template

The email includes:
- **Subject**: "X new [Keyword] roles in Morocco"
- **Body**: 
  - Header with keyword
  - Number of matching jobs
  - Ordered list of jobs with:
    - Job title (bold)
    - Company name
    - City
    - Date posted
    - Skills detected
  - Footer with unsubscribe info

## Troubleshooting

### "RESEND_API_KEY is not configured"
- Check your `.env` file has `RESEND_API_KEY=re_...`
- Restart your backend server after adding it

### "Resend SDK is missing"
- Run: `pip install resend`

### "Failed to send Resend email"
- Check your API key is valid
- Verify your domain (or use `onboarding@resend.dev` for testing)
- Check Resend dashboard for error logs

### "No subscribers found"
- Verify subscriptions table exists in Supabase
- Check that subscriptions are being saved (check Supabase table)

### Emails not sending on new jobs
- Check backend logs for "📧 X new jobs detected; checking subscriber alerts..."
- Verify `notify_subscribers()` is being called in `run_pipeline()`
- Check that new jobs actually match subscription keywords

## Production Considerations

1. **Domain Verification**: 
   - Add your domain in Resend Dashboard
   - Update `RESEND_FROM_EMAIL` to use your domain
   - Set up SPF/DKIM records (Resend provides instructions)

2. **Rate Limiting**:
   - Resend free tier: 100 emails/day
   - Consider batching notifications
   - Monitor email usage in Resend dashboard

3. **Unsubscribe**:
   - Currently, users need to manually delete from Supabase
   - Future enhancement: Add unsubscribe link in emails

4. **Email Content**:
   - Customize `build_email_html()` in `main.py` for branding
   - Add unsubscribe link
   - Consider plain text alternative

## Next Steps

- ✅ Subscriptions table created
- ✅ Resend SDK installed
- ⚠️ Add `RESEND_API_KEY` to `.env`
- ⚠️ Run `supabase_subscriptions_setup.sql`
- ⚠️ Test with `python3 test_email.py`
- ⚠️ Subscribe via dashboard and verify

Once configured, your users can subscribe to keywords and receive automatic email alerts whenever matching jobs are found! 🎉

