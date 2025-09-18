readarr-to-play-books
=====================

Upload Readarr-imported books (EPUB/PDF) to your Google Play Books library using Playwright.

Quick start
-----------

1) Install and prepare

```
pip install .
playwright install
```

2) Configure

Copy `env.example` to `.env` and adjust:

```
cp env.example .env
```

3) First-time login (headful)

Run once headful on a machine with a display, log in to Google, and verify you can upload a book. This saves the session in `USER_DATA_DIR`.

```
readarr-to-play-books --headless false --dir /path/to/books
```

4) Run headless (Docker/LXC)

Copy the `USER_DATA_DIR` into your container, ensure Chromium deps are installed, then run:

```
readarr-to-play-books --headless true --dir /path/inside/container
```

Readarr post-import hook
------------------------

Configure a Custom Script in Readarr to call the CLI with the imported file path:

```
readarr-to-play-books --file "$READARR_BOOKFILE_PATH"
```

Environment variables
---------------------

You can set these in `.env` or via the environment:

- `READARR_BOOKFILE_PATH`: preferred single-file mode from Readarr
- `READARR_EXPORT_DIR`: optional directory scan fallback
- `USER_DATA_DIR`: Chromium profile dir with saved login (default `./user-data`)
- `STATE_FILE`: path to record uploaded files (default `./uploaded_state.json`)
- `HEADLESS`: `true`/`false` (default `true`)
- `BATCH_SIZE`: number of files per upload batch (default `3`)

Notes
-----

- If headless login fails (e.g., CAPTCHA), refresh the session headful.
- UI changes can break selectors; update as needed.
- For Docker, add `--no-sandbox` and ensure Chromium deps are installed.

License
-------

MIT, see LICENSE.


