# Job Description Template

For best parsing results, structure your job description documents with these headers at the top:

## Recommended Structured Header Format

```
Job Title: [Your job title]
Location: [City, State/Country]
Work Model: [Remote/Hybrid/On-site details]
Employment Type: full_time
Travel Required: false
Experience Required: [X-Y years]
Education: [Degree level required]
Visa Sponsorship: [true/false]

Company: [Company name]
Industry: [Industry sector]
Company Size: [Size range]

Salary Range: [Min-Max]
Currency: [INR/USD/EUR/GBP]
Benefits: [List key benefits]
```

## Field Format Guidelines

### Employment Type
**Must be exactly one of:**
- `full_time`
- `part_time`
- `contract`
- `internship`
- `temporary`

### Boolean Fields
Use `true` or `false` (lowercase, no quotes):
- `Travel Required: false`
- `Visa Sponsorship: true`
- `Remote: true`

### Location
- **City**: Full city name
- **Country**: Use 2-letter ISO codes (US, IN, GB, CA, etc.)
- Example: `Chennai, India` or `San Francisco, US`

### Education Level
**Recommended values:**
- `high_school`
- `associate`
- `bachelor`
- `master`
- `phd`
- `none`

### Dates
- **Format**: YYYY or YYYY-MM
- Example: `2025` or `2025-12`

## Example Job Description

See `examples/sample_job_description.txt` for a complete example following this template.

## Benefits of Structured Headers

1. **Higher parsing accuracy** - Direct extraction of key fields
2. **Consistent data quality** - Reduces GPT interpretation errors
3. **Faster processing** - Less ambiguity for the parser
4. **Better validation** - Values match schema requirements exactly

## Fallback for Unstructured Documents

Even without structured headers, the parser will:
- Use GPT-4o-mini to intelligently extract information
- Normalize values to match schema requirements
- Apply validation fixes for common variations
- Still produce canonical JSON output

However, structured headers will give you the most reliable results!
