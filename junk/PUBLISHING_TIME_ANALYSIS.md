# YouTube Video Publishing Time Analysis for Sri Lankan Creators

## Overview

This enhanced YouTube Data Extractor is specifically designed to help Sri Lankan YouTube creators determine the optimal publishing times for their content. The system collects comprehensive video data and analyzes publishing patterns to maximize viewer engagement and reach.

## Key Features for Publishing Time Analysis

### 1. Enhanced Data Collection
- **Sri Lankan Timezone Conversion**: All publishing times are converted to Asia/Colombo timezone
- **Time-based Metrics**: Capture publishing hour, day of week, and time categories
- **Performance Tracking**: Views per hour in first 24 hours, engagement rates by time
- **Holiday Detection**: Identify uploads during Sri Lankan holidays and special periods

### 2. Dashboard with Tabular Data View
- **Dataset Tab**: View collected videos in a comprehensive table format
- **Filter Options**: Filter by time range, category, and sort by various metrics
- **Pagination**: Navigate through large datasets efficiently
- **Export-ready Format**: Data presented in analysis-ready structure

### 3. Publishing Analytics Tab
- **Hourly Analysis**: Charts showing best performing hours (Sri Lankan time)
- **Daily Analysis**: Compare weekday vs weekend performance
- **Category-wise Recommendations**: Optimal times for different content types
- **Visual Charts**: Interactive charts powered by Chart.js

## Data Fields Collected

### Publishing Time Analysis Fields
- `published_at_lk`: Publishing time in Sri Lankan timezone
- `published_day_of_week`: Day of week (0=Monday, 6=Sunday)
- `published_hour_lk`: Hour of publication (0-23) in Sri Lankan time
- `upload_time_category`: Morning, Afternoon, Evening, Night
- `is_weekend_upload`: Boolean flag for weekend uploads
- `is_holiday_period`: Flag for Sri Lankan holiday periods

### Performance Metrics
- `views_per_hour_first_24h`: Early performance indicator
- `engagement_rate`: Likes + Comments / Views
- `likes_per_view`: Like rate percentage
- `comments_per_view`: Comment rate percentage
- `views_per_day`: Average daily views since publication

### Content Characteristics
- `duration_category`: Short, Medium, Long, Very Long
- `content_score`: Sri Lankan relevance score
- `quality_score`: Overall content quality assessment
- `detected_location`: Specific Sri Lankan locations mentioned

## How to Use for Publishing Time Analysis

### 1. Start Data Collection
1. Navigate to the Dashboard tab
2. Use "Quick Start" for immediate collection or "Full Extraction" for comprehensive data
3. Monitor progress through the status indicators

### 2. View Dataset
1. Click on the "Dataset" tab
2. Use filters to focus on:
   - Time ranges (7d, 30d, 90d)
   - Specific categories
   - Sort by performance metrics
3. Analyze patterns in the tabular view

### 3. Get Publishing Recommendations
1. Go to the "Publishing Analytics" tab
2. Review hourly performance charts
3. Check category-specific optimal times
4. Note weekend vs weekday patterns

## Key Insights You Can Derive

### Optimal Publishing Hours
- Best performing hours in Sri Lankan time
- Peak engagement periods
- Category-specific timing recommendations

### Day-of-Week Analysis
- Weekend vs weekday performance
- Best days for different content types
- Holiday period impact

### Content Strategy
- Optimal video lengths by time slot
- Engagement patterns by upload time
- Regional content performance

## API Endpoints for Analysis

### Dataset Access
- `GET /api/dataset/videos` - Paginated video data with filters
- `GET /api/dataset/summary` - Dataset overview statistics

### Publishing Analytics
- `GET /api/analytics/publishing-times` - Comprehensive time analysis
- `GET /api/analytics/trending` - Current trending videos

## Sample Analysis Queries

The system automatically generates insights like:

1. **Best Publishing Hours**: "Videos uploaded at 7 PM Sri Lankan time receive 40% more engagement"
2. **Category Recommendations**: "Travel content performs best on weekends between 10 AM - 2 PM"
3. **Holiday Impact**: "Videos uploaded during Vesak season show 25% higher view rates"

## Data Export and Further Analysis

The collected data can be:
- Viewed in the dashboard's tabular format
- Exported from BigQuery for advanced analysis
- Used with external BI tools for custom reports
- Integrated with ML models for predictive analysis

## Best Practices for Sri Lankan Creators

Based on the data analysis capabilities:

1. **Time Testing**: Upload similar content at different times and compare performance
2. **Audience Segmentation**: Analyze performance by detected locations within Sri Lanka
3. **Seasonal Patterns**: Consider holiday periods and cultural events
4. **Content Length**: Match video duration to optimal time slots
5. **Consistency**: Use data to establish regular publishing schedules

## Getting Started

1. Ensure your YouTube API keys are configured
2. Start with a "Quick Start" extraction to get initial data
3. Let the system collect data for at least a week
4. Use the Publishing Analytics tab to get initial insights
5. Refine your publishing strategy based on the data

This enhanced system transforms raw YouTube data into actionable insights for optimizing your content publishing strategy specifically for Sri Lankan audiences.
