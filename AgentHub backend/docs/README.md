# SmartSchema Backend Documentation

This directory contains the Sphinx documentation for the SmartSchema Backend API.

## Building the Documentation

### Prerequisites

Install the documentation dependencies:

```bash
pip install -r requirements-docs.txt
```

### Building HTML Documentation

**On Windows (PowerShell):**
```powershell
cd docs
.\make.bat html
```
Or use the PowerShell script:
```powershell
cd docs
.\make.ps1 html
```

**On Windows (Command Prompt):**
```cmd
cd docs
make.bat html
```

**On macOS/Linux:**
```bash
cd docs
make html
```

The built documentation will be available in `docs/_build/html/index.html`.

### Building Other Formats

You can build documentation in other formats:

- **PDF**: `make latexpdf` (requires LaTeX)
- **EPUB**: `make epub`
- **Single HTML**: `make singlehtml`

### Viewing the Documentation

After building, open `docs/_build/html/index.html` in your web browser.

## Documentation Structure

- `index.rst` - Main documentation entry point
- `getting-started.rst` - Installation and setup guide
- `api-reference.rst` - API endpoint overview
- `modules.rst` - Module documentation (auto-generated from code)
- `configuration.rst` - Configuration and environment variables

## Theme

The documentation uses the `sphinx_rtd_theme` (Read the Docs theme) for a clean, professional appearance.

## Auto-documentation

The documentation automatically extracts docstrings from Python modules using Sphinx's autodoc extension. Make sure your code has proper docstrings for best results.

## GitHub Pages Deployment

The documentation is automatically built and deployed to GitHub Pages when you push changes to the `main` or `master` branch.

### Setup (One-time)

1. Go to your GitHub repository settings
2. Navigate to **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions**
4. Save the settings

### Automatic Deployment

The documentation will automatically build and deploy when:
- You push changes to `main` or `master` branch
- Changes are made to files in `docs/`, `app/`, or the workflow file
- You manually trigger the workflow from the Actions tab

### Accessing Your Documentation

After deployment, your documentation will be available at:
```
https://<your-username>.github.io/<repository-name>/
```

Or if you have a custom domain configured:
```
https://docs.yourdomain.com
```

### Manual Deployment

You can also manually trigger the workflow:
1. Go to the **Actions** tab in your GitHub repository
2. Select **Build and Deploy Documentation**
3. Click **Run workflow**

The workflow will build the documentation and deploy it to GitHub Pages, making it accessible online just like when you view it locally!

