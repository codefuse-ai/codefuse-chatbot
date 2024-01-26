非常感谢您对 Codefuse 项目感兴趣，我们非常欢迎您对 Codefuse 项目的各种建议、意见（包括批评）、评论和贡献。

您对 Codefuse 的各种建议、意见、评论可以直接通过 GitHub 的 Issues 提出。

参与 Codefuse 项目并为其作出贡献的方法有很多：代码实现、测试编写、流程工具改进、文档完善等等。任何贡献我们都会非常欢迎，并将您加入贡献者列表.

进一步，有了足够的贡献后，您还可以有机会成为 Codefuse 的 Committer。

任何问题，您都可以联系我们得到及时解答，联系方式包括微信、Gitter（GitHub提供的即时聊天工具）、邮件等等。


## 初次接触
初次来到 Codefuse 社区，您可以：

- 关注 Codefuse Github 代码库
- 加入 Codefuse 相关的微信群 随时提问；
通过以上方式及时了解 Codefuse 项目的开发动态并为您关注的话题发表意见。


## 贡献方式
这份贡献指南并不仅仅关于编写代码。我们重视并感激在各个领域的帮助。以下是一些您可以贡献的方式
- 文档
- Issue
- PR

### 改进文档
文档是您了解 Codefuse 的最主要的方式，也是我们最需要帮助的地方！

浏览文档，可以加深您对 Codefuse 的了解，也可以帮助您理解 Codefuse 的功能和技术细节，如果您发现文档有问题，请及时联系我们；

如果您对改进文档的质量感兴趣，不论是修订一个页面的地址、更正一个链接、以及写一篇更优秀的入门文档，我们都非常欢迎！

我们的文档大多数是使用 markdown 格式编写的，您可以直接通过在 GitHub 中的 docs/ 中修改并提交文档变更。如果提交代码变更，可以参阅 Pull Request。

### 如果发现了一个 Bug 或问题
如果发现了一个 Bug 或问题，您可以直接通过 GitHub 的 Issues 提一个新的 Issue，我们会有人定期处理。详情见[Issue Template](#issue-template)

您也可以通过阅读分析代码自己修复（当然在这之前最好能和我们交流下，或许已经有人在修复同样的问题了），然后提交一个 Pull Request。

### 修改代码和提交PR（Pull Request）
您可以下载代码，编译安装，部署运行试一试（可以参考编译文档，看看是否与您预想的一样工作。如果有问题，您可以直接联系我们，提 Issue 或者通过阅读和分析源代码自己修复。详情见[Contribution](#contribution)

无论是修复 Bug 还是增加 Feature，我们都非常欢迎。如果您希望给 Doris 提交代码，您需要从 GitHub 上 fork 代码库至您的项目空间下，为您提交的代码创建一个新的分支，添加源项目为upstream，并提交PR。 提交PR的方式可以参考文档 Pull Request。




## Issue Type
Issue分为三种类型
- Bug: 代码或者执行示例存在bug或缺少依赖导致无法正确执行
- Documentation：文档表述存在争议、文档内容与代码不一致等
- Feature：在当前代码基础继续演进的新功能

## Issue Template
### Issue: Bug Template

**提交Issue前的确认清单** 
<br>要先确认是否查看  document、issue、discussion(github 功能) 等公开的文档信息
- 我搜索了Codefuse相关的所有文档。
- 我使用GitHub搜索寻找了一个类似的问题，但没有找到。
- 我为这个问题添加了一个非常描述性的标题。

**系统信息** 
<br>确认系统，如 mac -xx 、windwos-xx、linux-xx

**代码版本**
<br>确认代码版本或者分支，master、release等

**问题描述**
<br>描述您碰到的问题，想要实现的事情、或代码执行Bug

**代码示例**
<br>附上你的执行代码和相关配置，以便能够快速介入进行复现

**报错信息、日志**
<br>执行上述代码示例后的报错日志和相关信息

**相关依赖的模块**
<br>以chatbot项目为例
- connector
- codechat
- sandbox
- ...


### Issue: Documentation Template
**Issue with current documentation:**
<br>请帮忙指出当前文档中的问题、错别字或者令人困惑的地方

**Idea or request for content**
<br>您觉得合理的文档表述方式应该是什么样的


### Issue: Feature Template
**提交Issue前的确认清单** 
<br>要先确认是否查看  document、issue、discussion(github 功能) 等公开的文档信息
- 我搜索了Codefuse相关的所有文档。
- 我使用GitHub Issue搜索寻找了一个类似的问题，但没有找到。
- 我为这个问题添加了一个非常描述性的标题。

**功能描述**
<br>描述这个功能作何用途

**相关示例**
<br>提供参考的文档、仓库等信息，Please provide links to any relevant GitHub repos, papers, or other resources if relevant.

**动机**
<br>描述下这个feature的动机，为什么需要这个功能，提供足够的上下文信息帮助理解这个feature的诉求

**Contribution**
<br>你如何参与到这个feature的构建（如果参与的话）



## Contribution

### Pre-Checklist
- 要先确认是否查看  document、issue、discussion(github 功能) 等公开的文档信息
- 找到你想处理的GitHub问题。如果不存在，创建一个问题或草案PR，并请求维护者进行检查。
- 检查相关的、相似的或重复的拉取请求。
- 创建一个草案拉取请求。
- 完成PR模板中的描述。
- 链接任何被你的PR解决的GitHub问题。

### Description
PR的描述信息，用简洁的语言表达PR完成的事情，具体规范见[Commit 格式规范](#commit-格式规范)

### Related Issue
`#xx` if has

### Test Code with Result
请提供相关的测试代码如果有必要的话


## Commit 格式规范
Commit 分为“标题”和“内容”。原则上标题全部小写。内容首字母大写。


### 标题
commit message的标题：`[<type>](<scope>) <subject> (#pr)`


### type 可选值

本次提交的类型，限定在以下类型（全小写）
- fix：bug修复
- feature：新增功能
- feature-wip：开发中的功能，比如某功能的部分代码。
- improvement：原有功能的优化和改进
- style：代码风格调整
- typo：代码或文档勘误
- refactor：代码重构（不涉及功能变动）
- performance/optimize：性能优化
- test：单元测试的添加或修复
- deps：第三方依赖库的修改
- community：社区相关的修改，如修改 Github Issue 模板等。

几点说明：

如在一次提交中出现多种类型，需增加多个类型。
如代码重构带来了性能提升，可以同时添加 [refactor][optimize]
不得出现如上所列类型之外的其他类型。如有必要，需要将新增类型添加到这个文档中。

### scope 可选值
本次提交涉及的模块范围。因为功能模块繁多，在此仅罗列部分，后续根据需求不断完善。
<br>以 chatbot的框架为例
- connector
- codechat
- sandbox
- ...

几点说明：

尽量使用列表中已存在的选项。如需添加，请及时更新本文档。

### subject 内容
标题需尽量清晰表明本次提交的主要内容。


## 示例
comming soon


## Reference
[doris-commit-format](https://doris.apache.org/zh-CN/community/how-to-contribute/commit-format-specification)