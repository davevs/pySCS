# Contributing

Below you will find a collection of guidelines for submitting issues as well as contributing code to the PySCS repository.
Please read those before starting an issue or a pull request.

## Issues

Specific pySCS design and development issues, bugs, and feature requests are maintained by GitHub Issues.

*Please do not post installation, build, usage, or modeling questions, or other requests for help to Issues.*
This helps developers maintain a clear, uncluttered, and efficient view of the state of pySCS.
Feel free to reach out via Twitter for any problems using the tool: @Dave_von_S

When reporting an issue, it's most helpful to provide the following information, where applicable:
* How does the problem look like and what steps reproduce it?
* Can you reproduce it using the latest [master](https://github.com/davevs/pySCS/tree/master)?
* What is your running environment? In particular:
	* OS,
	* Python version,
	* Dot or PlantUML version, if relevant,
	* Your model file, if possible.
* **What have you already tried** to solve the problem? How did it fail? Are there any other issues related to yours?
* If the bug is a crash, provide the backtrace (usually printed by pySCS).

If only a small portion of the code/log is relevant to your issue, you may paste it directly into the post, preferably using Markdown syntax for code block: triple backtick ( \`\`\` ) to open/close a block.
In other cases (multiple files, or long files), please **attach** them to the post - this greatly improves readability.

If the problem arises during a complex operation (e.g. large model using pySCS), please reduce the example to the minimal size that still causes the error.
Also, minimize influence of external modules, data etc. - this way it will be easier for others to understand and reproduce your issue, and eventually help you.
Sometimes you will find the root cause yourself in the process.

Try to give your issue a title that is succinct and specific. The devs will rename issues as needed to keep track of them.

## Pull Requests

pySCS welcomes all contributions.

Briefly: read commit by commit, a PR should tell a clean, compelling story of _one_ improvement to pySCS. In particular:

* A PR should do one clear thing that obviously improves pySCS, and nothing more. Making many smaller PRs is better than making one large PR; review effort is superlinear in the amount of code involved.
* Similarly, each commit should be a small, atomic change representing one step in development. PRs should be made of many commits where appropriate.
* Please do rewrite PR history to be clean rather than chronological. Within-PR bugfixes, style cleanups, reversions, etc. should be squashed and should not appear in merged PR history.
* Anything nonobvious from the code should be explained in comments, commit messages, or the PR description, as appropriate.

(With many thanks to the Caffe project for their original CONTRIBUTING.md file)
