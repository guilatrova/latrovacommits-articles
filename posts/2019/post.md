---
tags: [DevOps, Ubuntu, Productivity]
---

# As a DevOps here's how you should be doing your backups and getting back to work quickly

As a DevOps engineer, there's nothing that I do today that I don't consider how I can automate to be faster and more productive and
recently I noticed everything I have always been doing after formatting my dev notebook, which is pretty much:

1. Backup all my data and settings
2. (Re)Install new OS
3. Restore my backup
4. Set up every single configuration back

Since Ubuntu 19.10 is already there (I have been using 18.04 for a while), I finally found a moment for trying this out.

The main reason for doing this is to migrate between linux dists smoothly and get back to work fast without having to spend the whole weekend setting things up.

That's why I'm going to show you how Ansible can speed you up on setting your environment. Hopefully, it will give some insights on why DevOps is a MUST for every company (and regular developer) nowadays that want to increase productivity. 

If you're curious to see the final result, head out to https://github.com/guilatrova/base-dev-setup/

## Why Ansible?

We're going to have several actionable steps that I might want to rerun several times (for backing up my data again or updating a version of a tool), and playbooks fit this perfectly.

From their official site, they claim:
> Ansible is a universal language, unraveling the mystery of how work gets done. Turn tough tasks into repeatable playbooks. Roll out enterprise-wide protocols with the push of a button.


## Backing up all my data with a single command

Rules the playbook should follow to be useful:

**1. Should be stored in the Cloud**
I don't want to worry about having any free space in pen drives or bothering to carry them around. I like having my data always available to me no matter where I am. I decided to go with AWS S3 for this.

**2. Customizable**
It should be extremely easy to add and remove system paths from my backup. I decided to go by setting up a list of variables, that would follow the most simple format possible:

```yaml
{
    remote: CLOUD_FOLDER,
    local: LOCAL_FOLDER"
}
```

**3. Easy to trigger**
I should be able to rerun it as many times as I want with a single command, for this case, it would be: `ansible-playbook playbooks/backup.yml`.

### Result

It's so incredibly simple with Ansible since we can just use `s3_sync` module: https://github.com/guilatrova/base-dev-setup/blob/master/roles/backup/tasks/main.yml

Also, you can filter files (instead of backing up the whole folder contents): https://github.com/guilatrova/base-dev-setup/blob/master/vars/backup.example.yml

I did my best to back up my keybindings. I couldn't make it work, though.

## Restoring all data back

Well, just backing up and not getting it back as easy as before sounds like a problem to me. That's why the playbook for restoring the data should follow the same logic with additional concerns:

**1. Restored files should go back to their original place**
I don't want to worry about moving files. If I have to do any backup step manually, it's not good enough.

**2. Handle cases where restored files live in a protected directory**
There are a couple of files, binaries and scripts I like to keep under `/usr/local/bin`, but this directory has writing protection by default. The same backup vars will handle a `sudo: true` prop to specify it requires proper permissions to write to that place.

**3. Packages and binaries should be installed or updated**

**4. Configs might be restored**


---

## What else can I do with Ansible?

Also, I really believe it's a healthy behavior to fresh install all your system from time to time, so hopefully such tool can help you start a good habit and get it done really quick.
After doing this process a couple times for Ubuntu 18.04, I started taking notes about everything that I do frequently: install this, install that, set this up, etc.

Across all those reinstalls I made, I was developing and contributing to some solutions in my current company to manage cloud resources with both terraform and ansible, I realized that ansible would do a perfect work for what I want on every new system:

Load my backup
Install packages and apps I use daily
Set up my personal keybindings and preferences

Introduction to Ansible
Let me start this giving you some overview about how ansible works...

Storing and loading backups
That's a tedious task of copying and pasting somewhere (often to a regular pendrive).

As soon as you know which file paths matter for you, you can easily automate this flow. For that job I decided to use S3, since I'm really not expecting to access any of this on cloud, but just storing and restoring, I think it does the job :)

Installing packages and apps
