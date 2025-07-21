# Resume Website

This directory contains a static website for Michael E. Faherty's resume. The content has been sanitized to remove personal contact information and can be hosted with any static web server such as nginx.

To view the site locally you can build and run the accompanying Docker image:

```bash
# from this directory
docker build -t resume .
docker run --rm -p 8080:8080 resume
```

Then navigate to `http://localhost:8080/` in your browser. The page uses the
Bootswatch **lux** theme from a CDN, so Internet access is required.
