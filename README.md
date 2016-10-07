# autolite (v0.2)

![alt text](http://github.com/avitalyahel/autolite/blob/master/python-3.100x34.png "python 3")

### *Phase:* Alpha

## Mission

**Simple & to-the-point automation management.**

## Audience

**Software development groups, small or big, who favor simplicity and need scalability.**

## Concept

**Leave definitions to CLI & procedures to scripts - focus on schduling.**

### Terminal UI

Automation definition includes: **system pool**, **tasks**, **schduling** & **notifications**. Here in **autolite**, all these are done by scripting and CLI  *<span style="color:RoyalBlue">[Future: Web UI for monitoring and launching]</span>*.

### Objects: Tasks & Systems

* **Task** basic attributes are: **command** (executable), **schedule** & **state** *<span style="color:RoyalBlue">[WIP: task hierarchial launch & state summary (tracking: [here](https://github.com/avitalyahel/autolite/issues/20))]</span>*.
* **System** basic attributes are: **name**, **user** & **installer** (executable).

The two are not directly connected, rather may be associated by scripts.

## Installation

Current method of installation is by [GitHub](http://github.com/avitalyahel/autolite):

(1) Clone the packge & install:

```
$ git clone http://github.com/avitalyahel/autolite
$ cd autolite
$ install
```

(2) On Linux *<span style="color:RoyalBlue">[Future: on Win32]</span>*, add **autolite** cron job to `crontab`:

`$ crontab -e`

```
* * * * * $AUTOLITE_DIR/crontab_job >/dev/null 2>&1
```
This shall execute `autolite/crontab_job` every minute, and let **autolite** manage scheduling & notifications.

## Usage: the CLI

### Basic Task Definition

    $ actl task create Full-Regression --daily --command "./run-tests full"
    $ actl task create CI --continuous --command "run-tests sanity"
    $ actl task list
    NAME             STATE
    Full-Regression  pending
    CI               pending
    $ actl task list -l
    NAME             COMMAND           PARENT  SETUP  LAST  SCHEDULE    EMAIL  STATE    TEARDOWN
    Full-Regression  run-tests full                         daily              pending
    CI               run-tests sanity                       continuous         pending
    $ actl task set Full-Regression email nightly-officer@mine.com
    $ actl task set CI email ci-officer@mine.com

### Basic System Definition

    $ actl system create sys1 --installer "./install sys1" --cleaner "./clean sys1"
    $ actl system create sys2 --installer "./install sys2" --cleaner "./clean sys2"
    $ actl system list
    NAME  USER
    sys1
    sys2
    $ actl system list -l
    NAME  CONFIG  INSTALLER       IP  CLEANER       USER  MONITOR
    sys1          ./install sys1      ./clean sys1
    sys2          ./install sys2      ./clean sys2
    
### Task scripts may access the system pool

    actl system acquire sys1  # sys1's user set to the active user
    actl system install       # executes sys1's installer
    ...
    actl system releasee      # sys1's user is cleared

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

To share **autolite**'s Db with other users, each user need to install separately and then the Db file need to be put in a shared location, typically on the NFS. Then each user may set the `db_path` parameter to that location.

Resetting the Db is done simply by deleting the Db file. Over NFS, permissions may be set so only selected users may delete - or modify - the Db file.

### Full Help
```
autolite control tool.

Usage:
    actl task list [-l | -J | -Y] [-r] [-v | -vv]
    actl task create <name> (--daily | --continuous | --never) [-v | -vv]
                     [--command=<exe>] [--setup=<exe>] [--teardown=<exe>]
    actl (task | system) (read | delete) <name> [-v | -vv]
    actl task set <name> schedule (--daily | --continuous | --never) [-v | -vv]
    actl task set <name> (setup | command | teardown) <exe> [-v | -vv]
    actl task set <name> parent <parent> [-v | -vv]
    actl task set <name> email <email> [-v | -vv]
    actl task reset <name> [--force] [-v | -vv]
    actl system list [-l | -J | -Y] [-v | -vv]
    actl system create <name> [--ip <ip>] [-v | -vv]
                     [--installer=<exe>] [--cleaner=<exe>] [--monitor=<exe>] [--config=<exe>]
    actl system set <name> ip <ip> [-v | -vv]
    actl system set <name> (installer | cleaner | monitor | config) <exe> [-v | -vv]
    actl system (acquire | install | clean | monitor | config) <name> [-v | -vv]
    actl system release <name> [--force] [-v | -vv]
    actl test [-- <arg>...] [-v | -vv]

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

The open issues are mangaged at [GitHub/issues](https://github.com/avitalyahel/autolite/issues) as well.

