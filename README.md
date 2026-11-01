# J-STAGE article RSS for Feedly

This repository generates one RSS 2.0 file per journal, using the official J-STAGE article RSS (`JT0041`, not the issue RSS `JT0040`).

## Configuration

Add all journals to `journals.json` as `{ "code": "...", "name": "..." }` entries. The included `jjlp` entry is a temporary test only.

## Running

GitHub Actions > Update J-STAGE RSS > Run workflow, then review the run log and generated `feeds/*.xml` files. Scheduled execution runs every 6 hours (subject to GitHub scheduling delays). Set repository Actions workflow permissions to allow write if push fails.

## Publishing

Settings > Pages > Deploy from a branch > main > /(root). Feed URL: `https://USERNAME.github.io/jstage-rss/feeds/CODE.xml`.

## Validation limitations

This code is syntax-tested but the J-STAGE endpoint could not be fetched from the build environment. Validate the returned feed format and article titles in GitHub Actions before relying on it. The official article RSS may omit older items or updates; no completeness guarantee is made. Empty or malformed responses cause the workflow to fail rather than silently overwrite a feed.
