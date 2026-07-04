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

## Required Files For Deployment

These files must be committed:

```text
app/
src/
scripts/
docs/
requirements.txt
README.md
.streamlit/config.toml
```

Do not rely on your local `localhost` URL for LinkedIn. It only works on your machine.

## Public Link For LinkedIn

After deployment, use the Streamlit public URL in your post, for example:

```text
https://your-app-name.streamlit.app/
```

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
4. Capture screenshots with only the dashboard visible.
5. Avoid showing local folders, terminals, API keys or browser tabs with personal information.
