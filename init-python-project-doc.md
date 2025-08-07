# Initialize Python Project Documentation

## Tools used
- Pyenv - to manage different python versions
- Poetry - to manage project dependencies
- Doppler - to manage secrets, so that code can be pushed to Github and exposed publicly without exposing secrets

## Create your project folder and set local Python
Project name: `my-project`

```bash
mkdir my-project
cd my-project
pyenv local 3.12.8
```

This writes a .python-version file so that every time you cd in, pyenv uses 3.12.8

## Initialize Git

```bash
git init
```

### Set Git Username and Email

```bash
git config user.name neocypher
git config user.email "5590838+neocypher-x@users.noreply.github.com"
```

## Create README

```bash
touch README.md
```

The readme is needed for `poetry install` to work

## Poetry

**Configure Poetry to create in-project venvs**

```bash
poetry config virtualenvs.in-project true
```

**Initialize the project with Poetry**

```bash
poetry init \
    --name my-project \
    --no-interaction
```

This creates a `pyproject.toml` with your project name.

**Create package directory (src layout)**

```bash
# NOTE: convert - to _, so my-project becomes my_project
mkdir -p src/my_project && touch src/my_project/__init__.py
```

This sets up the root package so that Poetry can build and install your project in package‑mode.

**Install dependencies**

```bash
poetry install
```

This will create a `.venv/` directory inside your project.

**Add doppler-env package**

```bash
poetry add doppler-env
```

This package is required for doppler to automatically inject secrets into your Python runtime. Reference: https://docs.doppler.com/docs/vscode-python

**Enter the virtual environment**

```bash
poetry shell
```

## Create .gitignore

**Add a `.gitignore`**

```gitignore
*.pyc

.DS_Store
.python-version

.venv
```

## Create initial commit

```bash
git add .
git commit -m "initial commit"
```

## Setup Github SSH Credentials For Project

```bash
ssh-add ~/.ssh/id_personal
```

## Create a remote repository and Push to Github

1. Go to https://github.com/new
2. Name the repo `my-project` (no README or license; you already have those locally).
3. Click **Create repository**.
4. Copy the “…or push an existing repository from the command line” snippet.
5. The first command will look like
`git remote add origin git@github.com:username/my-project.git`. Replace `github.com` with `github-personal` to get `git remote add origin git@github-personal:username/my-project.git`
6. Run the rest of the commands as is

## Manage Secrets

Verify Doppler is logged in and is pointing to Workplace

```bash
> doppler me
┌────────────────────────────┬──────┬──────────────────────────────────┬───────────────┬──────────────────────────────────────┬──────────────────────────┬──────────────────────────┐
│ NAME                       │ TYPE │ WORKPLACE                        │ TOKEN PREVIEW │ SLUG                                 │ CREATED AT               │ LAST SEEN AT             │
├────────────────────────────┼──────┼──────────────────────────────────┼───────────────┼──────────────────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Christophers-MacBook-Pro-2 │ cli  │ Workplace (9913b3d2e5761ffe2bfe) │ dp.ct…FBi5QB  │ 73c4aa14-e6e7-4d4b-9f3f-3642df6242e0 │ 2025-08-04T05:19:59.385Z │ 2025-08-04T05:43:04.345Z │
└────────────────────────────┴──────┴──────────────────────────────────┴───────────────┴──────────────────────────────────────┴──────────────────────────┴──────────────────────────┘
```

If it's not logged in or already pointing to the correct workplace, then change directory to the project or desired directory, and run:

```bash
doppler login --scope=./
```

Notice `--scope` keeps the doppler login scoped to the working directory.

## Setup VSCode Launch Configuration

Create file `.vscode/launch.json`

Paste the following:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONUNBUFFERED": "1",
                "DOPPLER_ENV": "1",
                "DOPPLER_ENV_COMMAND": "doppler secrets download --no-file --format env -c dev -p main"
            },
        }
    ]
}
```

`DOPPLER_ENV` and `DOPPLER_ENV_COMMAND` are required for the `doppler-env` package installed earlier to inject secrets into your Python runtime.