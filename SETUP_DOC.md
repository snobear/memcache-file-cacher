# Zapier SRE Skills Interview

## Project Setup

Thanks for requesting to take our Infrastructure Engineering skills interview. At Zapier, we try to make the interviewing process as painless and transparent as possible. For engineering, we avoid whiteboarding sessions and quizzes on implementing red-black trees. Instead, we opt to provide a real world scenario and a small project for you to complete. 

Before you begin the project, here are a few things you’ll need set up:

### 1. Clone this repo

```bash
git clone https://github.com/zapier-interviews/yourreponame.git
cd yourreponame
```

Your repo will be named something like `interview-yourname-abc123`. Use the real repo name in place of `yourreponame`. Use SSH or HTTPS, whatever works for you.

### 2. Create a branch for your project

All work for the project should be done on a branch named `project`, and after completing your project, you'll create a pull request within Github to merge it to `master`.

```bash
git checkout -b project
```

### 3. Set up Your Development Environment

Setup up your preferred development environemnt. You should use whatever language you are the most comfortable with for this test whether it's golang, python, ruby, rust, etc. But here it is important to get the basic structure for a project setup so you can work effeciently.


### 4. You’ll need to set up a working local Memcached server.

You can set this up via Docker or whichever way you want. Once installed, you'll want make sure you set the `-m 1000` option on the server to allow you to store up to 1000MB of data in the server.

If you're running Memcache from the command line, the command would look like this:

```bash
memcached -m 1000
```

### 5. You’ll need to make sure you can talk between your development environment and Memcached.

The easiest way to test this is to write a small script that sets and gets a key to make sure everything works and you can read from and write to Memcache.

### 6. Push your project setup to Github

First, be sure to add a .gitignore file to prevent committing your environment.

```bash
echo "env" > .gitignore
```

Then, push your project setup to your private Zapier repo to make sure everything is working.

```bash
git add .
git commit -m "project setup"
git push -u origin project
```

If you're reading this file, everything should be fine with permissions. But, if for some reason this doesn't work, let us know!

### 7. Prepare for your project

Once you get your project, you can use any additional libraries or resources you like as long as that resource does not solve the problem for you completely. 

---

**It is essential** to have these items completed ahead of time. You need to have this setup complete before you start the skills interview so you can spend most of your available time coding instead of dealing with configuring the setup.

---

### 8. Begin!

Head over to [this page and fill out the form](https://zapier.wufoo.co.uk/forms/zapier-engineering-skills-test/) to get started with your project. Once you submit the form, a `PROJECT_SPEC.md` file will be added to the `project` branch of your repository with details of the project.


