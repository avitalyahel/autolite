# autolite (v0.2)

![alt text](https://github.com/avitalyahel/autolite/blob/master/python-3.100x34.png "python 3")

### *Phase:* Alpha

## Mission

**Simple and to-the-point automation management.**

## Audience

Software development groups, small or big, who favor simplicity and need scalability.

## Concept

***Leave definitions to CLI & procedures to scripts - focus on schduling.***

### Terminal UI

Automation definition includes: system pool, tasks, schduling & notifications. Here in autolite, all these are done by scripting and CLI  *<span style="color:RoyalBlue">[Future: Web UI for monitoring and launching]</span>*.

### Objects: Tasks & Systems

* **Task** basic attributes are: Command (executable), Schedule & State.
* **System** basic attributes are: Name, User & Installer (executable).

The two are not directly connected, rather may be associated by scripts.

## Getting Started

#### 1) Clone the packge & install from: [GitHub](http://github.com/avitalyahel/autolite)

```
git clone http://github.com/avitalyahel/autolite
cd autolite
./install
```

#### 2) Set first shared Db, for multiple users

```
echo "db_path: /mnt/shared/autolite.db" > settings-user.yaml
```

This shall link your clone to shared Db at `/mnt/shared/autolite.db`.

#### 3) Trigger autolite's Runner automatically, one per Db. On Linux, add cron job to `crontab`:

```
crontab -e
```

```
* * * * * $AUTOLITE_DIR/runner >/dev/null 2>&1
```

This shall execute `autolite/runner` every minute, and let **autolite** manage scheduling & notifications.

#### 4) Define your first task:

```
autolite task create My-First-Task --continuous --commmand "echo Hello, World!"
```

Shall announce *"Hello, World!"* every minute.

#### 5) Define your first system:

```
autolite system create s1 --installer "./system-install" --monitor "./system-status"
```

Shall allow: `autolite system s1 install`

## Runner Logic

autolite Runner normally executes in the background, applying the following algorithm:

<span style="font-size: large; font-style: italic; font-family: serif">
cron trigger: <br>
&emsp; start every ready and able task. <br>
&emsp; for every running task process: <br>
&emsp; &emsp; if completed, set task status to Pass of Fail by process return code. <br>
&emsp; &emsp; if timed-out, abort the process and Fail the task. <br>
</span>

As mentioned above, there is no reference system status; if required then implement with task condition or command.

## Usage: the CLI

### Basic Task Definition

    $ autolite task create Full-Regression --daily --command "./run-tests full"
    $ autolite task create CI --continuous --command "run-tests sanity"
    $ autolite task list
    NAME             STATE
    Full-Regression  pending
    CI               pending
    $ autolite task list -l
    NAME             COMMAND           PARENT  SETUP  LAST  SCHEDULE    EMAIL  STATE    TEARDOWN
    Full-Regression  run-tests full                         daily              pending
    CI               run-tests sanity                       continuous         pending
    $ autolite task set Full-Regression email nightly-officer@mine.com
    $ autolite task set CI email ci-officer@mine.com
    $ autolite task set CI parent Full-Regression
    $ autolite task list -r
    Full-Regression: pending (1 subtasks: 1 pending)
      CI: pending

### Basic System Definition

    $ autolite system create sys1 --installer "./install sys1" --cleaner "./clean sys1"
    $ autolite system create sys2 --installer "./install sys2" --cleaner "./clean sys2"
    $ autolite system list
    NAME  USER
    sys1
    sys2
    $ autolite system list -l
    NAME  CONFIG  INSTALLER       IP  CLEANER       USER  MONITOR
    sys1          ./install sys1      ./clean sys1
    sys2          ./install sys2      ./clean sys2
    
### Task scripts may access the system pool

    autolite system acquire sys1  # sys1's user set to the active user
    autolite system install       # executes sys1's installer
    ...
    autolite system releasee      # sys1's user is cleared

### Settings

The tool's configuration is done by `settings` files in YAML format:

	$ cd autolite
	$ ls settings-*.yaml
	settings-default.yaml  settings-user.yaml
	$ cat settings-default.yaml
	db_path: ./autolite.db
	email:
	    server: smtp.gmail.com
	    port: 587
	    username: ''
	    password: ''
	
`settings-default.yaml` comes with the installation, is read-only and specify the entire paramater set.

`settings-user.yaml` is designated to be created by user, copying from the default settings and overriding them. User's settings file may contain the entire setting set, or a subset.

**autolite** reads first the default settings, and then overrides with users's settings.
	
### Sharing the Db

To share **autolite**'s Db with other users, each user need to install separately and then the Db file need to be put in a shared location, typically on NFS. Then each user may set the `db_path` parameter to that path.

Resetting the Db is done simply by deleting the Db file. Over NFS, permissions may be set so only selected users may delete - or modify - the Db file.

### Full Help
```
autolite control tool.

Usage:
    autolite task list [-l | -J | -Y] [-r] [-v | -vv]
    autolite task create <name> (--daily | --continuous | --never) [-v | -vv]
                     [--command=<exe>] [--setup=<exe>] [--teardown=<exe>]
    autolite (task | system) (read | delete) <name> [-v | -vv]
    autolite task set <name> schedule (--daily | --continuous | --never) [-v | -vv]
    autolite task set <name> (setup | command | teardown) <exe> [-v | -vv]
    autolite task set <name> parent <parent> [-v | -vv]
    autolite task set <name> email <email> [-v | -vv]
    autolite task reset <name> [--force] [-v | -vv]
    autolite system list [-l | -J | -Y] [-v | -vv]
    autolite system create <name> [--ip <ip>] [-v | -vv]
                     [--installer=<exe>] [--cleaner=<exe>] [--monitor=<exe>] [--config=<exe>]
    autolite system set <name> ip <ip> [-v | -vv]
    autolite system set <name> (installer | cleaner | monitor | config) <exe> [-v | -vv]
    autolite system (acquire | install | clean | monitor | config) <name> [-v | -vv]
    autolite system release <name> [--force] [-v | -vv]
    autolite test [-- <arg>...] [-v | -vv]

Options:
    -h --help               Show this screen.
    --version               Show version.
    -v --verbose            Higher verbosity messages.
    -l --long               Table list long format.
    -J --JSON               List with JSON format.
    -Y --YAML               List with YAML format.
    -r --recursive          Task recursive listing, by lineage.
    --force                 Force the command.
    -D, --daily             Set task schedule to 'daily'.
    -C, --continuous        Set task schedule to 'continuous'.
    -N, --never             Set task schedule to 'never'.
    --command <exe>         Task command executable.
    --setup <exe>           Task setup executable (returns bool).
    --teardown <exe>        Task teardown executable.
    --installer <exe>       System installation executable.
    --cleaner <exe>         System cleaning executable.
    --monitor <exe>         System monitoring executable.
    --config <exe>          System configuration executable.
```

## Open Issues

The open issues are mangaged at [GitHub/issues](https://github.com/avitalyahel/autolite/issues).

