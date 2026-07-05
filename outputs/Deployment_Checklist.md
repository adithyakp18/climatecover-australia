# ClimateCover Australia - Deployment Checklist

## Recommended Fast Deployment: Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to https://share.streamlit.io/
3. Create a new app.
4. Select the GitHub repository.
5. Set the main file path:

```text
app/Home.py
```

6. Deploy.

The app includes an automatic startup bootstrap. If the DuckDB table is missing on the host, it will prepare the ABS-backed database before rendering.

The latest build includes real ABS Census SA2 household indicators and a Data Quality page for source lineage and validation status.

## Required Files For Deployment

These files must be committed:

```text
app/
src/
scripts/
docs/
outputs/
requirements.txt
README.md
.streamlit/config.toml
```

Recommended committed data/documentation files:

```text
data/raw/seifa_2021_sa2.xlsx
data/raw/census_2021_sa2_demographics.csv
docs/data_refresh_manifest.json
docs/data_source_catalog.json
outputs/ClimateCover_Project_Summary.md
outputs/Deployment_Checklist.md
```

Do not rely on your local `localhost` URL for LinkedIn. It only works on your machine.

## Public Link For LinkedIn

After deployment, use the Streamlit public URL in your post, for example:

```text
https://your-app-name.streamlit.app/
```

Before posting, open the deployed app and confirm:

- Home page loads without the database warning.
- Executive Overview shows KPI cards and donut charts.
- Region Profile shows a generated regional briefing.
- Data Quality shows `Real Public Data: 2,353` for household indicators.
- Methodology explains real public data, modelled indicators and calculated metrics.

## Suggested LinkedIn Format

Use:

- A short project post
- The live app link
- One or two screenshots captured manually from the deployed app
- A GitHub repository link

## Manual Screenshot Guidance

For LinkedIn:

1. Open the deployed app URL.
2. Use the Executive Overview page.
3. Use the Region Profile page.
4. Use the Data Quality page if you want to prove source credibility.
5. Capture screenshots with only the dashboard visible.
6. Avoid showing local folders, terminals, API keys or browser tabs with personal information.

## Refresh Commands

Local refresh:

```powershell
python scripts\refresh_public_data.py
```

If DuckDB is locked, stop any running Streamlit sessions first:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*streamlit*app/Home.py*' } | Select-Object ProcessId,CommandLine
```

GitHub refresh:

- Open the repository on GitHub.
- Go to Actions.
- Select `Refresh public data`.
- Click `Run workflow`.
