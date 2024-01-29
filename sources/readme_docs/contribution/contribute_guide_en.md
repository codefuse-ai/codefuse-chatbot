

Thank you for your interest in the Codefuse project. We warmly welcome any suggestions, opinions (including criticisms), comments, and contributions to the Codefuse project.

Your suggestions, opinions, and comments on Codefuse can be directly submitted through GitHub Issues.

There are many ways to participate in the Codefuse project and contribute to it: code implementation, test writing, process tool improvement, documentation enhancement, and more. We welcome any contributions and will add you to our list of contributors.

Furthermore, with enough contributions, you may have the opportunity to become a Committer for Codefuse.

For any questions, you can contact us for timely answers through various means including WeChat, Gitter (an instant messaging tool provided by GitHub), email, and more.


## Getting Started
If you are new to the Codefuse community, you can:
- Follow the Codefuse GitHub repository.
- Join related WeChat groups for Codefuse to ask questions at any time;

Through the above methods, you can stay up-to-date with the development dynamics of the Codefuse project and express your opinions on topics of interest.


## Contributation Ways
This contribution guide is not just about writing code. We value and appreciate help in all areas. Here are some ways you can contribute:
- Documentation
- Issues
- Pull Requests (PR)

### Improve Documentation
Documentation is the main way for you to understand Codefuse and is also where we need the most help!

By browsing the documentation, you can deepen your understanding of Codefuse and also help you grasp the features and technical details of Codefuse. If you find any issues with the documentation, please contact us in time;

If you are interested in improving the quality of the documentation, whether it is revising an address of a page, correcting a link, or writing a better introductory document, we are very welcoming!

Most of our documentation is written in markdown format. You can directly modify and submit documentation changes in the docs/ directory on GitHub. For submitting code changes, please refer to Pull Requests.

### If You Discover a Bug or Issue
If you discover a bug or issue, you can directly submit a new Issue through GitHub Issues, and someone will handle it regularly. For more details, see Issue Template.[Issue Template](#issue-template)

You can also choose to read and analyze the code to fix it yourself (it is best to communicate with us before doing so, as someone might already be working on the same issue), and then submit a Pull Request.

### Modify Code and Submit a PR (Pull Request)
You can download the code, compile, install, and deploy to try it out (you can refer to the compilation documentation to see if it works as you expected). If there are any issues, you can directly contact us, submit an Issue, or fix it yourself by reading and analyzing the source code. For more details, see[Contribution](#contribution)

Whether it's fixing a bug or adding a feature, we warmly welcome it. If you wish to submit code to Doris, you need to fork the code repository to your project space on GitHub, create a new branch for your submitted code, add the original project as an upstream, and submit a PR. The method for submitting a PR can be referenced in the Pull Request documentation.


## Issue Type
Issues can be categorized into three types:
- Bug: Issues where code or execution examples contain bugs or lack dependencies, resulting in incorrect execution.
- Documentation: Discrepancies in documentation, inconsistencies between documentation content and code, etc.
- Feature: New functionalities that evolve from the current codebase.

## Issue Template
### Issue: Bug Template

**Checklist before submitting an issue**
<br>Please confirm that you have checked the document, issues, discussions (GitHub feature), and other publicly available documentation.
- I have searched through all documentation related to Codefuse.
- I used GitHub search to find a similar issue, but did not find one.
- I have added a very descriptive title for this issue.

**System Information**
<br>Please confirm your operating system, such as mac-xx, windows-xx, linux-xx.

**Code Version**
<br>Please confirm the code version or branch, such as master, release, etc.

**Problem Description**
<br>Describe the problem you encountered, what you want to achieve, or the bug encountered during code execution.

**Code Example**
<br>Attach your execution code and relevant configuration to facilitate rapid intervention and reproduction.

**Error Information, Logs**
<br>The error logs and related information after executing the above code example.

**Related Dependencies**
<br>Taking the chatbot project as an example:
- connector
- codechat
- sandbox
- ...


### Issue: Documentation Template

**Issue with current documentation:**
<br>Please point out any problems, typos, or confusing points in the current documentation.

**Idea or request for content**
<br>What do you think would be a reasonable way to express the documentation?

### Issue: Feature Template

**Checklist before submitting an issue**
<br>Please confirm that you have checked the document, issues, discussions (GitHub feature), and other publicly available documentation.
- I have searched through all documentation related to Codefuse.
- I used GitHub Issue search to find a similar issue, but did not find one.
- I have added a very descriptive title for this issue.

**Feature Description**
<br>Describe the purpose of this feature.

**Related Examples**
<br>Provide references to documents, repositories, etc., Please provide links to any relevant GitHub repos, papers, or other resources if relevant.

**Motivation**
<br>Describe the motivation for this feature. Why is it needed? Provide enough context information to help understand the demand for this feature.

**Contribution**
<br>How you can contribute to the building of this feature (if you are participating).



## Contribution

### Pre-Checklist
- First, confirm whether you have checked the document, issue, discussion (GitHub features), or other publicly available documentation.
- Find the GitHub issue you want to address. If none exists, create an issue or draft PR and ask a Maintainer for a check
- Check for related, similar, or duplicate pull requests
- Create a draft pull request
- Complete the PR template for the description
- Link any GitHub issue(s) that are resolved by your PR

### Description

A description of the PR should be articulated in concise language, highlighting the work completed by the PR. See specific standards at[Commit Format Specification](#Commit-Format-Specification)

### Related Issue
#xx if has

### Test Code with Result
Please provide relevant test code when necessary.



## Commit Format Specification
A commit consists of a "title" and a "body." The title should generally be in lowercase, while the first letter of the body should be uppercase.

### Title
The title of the commit message: `[<type>](<scope>) <subject> (#pr)`


### Type - Available Options

本次提交的类型，限定在以下类型（全小写）
- fix: Bug fixes
- feature: New features
- feature-wip: Features that are currently in development, such as partial code for a function.
- improvement: Optimizations and improvements to existing features
- style: Adjustments to code style
- typo: Typographical errors in code or documentation
- refactor: Code refactoring (without changing functionality)
- performance/optimize: Performance optimization
- test: Addition or fix of unit tests
- deps: Modifications to third-party dependencies
- community: Community-related changes, such as modifying Github Issue templates, etc.

Please note:

If multiple types occur in one commit, add multiple types.

If code refactoring leads to performance improvement, both [refactor][optimize] can be added.

Other types not listed above should not appear. If necessary, new types must be added to this document.

### Scope - Available Options
The scope of the modules involved in the current submission. Due to the multitude of functional modules, only a few are listed here, and this list will be updated continuously based on needs.

For example, using a chatbot framework:
connector
codechat
sandbox
...

Please note:

Try to use options that are already listed. If you need to add new ones, please update this document promptly.

### Subject Content
The title should clearly indicate the main content of the current submission.


## Example
comming soon


## Reference
[doris-commit-format](https://doris.apache.org/zh-CN/community/how-to-contribute/commit-format-specification)