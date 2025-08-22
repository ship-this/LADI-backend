# OpenAI API Setup for Real Evaluation Scores

## Problem
Currently, the LADI backend is using **mock/fake evaluation scores** instead of real AI evaluation scores. This is because the OpenAI API key is not configured.

## Solution
To get real AI evaluation scores, you need to configure your OpenAI API key.

## Setup Instructions

### 1. Get an OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your OpenAI account
3. Create a new API key
4. Copy the API key (it starts with `sk-`)

### 2. Configure the API Key

#### Option A: Environment Variable (Recommended)
```bash
export OPENAI_API_KEY='sk-your-actual-api-key-here'
```

#### Option B: .env File (Local Development)
Add to your `.env` file:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

#### Option C: Render Dashboard (Production)
1. Go to your Render service dashboard
2. Navigate to Environment > Environment Variables
3. Add new variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `sk-your-actual-api-key-here`
4. Save and redeploy

### 3. Restart Your Application
After setting the API key, restart your backend application for the changes to take effect.

## Verification

### Check if Real Evaluation is Working
1. Upload a manuscript for evaluation
2. Check the backend logs for these messages:
   - ✅ `"Successfully initialized OpenAI client"`
   - ✅ `"Starting manuscript evaluation"`
   - ❌ **NOT** `"GENERATING MOCK EVALUATION"`

### Expected Log Messages
**Real Evaluation (Good):**
```
INFO: Successfully initialized OpenAI client
INFO: Starting manuscript evaluation for 5000 characters
INFO: Evaluating category: Line & Copy Editing
INFO: Evaluating category: Plot Evaluation
...
```

**Mock Evaluation (Bad):**
```
ERROR: ⚠️  GENERATING MOCK EVALUATION - THESE ARE FAKE SCORES FOR TESTING ONLY!
ERROR: ⚠️  Set OPENAI_API_KEY environment variable to get real AI evaluation scores!
```

## Cost Information
- **GPT-4**: ~$0.03 per 1K tokens
- **Typical evaluation**: ~$0.10-0.50 per manuscript
- **Recommendation**: Set usage limits in your OpenAI dashboard

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Make sure you've set the `OPENAI_API_KEY` environment variable
   - Check that the key starts with `sk-`
   - Restart your application after setting the key

2. **"Failed to initialize OpenAI client"**
   - Check your internet connection
   - Verify the API key is valid
   - Check OpenAI service status

3. **"Rate limit exceeded"**
   - Wait a few minutes before trying again
   - Consider upgrading your OpenAI plan
   - Check your usage in OpenAI dashboard

### Testing the Setup
Run the setup script to verify your configuration:
```bash
cd backend
python setup_openai.py
```

## Security Notes
- ⚠️ **Never commit your API key to version control**
- ⚠️ **Keep your API key secure**
- ⚠️ **Set usage limits in OpenAI dashboard**
- ⚠️ **Monitor your usage regularly**

## Support
If you're still having issues:
1. Check the backend logs for error messages
2. Verify your OpenAI API key is valid
3. Test with a simple API call to OpenAI
4. Contact support if needed
