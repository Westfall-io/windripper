# Windripper

Windripper listens for Harbor registry webhook push events, queries Harbor for
artifact manifest and config details (preferring linux/amd64), persists
container and artifact/digest metadata into PostgreSQL, and posts a small
notification to a Windstorm webhook for downstream processing.

**Quick overview**

- Language: Python
- Purpose: Ingest Harbor `PUSH_ARTIFACT` webhooks, store container/commit
  metadata, and notify `WINDSTORMHOST`.

**Requirements**

- Python 3.9+ (verify compatibility with your environment)
- Packages (from `requirements.txt`): `requests`, `SQLAlchemy`, `fire`, and
  the PostgreSQL DB driver (e.g. `psycopg2-binary`).

Install dependencies (example):

```bash
python -m pip install -r requirements.txt
```

**Configuration (environment variables)**

Windripper reads the following environment variables from `src/env.py`:

- `SQLHOST` — database host and port (default: `localhost:5432`).
- `DBUSER` — database user (default: `postgres`).
- `DBPASS` — database password (default: `mysecretpassword`).
- `DBTABLE` — database name (default: `sysml2`).
- `HARBORHOST` — Harbor API base URL (default: `http://harbor-core.harbor/api/v2.0`).
- `HARBORUSER` — Harbor API username (default: `admin`).
- `HARBORPASS` — Harbor API password (default: `Harbor12345`).
- `WINDSTORMHOST` — URL to post notifications after a DB update
  (default: `http://windstorm-webhook-eventsource-svc.argo-events:12000/windstorm`).

Set these variables in your environment or container before running.

**Database schema (ORM models)**

Defined in `src/main.py` using SQLAlchemy dataclass-style models:

- `Containers` (table: `containers`)
  - `id` (PK)
  - `resource_url` — original Harbor resource (e.g. `host/project/repo:tag`)
  - `host`, `project`, `image`, `tag`
  - `project_id`, `image_id` — numeric IDs retrieved from Harbor when available

- `Container_Commits` (table: `container_commits`)
  - `id` (PK)
  - `containers_id` — FK to `Containers.id`
  - `digest` — artifact digest (sha256)
  - `cmd` — serialized `Cmd` configuration from image config
  - `working_dir` — `WorkingDir` from image config
  - `date` — observation timestamp

**How it works (behavior)**

1. The CLI entrypoint is `main(wh_type, wh_resource_url, wh_digest)` (invoked
   via `fire.Fire(main)` when run as a script).
2. Only `PUSH_ARTIFACT` webhooks are processed. `wh_resource_url` is expected
   to be `host/project/repo:tag`. `wh_digest` should be of the form `sha256:...`.
3. The code checks/creates a `Containers` record for the given `project/image/tag`.
4. It calls Harbor API to find a linux/amd64 child manifest for the artifact
   digest, fetches the manifest's config, and extracts `Cmd` and `WorkingDir`.
5. The artifact digest and extracted metadata are saved in
   `container_commits`. If `project_id`/`image_id` are available, they are
   stored back to the `containers` row.
6. A JSON POST is sent to `WINDSTORMHOST` with a payload containing `container_id`.

**Running locally**

Example (invoke the `main` entry manually):

```bash
# from project root
python -m src.main --wh_type PUSH_ARTIFACT --wh_resource_url "registry/proj/repo:tag" --wh_digest "sha256:..."
```

(Or run the script directly in your environment; the module uses `fire` to
expose the `main` function as a CLI.)

**Harbor API notes**

- The code expects Harbor API responses under `/api/v2.0/projects/.../repositories/.../artifacts/...`.
- It attempts to locate a platform-specific child manifest for `linux/amd64`.
- If the artifact has no appropriate child manifest, the code returns an
  empty info dict and the webhook processing stops for that artifact.

**Files of interest**

- `src/env.py` — environment/configuration constants.
- `src/main.py` — main logic, ORM models, Harbor API integration, DB I/O.

**Contributing & License**

This repository includes a NOTICE and is distributed under the GNU Affero
General Public License (see project root). Follow existing code style when
contributing and run tests locally if you add behavior.

---

If you want, I can:
- add example unit tests,
- add a Dockerfile run example, or
- commit the README and run a linter/formatter.
