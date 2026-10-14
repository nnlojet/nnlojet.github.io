# Publish the NNLOJET website at nnlojet.github.io

This guide assumes a new, public website repository and a publishing branch
named `main`. You need Git locally, GitHub authentication for pushing, and
permission to create/configure repositories under the `nnlojet` account or
organisation. You do **not** need LaTeX locally to deploy: CI installs it.

## 1. Use the correct owner and repository name

The exact address requires:

```text
Owner:       nnlojet
Repository:  nnlojet.github.io
Branch:      main
Website:     https://nnlojet.github.io/
```

The repository's full name is `nnlojet/nnlojet.github.io`. Creating a
repository of that name under a different account does not give you the
NNLOJET hostname. GitHub permits only one user/organisation homepage per
account. Do not replace an existing website without reviewing it first.
See [GitHub's site-name rules][site-types].

## 2. Create an empty public repository

On GitHub, choose **New repository**, set **Owner** to `nnlojet`, and enter
**Repository name** `nnlojet.github.io`. Select **Public**. Do not initialise
with a README, .gitignore, or license; the archive already supplies its own
README and .gitignore. Create the repository.

A public repository is suitable for the free Pages setup described here.
The repository itself exposes all committed sources, not only the files that
Pages serves, so review the contents before pushing.

An existing repository must instead be cloned and updated without replacing
its Git history; see the alternative commands below.

## 3. Unpack, commit, and push

Run these commands in the directory containing the downloaded tarball. The
archive creates one directory called `nnlojet.github.io`. Run `git init`
**inside** that directory; do not put that entire directory inside another
repository.

```bash
tar -xzf nnlojet.github.io.tar.gz
cd nnlojet.github.io

# Hidden .github/ and .gitignore entries must be present.
ls -la

git init -b main
git add .
git status --short
git commit -m "Add NNLOJET website and manual [skip ci]"
git remote add origin https://github.com/nnlojet/nnlojet.github.io.git
git push -u origin main
```

Use your normal GitHub Git authentication. An SSH-configured account can use
`git@github.com:nnlojet/nnlojet.github.io.git` as the remote instead. These
credentials are for your local push, not a secret to add to the workflow.

The initial `[skip ci]` avoids running the build before Pages is configured.
It skips this commit's push-triggered workflow only. The manual run in step 7
will still work. Do not include `[skip ci]` in ordinary updates.
See [GitHub's skip instructions][skip].

The GitHub repository root must directly contain:

```text
.github/workflows/pages.yml
.gitignore
README.md
SETUP.md
VALIDATION.md
MANUAL-SOURCES.sha256
manual/
web/
```

### Alternative: adding to an existing repository

Do not force-push or run `git init` over a separate existing history. From
a clean working directory, with the tarball in the parent of the new clone:

```bash
git clone https://github.com/nnlojet/nnlojet.github.io.git
cd nnlojet.github.io
git switch main
# Review/back up existing files before this extraction; matching files are replaced.
tar -xzf ../nnlojet.github.io.tar.gz --strip-components=1
git status --short
git diff
git add .
git commit -m "Add NNLOJET website and manual [skip ci]"
git push
```

Merge `.gitignore` or other existing repository configuration deliberately
rather than discarding existing rules. Remove superseded website workflows
only after reviewing them.

## 4. Enable the required GitHub Actions

Open **Settings → Actions → General**. Ensure Actions is enabled and that
GitHub-authored actions are allowed. The bundled workflow uses only:

```text
actions/checkout
actions/configure-pages
actions/upload-pages-artifact
actions/deploy-pages
```

Where an allowlist is used, choose **Allow OWNER, and select non-OWNER, actions
and reusable workflows**, then enable **Allow actions created by GitHub**.
The standard allow-all policy also works. Do not select a policy that allows
only actions authored inside NNLOJET: that would exclude the GitHub actions.

Under **Workflow permissions**, the restricted **Read repository contents
and packages permissions** default is sufficient. The YAML explicitly grants
`pages: write` and `id-token: write` to the deployment job only. There is no
need to enable general write access, PR approval by Actions, or create a
personal access token/deploy key for publication.

An organisation-wide policy can override repository settings. If it requires
full-length SHA pins for actions, retain that policy and replace the action
tags with their verified commit SHAs before running.
See [Actions settings][actions-settings] and [the Pages workflow contract][workflows].

## 5. Enable GitHub Pages

Open **Settings → Pages** and set:

```text
Build and deployment → Source: GitHub Actions
Custom domain:                   leave empty
```

Do not choose **Deploy from a branch**. Do not select Jekyll, install a
static-site template, or create a `gh-pages` branch. The workflow is already
committed, so ignore suggestions to create another workflow.

The `github.io` hostname needs no DNS changes and no `CNAME` file. HTTPS is
enforced for the default GitHub Pages domain; leave **Enforce HTTPS** enabled
where the checkbox is shown. See [publishing configuration][publishing] and
[HTTPS documentation][https].

## 6. Restrict the deployment environment to main

Open **Settings → Environments → github-pages**. If it does not yet exist,
choose **New environment**, name it `github-pages`, and configure it.

Under **Deployment branches and tags**, choose **Selected branches and tags**
and add one rule with **Ref type: Branch** and **Name pattern: main**.

For unattended publication, leave required reviewers and wait timers unset,
subject to your organisation's policies. Required reviewers deliberately
pause deployments for approval, so enabling them changes the workflow from
fully automatic to approval-gated. No environment secrets are needed.
See [GitHub's environment settings][environments].

## 7. Run the first publication

Open **Actions**, select **Build and publish NNLOJET website**, then click
**Run workflow**, select branch **main**, and run it. The workflow supports
`workflow_dispatch`, so a manual run works despite the initial skip marker.
See [manual workflow execution][manual-run].

The `build` job checks out sources, installs the document toolchain, builds
the PDF and HTML manual, assembles the site, checks local links/anchors, and
uploads `web/autogenerated/`. The separate `deploy` job publishes the result
to Pages. A failed build does not deploy.

The completed deployment shows its page URL. Verify:

```text
https://nnlojet.github.io/
https://nnlojet.github.io/manual.html
https://nnlojet.github.io/nnlojet-manual.pdf
```

Check the homepage, navigation, manual figures/equations, and external
software downloads in a normal browser. The included link checker checks
local HTML links, not availability of third-party services.

## 8. Normal updates

Edit ordinary page fragments in `web/`, shared CSS/template files, or manual
sources in `manual/`. Commit and push to `main`, or merge a reviewed PR there.

```bash
git add web/index.html
git commit -m "Update homepage"
git push
```

Every push to `main` builds and publishes automatically. PRs targeting `main`
build and validate without deploying; external-contributor runs may need
approval under your Actions policy. Generated files do not need committing.

## Software downloads: deliberate temporary HEPForge dependency

Neither uploaded archive contains the two software-release packages. This
complete website bundle uses the original host for those links:

```text
https://nnlojet.hepforge.org/nnlojet-v1.0.0.tar.gz
https://nnlojet.hepforge.org/nnlojet-v1.0.2.tar.gz
```

These URLs are the original relative links resolved against the old site
address. Access protection prevented independent verification of the legacy
downloads; test them in your browser before announcing the new site. The
website build does not download them and does not depend on their availability.

When public software releases are on GitHub, replace these `href` values in
`web/releases.html` with the real GitHub Release download URLs. The builder
already accepts external URLs; its Python code need not change. Alternatively,
supply genuine archives under `web/` and use relative download links; the
builder will copy them and fail clearly when such a local file is missing.
No fake or empty software packages are supplied.

## Optional local build

This is not required for deployment; GitHub installs these dependencies.
On Ubuntu 24.04:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends -y \
  latexmk texlive-latex-extra texlive-fonts-extra \
  texlive-fonts-recommended cm-super \
  poppler-utils python3-lxml

export PYTHON=/usr/bin/python3
bash web/make_manual.sh
"$PYTHON" web/update.py
"$PYTHON" web/check_site.py
"$PYTHON" -m http.server 8000 --bind 127.0.0.1 --directory web/autogenerated
```

Open `http://localhost:8000`. On another system, provide equivalent tools and
`lxml` in the selected Python environment. On macOS the manual conversion also
requires GNU sed; use `MYSED=gsed` with a full TeX installation.

`make_manual.sh` builds only into `_build/manual/` and never deletes source
`manual/`. `update.py` recreates only `web/autogenerated/`. Existing example
runcards and results are copied, not recomputed.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No workflow is listed | `.github/workflows/pages.yml` must be at the repository root and committed to the default `main` branch. Hidden directories must not be omitted. |
| First push did not build | Intentional for the first `[skip ci]` commit; use Run workflow after completing settings. |
| No Run workflow button | Ensure the workflow is on the default branch and you have write permission. Refresh the Actions page. |
| An action is forbidden | Repository/organisation Actions policy must permit GitHub-authored actions, including nested GitHub actions. |
| Pages reports not found or is disabled | Set Settings → Pages → Source to GitHub Actions, then run the workflow again. |
| Deployment awaits approval | Review protection rules on the `github-pages` environment. |
| Main is not permitted to deploy | Add the explicit Branch `main` rule in that environment. |
| Manual build fails | Open the Build PDF and HTML manual step; its LaTeX errors are in the job log. Do not disable the build or checker to publish partial output. |
| Missing local release archive | Restore the real local archive or change that href to a real external download URL. |
| Website has the wrong hostname or a repository suffix | Confirm owner `nnlojet`, repository `nnlojet.github.io`, and no custom domain. |
| Git push is rejected because the repository already has history | Clone it and apply the archive there; do not force-push the initial commands over existing work. |

Only website/manual source files belong in this repository. The source
Monte Carlo code can remain in a separate repository. Moving the website does
not automatically redirect the old HEPForge hostname; coordinate redirects
with that host separately.

## Official documentation (checked 2026-10-14)

[site-types]: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
[publishing]: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
[workflows]: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
[actions-settings]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
[environments]: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
[manual-run]: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
[skip]: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs
[https]: https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https
