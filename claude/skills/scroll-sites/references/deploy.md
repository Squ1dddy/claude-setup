# Deploy

A scroll site is static files, so any static host works. Ask where it should live (clickable): the user's existing host, Hostinger (connector flow below), or a free static host (Cloudflare Pages, Netlify drop). Deploying costs nothing beyond hosting.

## Before any deploy

1. The deploy folder contains only `index.html` and `assets/`. No `review/`, raws, payloads, zips.
2. Patch `og:image` and `og:url` at the `<!-- DEPLOY STEP -->` comment with the live absolute URL, using the editor tool (shell find-and-replace can mangle UTF-8).
3. Hosts that recompress images: upload stills at about 1920px with one clean pass. WebP frames pass through most hosts untouched; spot-check one live.

## Hostinger (connector)

1. If the Hostinger tools don't respond, the user needs a plan and the connector: Windows `claude mcp add hostinger -- npx.cmd -y hostinger-api-mcp` (Mac/Linux `npx`). Trigger sign-in with a harmless read (list websites); the browser may open in a different browser than usual. If nothing opens, one full app restart, then retry.
2. List domains; propose the one matching the brand, or a free temporary subdomain. The user chooses.
3. Zip the CONTENTS, not the folder: `Compress-Archive -Path .\index.html, .\assets -DestinationPath ..\site.zip -Force`
4. Create the website if needed, deploy the zip with the static deploy tool.

## Cloudflare Pages / Netlify

Drag-and-drop the deploy folder in their dashboard, or use their CLI if the user already has it set up. The user creates the account themselves.

## Verify live (before saying it's done)

- Page returns 200 over HTTPS; a new custom domain's certificate can take minutes, so re-check before calling it broken.
- A frame URL from each scene serves (`curl.exe -s -o NUL -w "%{http_code} %{size_download}\n" <url>`).
- Console clean; scrub every scene on the live URL.
- Receipts, measured not estimated: HTML+CSS+JS weight (tens of KB), load time (`performance.getEntriesByType('navigation')[0].loadEventEnd`), each scene's frame total and time to `is-ready`.
- The user tests on desktop and their own phone on their real connection.

Iterating is cheap: edit, re-deploy, re-verify with a string you know changed (caches lie).
