# Data — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `data`). Edit in the Memory tab or say **"data cheatsheet"**.

## Chat examples

| You say | ARIA does |
|---------|-------------|
| Attach CSV/JSON or "load data.csv" | Loads dataset into session |
| "How many rows?" / "Describe this data" | Summary stats |
| "Chart column_name" | Matplotlib chart (GUI shows image) |
| "Plot histogram of age" | Chart from natural language |
| "Clean duplicates and nulls" | Cleaning pipeline |
| "Export to CSV" / "Export report to PDF" | Export results |
| Follow-up questions on loaded data | SQL-like LLM queries over sample |

## Requirements

- **pandas** recommended: `pip install pandas`
- Large files may use streaming mode automatically.

## CLI

```bash
python main.py data
```

## Tips

- Session remembers **last data path** — ask to reload after restart.
- Export PDF needs matplotlib.
