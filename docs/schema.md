# Data Schema (v1)

## events

- `id` (str, PK) – GDELT `GLOBALEVENTID`
- `ts` (datetime) – derived from `SQLDATE` at midnight UTC
- `date` (date) – calendar date of the event
- `country` (str, ISO-2, nullable) – primarily `ActionGeo_CountryCode`
- `admin1` (str, nullable) – `ActionGeo_ADM1Code`
- `lat` (float, nullable) – `ActionGeo_Lat`
- `lon` (float, nullable) – `ActionGeo_Long`
- `event_code` (str, nullable) – `EventCode`
- `quad_class` (int, nullable) – `QuadClass`
- `avg_tone` (float, nullable) – `AvgTone`
- `source_url` (str, nullable) – `SOURCEURL`
- `category` (str, nullable) – taxonomy-mapped category

## daily_metrics

- `id` (int, PK)
- `date` (date, indexed)
- `country` (str, ISO-2, indexed)
- `category` (str, indexed)
- `event_count` (int)
- `avg_tone` (float, nullable)

Unique constraint on `(date, country, category)`.

