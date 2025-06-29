# Data Analysis Workflows

This directory contains workflows for automating data analysis and insight extraction.

## 📁 Included Workflows

### simple-analytics.yml
**Purpose**: Basic analysis of CSV format data  
**Features**:
- Automatic data structure analysis
- Basic statistics calculation
- Trend analysis
- Business insight generation
- Improvement recommendations

**Usage Example**:
```bash
bakufu run examples/data-analysis/simple-analytics.yml --input '{
  "csv_data": "Date,Sales,Customers\n2024-01-01,150000,45\n2024-01-02,180000,52\n2024-01-03,165000,48",
  "analysis_focus": "Sales trend analysis"
}'
```

### log-analyzer.yml
**Purpose**: Application log analysis and monitoring  
**Features**:
- Error pattern detection
- Performance analysis
- Time series trend analysis
- Prioritized improvement recommendations
- Anomaly detection

**Usage Example**:
```bash
bakufu run examples/data-analysis/log-analyzer.yml --input '{
  "log_data": "2024-01-01 09:00:00 INFO Application started\n2024-01-01 09:05:00 ERROR Database connection failed\n2024-01-01 09:05:30 WARN Retrying connection\n2024-01-01 09:06:00 INFO Connected successfully",
  "time_range": "2024-01-01 09:00-10:00"
}'
```

## 💡 Use Cases

### Business Analysis
- Regular sales data analysis
- Customer behavior pattern investigation
- Marketing effectiveness measurement
- KPI monitoring reports

### System Operations
- Server log monitoring
- Performance degradation detection
- Error trend analysis
- Capacity planning support

### Quality Management
- Defect pattern analysis
- User experience evaluation
- System stability assessment

## 📊 Analysis Best Practices

### Data Preparation
1. **Data Quality Assurance**: Check for missing values and outliers
2. **Format Standardization**: Standardize date/time and category notation
3. **Sample Size**: Ensure statistically meaningful data volume

### Analysis Design
1. **Clear Purpose**: Set specific goals for what you want to learn
2. **Hypothesis Setting**: Pre-consider expected results and factors
3. **Context Consideration**: Account for business environment and seasonality

### Result Utilization
1. **Action-Oriented**: Insights that lead to concrete actions
2. **Continuous Monitoring**: Track changes through regular analysis
3. **Knowledge Sharing**: Share insights among stakeholders

## 🔧 Customization Tips

- **Analysis Focus Adjustment**: Specify analysis direction with `analysis_focus` parameter
- **Time Range Setting**: Narrow target period for log analysis
- **Threshold Adjustment**: Customize anomaly and warning levels
- **Report Format**: Adapt output format to business requirements
