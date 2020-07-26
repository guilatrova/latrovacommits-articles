# Thoughts on Python Dependency Injection

The first thing that I thought that was missing when I came from a C# background to Python was:

> What should I use for Dependency Injection? How can I create interfaces?

And looks like that's a pretty common question from anyone coming from a typed language background, based on these stack overflow questions:

- https://stackoverflow.com/questions/2461702/why-is-ioc-di-not-common-in-python
- https://stackoverflow.com/questions/31678827/what-is-a-pythonic-way-for-dependency-injection
- https://stackoverflow.com/questions/156230/python-dependency-injection-framework

Please, note how all these questions mentions: _"Well, in Java..."_. Let me interrupt it right there because, well, you're not in Java (or C#), so how should you face this problem?

# What's Inversion of Control and why should I care about?
