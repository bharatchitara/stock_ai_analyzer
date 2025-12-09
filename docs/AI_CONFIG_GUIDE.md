# AI Configuration Management

## Overview
The project now uses a database-driven approach for managing AI model configurations instead of hardcoded values. This allows you to change AI models without modifying code.

## AIConfig Model

### Fields
- **name**: Configuration name (e.g., 'default', 'production', 'testing')
- **gemini_model**: Gemini model name (default: 'gemini-1.5-flash')
- **openai_model**: OpenAI model name (default: 'gpt-3.5-turbo')
- **is_active**: Boolean flag to mark active configuration
- **created_at**: Timestamp of creation
- **updated_at**: Timestamp of last update

### Database Location
Table: `news_aiconfig`

## Usage

### 1. View/Edit Configurations in Django Admin

1. Navigate to: `http://localhost:9150/admin/news/aiconfig/`
2. Login with admin credentials
3. View existing configurations
4. Edit model names or create new configurations

### 2. Changing AI Models

**Option A: Via Django Admin (Recommended)**
1. Go to Admin → News → AI Configurations
2. Click on the active configuration
3. Change `gemini_model` to desired model:
   - `gemini-2.5-flash` (default, recommended)
   - `gemini-2.5-pro` (more capable, better reasoning)
   - `gemini-flash-latest` (always uses latest)
   - `gemini-2.0-flash-exp` (experimental, may have rate limits)
4. Save

**Option B: Via Django Shell**
```python
python manage.py shell

from news.models import AIConfig

# Get active config
config = AIConfig.get_active_config()

# Update Gemini model
config.gemini_model = 'gemini-1.5-pro'
config.save()

# Update OpenAI model
config.openai_model = 'gpt-4'
config.save()
```

**Option C: Create New Configuration**
```python
from news.models import AIConfig

# Deactivate current configs
AIConfig.objects.all().update(is_active=False)

# Create new config
AIConfig.objects.create(
    name='production',
    gemini_model='gemini-2.5-pro',
    openai_model='gpt-4',
    is_active=True
)
```

### 3. Available Gemini Models

| Model Name | Speed | Cost | Best For |
|------------|-------|------|----------|
| `gemini-2.5-flash` | Fast | Low | **Default**, most use cases (recommended) |
| `gemini-2.5-pro` | Medium | Medium | Complex analysis, reasoning |
| `gemini-flash-latest` | Fast | Low | Alias to latest flash model |
| `gemini-2.0-flash` | Fast | Low | Previous generation |
| `gemini-2.0-flash-exp` | Fast | Free (limited) | Experimental features |

### 4. Where Models Are Used

**Gemini Models:**
- `news/scraper.py`: Content extraction, relevance filtering, article summarization
- `portfolio/image_processor.py`: OCR extraction from portfolio screenshots
- `quick_analysis.sh`: Sentiment analysis

**OpenAI Models:**
- `analysis/ai_analyzer.py`: Sentiment analysis, categorization
- `portfolio/portfolio_analyzer.py`: Portfolio analysis

## Code Implementation

### How It Works

1. **Model Retrieval Function** (`news/scraper.py`):
```python
def get_gemini_model():
    """Get Gemini model name from database configuration"""
    try:
        from news.models import AIConfig
        config = AIConfig.get_active_config()
        return config.gemini_model
    except Exception as e:
        logger.warning(f"Could not fetch AI config: {e}. Using default.")
        return 'gemini-2.5-flash'
```

2. **Usage in API Calls**:
```python
response = client.models.generate_content(
    model=get_gemini_model(),  # Dynamic model from DB
    contents=prompt
)
```

3. **Fallback Safety**: If database is unavailable, defaults to `gemini-1.5-flash`

## Benefits

✅ **No Code Changes**: Update models without editing source code  
✅ **Environment-Specific**: Different models for dev/staging/production  
✅ **A/B Testing**: Test different models easily  
✅ **Audit Trail**: Track when models were changed  
✅ **Hot Reload**: Changes take effect on next API call (no restart needed)  

## Migration

Applied migration: `news/migrations/0005_aiconfig.py`

## Best Practices

1. **Keep One Active Config**: Only one configuration should have `is_active=True`
2. **Test Before Production**: Test model changes in dev environment first
3. **Monitor Costs**: Higher-tier models (gemini-pro, gpt-4) cost more
4. **Rate Limits**: Be aware of free tier limits on experimental models
5. **Default Fallback**: System always falls back to `gemini-2.5-flash` if DB unavailable

## Troubleshooting

**Issue**: Changes not taking effect
- **Solution**: Restart Django server (changes are cached at startup)

**Issue**: Rate limit errors with `gemini-2.0-flash-exp`
- **Solution**: Change to `gemini-2.5-flash` in admin panel

**Issue**: "AIConfig matching query does not exist"
- **Solution**: Run `python manage.py shell -c "from news.models import AIConfig; AIConfig.get_active_config()"`

## Examples

### Switch to Pro Model for Production
```python
python manage.py shell

from news.models import AIConfig
config = AIConfig.get_active_config()
config.name = 'production'
config.gemini_model = 'gemini-2.5-pro'
config.save()
print(f"Updated to {config.gemini_model}")
```

### Create Test Configuration
```python
from news.models import AIConfig

AIConfig.objects.create(
    name='testing',
    gemini_model='gemini-2.5-flash',
    openai_model='gpt-3.5-turbo',
    is_active=False
)
```

### Switch Between Configurations
```python
from news.models import AIConfig

# Deactivate all
AIConfig.objects.all().update(is_active=False)

# Activate specific config
test_config = AIConfig.objects.get(name='testing')
test_config.is_active = True
test_config.save()
```
